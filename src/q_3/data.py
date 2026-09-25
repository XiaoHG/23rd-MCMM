"""问题三数据读取、训练集标准化和 CSV 安全写出工具。"""

from __future__ import annotations

import hashlib
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


MODALITIES = ("text", "audio", "vision")


@dataclass
class FeatureBundle:
    ids: list[str]
    text: np.ndarray
    audio: np.ndarray
    vision: np.ndarray
    mask: np.ndarray
    regression: np.ndarray | None = None
    classification: np.ndarray | None = None
    split: str = "unknown"
    raw_text: list[str] | None = None

    def validate(self) -> None:
        n = len(self.ids)
        if self.text.ndim != 3 or self.audio.ndim != 3 or self.vision.ndim != 3:
            raise ValueError("三模态特征必须为 [N, L, D] 三维数组")
        if any(len(x) != n for x in (self.text, self.audio, self.vision, self.mask)):
            raise ValueError("样本数量与 mask/特征数量不一致")
        if self.mask.shape != (n, self.text.shape[1], 3):
            raise ValueError(f"mask 形状错误：{self.mask.shape}")
        if len(set(self.ids)) != n:
            raise ValueError("样本主键不唯一")
        for name, arr in (("text", self.text), ("audio", self.audio), ("vision", self.vision)):
            if not np.isfinite(arr).all():
                raise ValueError(f"{name} 含非有限值")
        if self.regression is not None and len(self.regression) != n:
            raise ValueError("回归标签数量不匹配")
        if self.classification is not None and len(self.classification) != n:
            raise ValueError("分类标签数量不匹配")
        if self.raw_text is not None and len(self.raw_text) != n:
            raise ValueError("原始文本数量不匹配")


def _as_float32(value: Any) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float32)
    return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


def _full_mask(text: np.ndarray, audio: np.ndarray, vision: np.ndarray) -> np.ndarray:
    n, length = text.shape[:2]
    if audio.shape[1] != length or vision.shape[1] != length:
        raise ValueError("aligned 输入三模态时间长度不一致")
    # 附件二 aligned 文件没有独立 mask；有效数据均为固定 50 窗口。
    mask = np.ones((n, length, 3), dtype=bool)
    for index, arr in enumerate((text, audio, vision)):
        mask[:, :, index] = np.isfinite(arr).all(axis=2)
    return mask


def _pickle_load(path: Path) -> Any:
    """兼容 NumPy 2.x 写出、NumPy 1.x 读取的 pickle 模块路径。"""
    # NumPy 2 将部分 pickle 路径从 numpy.core 改为 numpy._core；数组格式本身
    # 在本项目中仍兼容，因此仅在导入失败时提供模块别名，不改写原始数据。
    try:
        with path.open("rb") as handle:
            return pickle.load(handle)
    except ModuleNotFoundError as exc:
        if not str(exc).startswith("No module named 'numpy._core"):
            raise
        import numpy.core as numpy_core

        sys.modules.setdefault("numpy._core", numpy_core)
        for name in ("numeric", "multiarray", "_multiarray_umath", "shape_base"):
            module = getattr(numpy_core, name, None)
            if module is not None:
                sys.modules.setdefault(f"numpy._core.{name}", module)
        with path.open("rb") as handle:
            return pickle.load(handle)


def load_attachment2(path: str | Path, split: str) -> FeatureBundle:
    """读取附件二 aligned pickle 的一个划分，不读取或混用其他划分。"""
    path = Path(path)
    data = _pickle_load(path)
    if split not in data:
        raise KeyError(f"pickle 中没有划分 {split!r}，可用划分为 {list(data)}")
    part = data[split]
    raw_text = np.asarray(part["text"], dtype=np.float32)
    raw_audio = np.asarray(part["audio"], dtype=np.float32)
    raw_vision = np.asarray(part["vision"], dtype=np.float32)
    mask = _full_mask(raw_text, raw_audio, raw_vision)
    text = np.nan_to_num(raw_text, nan=0.0, posinf=0.0, neginf=0.0)
    audio = np.nan_to_num(raw_audio, nan=0.0, posinf=0.0, neginf=0.0)
    vision = np.nan_to_num(raw_vision, nan=0.0, posinf=0.0, neginf=0.0)
    ids = [str(x) for x in part["id"]]
    bundle = FeatureBundle(
        ids=ids,
        text=text,
        audio=audio,
        vision=vision,
        mask=mask,
        regression=_as_float32(part["regression_labels"]).reshape(-1),
        classification=np.asarray(part["classification_labels"], dtype=np.int64).reshape(-1),
        split=split,
        raw_text=[str(x) for x in part.get("raw_text", [""] * len(ids))],
    )
    bundle.validate()
    return bundle


def load_attachment4(directory: str | Path, feature_version: str = "aligned") -> FeatureBundle:
    """读取附件四的无标签单样本 pickle，仅用于固定模型后的最终推理。"""
    directory = Path(directory) / feature_version
    files = sorted(directory.glob("*.pkl"))
    if not files:
        raise FileNotFoundError(f"没有找到附件四 {feature_version} pickle：{directory}")
    rows: list[dict[str, Any]] = []
    for path in files:
        item = _pickle_load(path)
        if not isinstance(item, dict):
            raise ValueError(f"附件四文件不是字典：{path}")
        rows.append(item)
    raw_text = np.asarray(np.stack([x["text"] for x in rows]), dtype=np.float32)
    raw_audio = np.asarray(np.stack([x["audio"] for x in rows]), dtype=np.float32)
    raw_vision = np.asarray(np.stack([x["vision"] for x in rows]), dtype=np.float32)
    mask = _full_mask(raw_text, raw_audio, raw_vision)
    text = np.nan_to_num(raw_text, nan=0.0, posinf=0.0, neginf=0.0)
    audio = np.nan_to_num(raw_audio, nan=0.0, posinf=0.0, neginf=0.0)
    vision = np.nan_to_num(raw_vision, nan=0.0, posinf=0.0, neginf=0.0)
    ids = [str(x.get("id", files[i].stem)) for i, x in enumerate(rows)]
    bundle = FeatureBundle(ids, text, audio, vision, mask, split="attachment4", raw_text=[str(x.get("raw_text", "")) for x in rows])
    bundle.validate()
    return bundle


def fit_standardizer(bundle: FeatureBundle) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """仅用训练集拟合每个模态的特征均值和标准差。"""
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name in MODALITIES:
        arr = getattr(bundle, name).astype(np.float64)
        mean = arr.reshape(-1, arr.shape[-1]).mean(axis=0).astype(np.float32)
        std = arr.reshape(-1, arr.shape[-1]).std(axis=0).astype(np.float32)
        std[std < 1e-6] = 1.0
        result[name] = (mean, std)
    return result


def apply_standardizer(bundle: FeatureBundle, stats: dict[str, tuple[np.ndarray, np.ndarray]]) -> FeatureBundle:
    kwargs = {}
    for name in MODALITIES:
        mean, std = stats[name]
        kwargs[name] = ((getattr(bundle, name) - mean) / std).astype(np.float32)
    result = FeatureBundle(bundle.ids, kwargs["text"], kwargs["audio"], kwargs["vision"], bundle.mask.astype(bool, copy=True), bundle.regression, bundle.classification, bundle.split, bundle.raw_text)
    result.validate()
    return result


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def excel_safe(value: Any) -> Any:
    """避免 Excel 将负号开头的样本主键误判为公式。"""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value
