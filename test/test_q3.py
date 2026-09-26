"""问题三核心数据、mask、模型和反事实解释单元测试。"""

from __future__ import annotations

import unittest

import numpy as np
import torch

from src.q_3.data import FeatureBundle, apply_standardizer, fit_standardizer
from src.q_3.explain import explain_batch
from src.q_3.model import MaskedMultimodalNet


class TestQ3(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.bundle = FeatureBundle(
            ids=["-sample$_$0", "sample$_$1", "sample$_$2"],
            text=rng.normal(size=(3, 6, 8)).astype(np.float32),
            audio=rng.normal(size=(3, 6, 4)).astype(np.float32),
            vision=rng.normal(size=(3, 6, 3)).astype(np.float32),
            mask=np.ones((3, 6, 3), dtype=np.float32),
            regression=np.array([-1.0, 0.0, 2.0], dtype=np.float32),
            classification=np.array([0, 1, 2], dtype=np.int64),
            split="train",
        )

    def test_bundle_and_train_only_standardizer(self):
        self.bundle.validate()
        stats = fit_standardizer(self.bundle)
        standardized = apply_standardizer(self.bundle, stats)
        self.assertEqual(standardized.text.shape, (3, 6, 8))
        self.assertEqual(standardized.mask.dtype, np.bool_)
        self.assertTrue(np.isfinite(standardized.text).all())

    def test_model_masks_padding_and_missing_modality(self):
        model = MaskedMultimodalNet({"text": 8, "audio": 4, "vision": 3}, hidden_dim=16, heads=4, layers=1, max_length=6)
        batch = {
            "text": torch.from_numpy(self.bundle.text),
            "audio": torch.from_numpy(self.bundle.audio),
            "vision": torch.from_numpy(self.bundle.vision),
            "mask": torch.from_numpy(self.bundle.mask),
        }
        batch["mask"][1, :, 1] = 0
        output = model(**batch)
        self.assertEqual(output["logits"].shape, (3, 3))
        self.assertEqual(output["regression"].shape, (3,))
        self.assertTrue(torch.isfinite(output["logits"]).all())
        self.assertTrue(torch.isfinite(output["regression"]).all())
        self.assertTrue(torch.isfinite(output["gates"]).all())

    def test_nonfinite_features_become_invalid_mask_before_cleaning(self):
        from src.q_3.data import load_attachment2
        import pickle
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as directory:
            path = Path(directory) / "features.pkl"
            payload = {
                "train": {
                    "id": ["sample"],
                    "text": np.array([[[np.nan, 1.0]]], dtype=np.float32),
                    "audio": np.zeros((1, 1, 1), dtype=np.float32),
                    "vision": np.zeros((1, 1, 1), dtype=np.float32),
                    "regression_labels": [0.0],
                    "classification_labels": [1],
                }
            }
            with path.open("wb") as handle:
                pickle.dump(payload, handle)
            bundle = load_attachment2(path, "train")
            self.assertFalse(bool(bundle.mask[0, 0, 0]))
            self.assertEqual(float(bundle.text[0, 0, 0]), 0.0)

    def test_counterfactual_explanation_contract(self):
        model = MaskedMultimodalNet({"text": 8, "audio": 4, "vision": 3}, hidden_dim=16, heads=4, layers=1, max_length=6)
        batch = {"text": torch.from_numpy(self.bundle.text[:1]), "audio": torch.from_numpy(self.bundle.audio[:1]), "vision": torch.from_numpy(self.bundle.vision[:1]), "mask": torch.from_numpy(self.bundle.mask[:1])}
        rows = explain_batch(model, batch, window=2, stride=2, top_k=2)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(sum(rows[0]["modality_contrib"]), 1.0, places=5)
        self.assertIn("text", rows[0]["evidence"])
        self.assertIn("audio", rows[0]["evidence"])
        self.assertIn("vision", rows[0]["evidence"])

    def test_train_mean_explanation_baseline(self):
        model = MaskedMultimodalNet({"text": 8, "audio": 4, "vision": 3}, hidden_dim=16, heads=4, layers=1, max_length=6)
        batch = {"text": torch.from_numpy(self.bundle.text[:1]), "audio": torch.from_numpy(self.bundle.audio[:1]), "vision": torch.from_numpy(self.bundle.vision[:1]), "mask": torch.from_numpy(self.bundle.mask[:1])}
        means = {"text": torch.zeros(8), "audio": torch.zeros(4), "vision": torch.zeros(3)}
        rows = explain_batch(model, batch, window=2, stride=2, top_k=2, baseline="train_mean", modality_means=means)
        self.assertEqual(rows[0]["explanation_baseline"], "train_mean")
        self.assertAlmostEqual(sum(rows[0]["modality_contrib"]), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
