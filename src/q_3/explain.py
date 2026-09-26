"""基于模态/局部窗口反事实遮挡的问题三解释器。"""

from __future__ import annotations

import numpy as np
import torch


MODALITIES = ("text", "audio", "vision")


@torch.no_grad()
def _outputs(model, batch: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    out = model(batch["text"], batch["audio"], batch["vision"], batch["mask"])
    return torch.softmax(out["logits"], dim=-1), out["regression"]


def _kl(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    return (p.clamp_min(1e-8) * (p.clamp_min(1e-8).log() - q.clamp_min(1e-8).log())).sum(-1)


def train_means_from_standardized(bundle) -> dict[str, np.ndarray]:
    """在已标准化的训练集空间中计算均值基线，避免重复标准化。"""
    return {
        name: np.asarray(getattr(bundle, name), dtype=np.float32).mean(axis=(0, 1))
        for name in MODALITIES
    }


@torch.no_grad()
def explain_batch(
    model,
    batch: dict[str, torch.Tensor],
    window: int = 5,
    stride: int = 5,
    top_k: int = 3,
    rho_cls: float = 0.5,
    baseline: str = "zero_invalid",
    modality_means: dict[str, torch.Tensor] | None = None,
) -> list[dict]:
    """返回模态贡献和局部证据。

    ``zero_invalid`` 表示将特征置零并令 mask 无效；``train_mean`` 表示用
    训练集均值替代被遮挡内容并保留 mask，有助于检查解释是否依赖于无效 mask。
    """
    if baseline not in {"zero_invalid", "train_mean"}:
        raise ValueError(f"不支持的解释基线：{baseline}")
    if baseline == "train_mean" and modality_means is None:
        raise ValueError("train_mean 基线必须提供 modality_means")

    def intervene(source: dict[str, torch.Tensor], name: str, start: int | None = None, end: int | None = None):
        target = {k: v.clone() for k, v in source.items()}
        mi = MODALITIES.index(name)
        begin = 0 if start is None else start
        finish = target[name].shape[1] if end is None else end
        if baseline == "train_mean":
            mean = modality_means[name].to(target[name].device, dtype=target[name].dtype)
            target[name][:, begin:finish] = mean
        else:
            target[name][:, begin:finish] = 0.0
            target["mask"][:, begin:finish, mi] = False
        return target

    full_p, full_y = _outputs(model, batch)
    n, length = batch["text"].shape[:2]
    modality_scores = torch.zeros((n, 3), device=full_p.device)
    local_records: list[list[list[tuple[int, int, float]]]] = [[[] for _ in MODALITIES] for _ in range(n)]
    for mi, name in enumerate(MODALITIES):
        masked = intervene(batch, name)
        p_removed, y_removed = _outputs(model, masked)
        modality_scores[:, mi] = rho_cls * _kl(full_p, p_removed) + (1 - rho_cls) * (full_y - y_removed).abs()
        for start in range(0, length, stride):
            end = min(start + window, length)
            local = intervene(batch, name, start, end)
            p_local, y_local = _outputs(model, local)
            scores = rho_cls * _kl(full_p, p_local) + (1 - rho_cls) * (full_y - y_local).abs()
            for row in range(n):
                if batch["mask"][row, start:end, mi].sum() > 0:
                    local_records[row][mi].append((start, end - 1, float(scores[row].item())))
    positive = modality_scores.clamp_min(0)
    contributions = positive / positive.sum(1, keepdim=True).clamp_min(1e-8)
    rows: list[dict] = []
    for row in range(n):
        main = [MODALITIES[i] for i in range(3) if contributions[row, i] >= contributions[row].max() - 1e-6]
        evidence = {}
        for mi, name in enumerate(MODALITIES):
            candidates = sorted(local_records[row][mi], key=lambda x: x[2], reverse=True)
            selected: list[tuple[int, int, float]] = []
            for item in candidates:
                if all(item[1] < old[0] - 1 or item[0] > old[1] + 1 for old in selected):
                    selected.append(item)
                if len(selected) >= top_k:
                    break
            evidence[name] = selected
        all_scores = [item[2] for values in local_records[row] for item in values]
        rows.append({
            "pred_class": int(full_p[row].argmax().item()),
            "pred_regression": float(full_y[row].item()),
            "modality_scores": [float(x) for x in modality_scores[row].cpu()],
            "modality_contrib": [float(x) for x in contributions[row].cpu()],
            "main_modality": ";".join(main),
            "evidence": evidence,
            "fidelity_top_mean": float(np.mean(sorted(all_scores, reverse=True)[:3])) if all_scores else 0.0,
            "fidelity_low_mean": float(np.mean(sorted(all_scores)[:3])) if all_scores else 0.0,
            "explanation_baseline": baseline,
        })
    return rows
