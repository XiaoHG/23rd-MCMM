"""问题三掩码感知时序编码、动态融合和双任务预测模型。"""

from __future__ import annotations

import torch
from torch import nn


class MaskedMultimodalNet(nn.Module):
    """三模态 Transformer 编码器 + 动态门控 + 分类/回归双头。"""

    def __init__(self, input_dims: dict[str, int], hidden_dim: int = 64, heads: int = 4, layers: int = 1, dropout: float = 0.1, max_length: int = 50, num_classes: int = 3):
        super().__init__()
        if hidden_dim % heads:
            raise ValueError("hidden_dim 必须能被 heads 整除")
        self.modalities = ("text", "audio", "vision")
        self.projections = nn.ModuleDict({m: nn.Sequential(nn.Linear(input_dims[m], hidden_dim), nn.LayerNorm(hidden_dim)) for m in self.modalities})
        self.position = nn.Parameter(torch.zeros(1, max_length, hidden_dim))
        self.encoders = nn.ModuleDict()
        for m in self.modalities:
            layer = nn.TransformerEncoderLayer(hidden_dim, heads, hidden_dim * 2, dropout, batch_first=True, norm_first=True)
            self.encoders[m] = nn.TransformerEncoder(layer, layers)
        self.cross_audio = nn.MultiheadAttention(hidden_dim, heads, dropout=dropout, batch_first=True)
        self.cross_vision = nn.MultiheadAttention(hidden_dim, heads, dropout=dropout, batch_first=True)
        self.gate = nn.Linear(hidden_dim, 1)
        self.fusion = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.GELU(), nn.Dropout(dropout), nn.LayerNorm(hidden_dim))
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self.regressor = nn.Linear(hidden_dim, 1)
        nn.init.normal_(self.position, std=0.02)

    @staticmethod
    def _pool(hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        weights = mask.unsqueeze(-1).to(hidden.dtype)
        return (hidden * weights).sum(1) / weights.sum(1).clamp_min(1.0)

    @staticmethod
    def _safe_padding_mask(valid: torch.Tensor) -> torch.Tensor:
        """避免整条模态全缺失时 softmax 对全 -inf 产生 NaN。"""
        safe = valid.clone()
        empty = ~safe.any(dim=1)
        if empty.any():
            safe[empty, 0] = True
        return ~safe

    def forward(self, text: torch.Tensor, audio: torch.Tensor, vision: torch.Tensor, mask: torch.Tensor) -> dict[str, torch.Tensor]:
        inputs = {"text": text, "audio": audio, "vision": vision}
        encoded: dict[str, torch.Tensor] = {}
        pooled: dict[str, torch.Tensor] = {}
        for index, name in enumerate(self.modalities):
            x = self.projections[name](inputs[name]) + self.position[:, : inputs[name].shape[1]]
            valid = mask[:, :, index].bool()
            h = self.encoders[name](x, src_key_padding_mask=self._safe_padding_mask(valid))
            h = h * valid.unsqueeze(-1).to(h.dtype)
            encoded[name] = h
            pooled[name] = self._pool(h, valid)
        text_valid = mask[:, :, 0].bool()
        audio_valid = mask[:, :, 1].bool()
        vision_valid = mask[:, :, 2].bool()
        audio_cross, _ = self.cross_audio(encoded["text"], encoded["audio"], encoded["audio"], key_padding_mask=self._safe_padding_mask(audio_valid))
        vision_cross, _ = self.cross_vision(encoded["text"], encoded["vision"], encoded["vision"], key_padding_mask=self._safe_padding_mask(vision_valid))
        pooled["text"] = pooled["text"] + self._pool(audio_cross, text_valid) + self._pool(vision_cross, text_valid)
        summary = torch.stack([pooled[m] for m in self.modalities], dim=1)
        present = (mask.sum(1) > 0).to(summary.dtype)
        gate_logits = self.gate(summary).squeeze(-1).masked_fill(present == 0, -1e4)
        gates = torch.softmax(gate_logits, dim=1)
        fused = self.fusion((summary * gates.unsqueeze(-1)).sum(1))
        logits = self.classifier(fused)
        regression = 3.0 * torch.tanh(self.regressor(fused).squeeze(-1))
        return {"logits": logits, "regression": regression, "gates": gates, "encoded": encoded, "pooled": pooled}
