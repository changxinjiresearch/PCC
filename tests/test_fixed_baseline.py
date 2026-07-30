import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    import torch
    import torch.nn as nn

    from src.models.fixed_baseline import (
        BASE_CHANNELS,
        FIXED_THRESHOLD,
        INFERENCE_BATCH_SIZE,
        INPUT_CHANNELS,
        OUTPUT_CHANNELS,
        ConvBlock,
        SmallUNet2D,
        build_fixed_baseline,
        get_threshold_from_checkpoint,
        load_fixed_baseline_checkpoint,
        predict_prob,
        threshold_probabilities,
    )

    TORCH_AVAILABLE = True
except ModuleNotFoundError:
    TORCH_AVAILABLE = False


@unittest.skipUnless(TORCH_AVAILABLE, "PyTorch is not installed")
class FixedBaselineRegressionTests(unittest.TestCase):
    def test_hard_coded_constants_match_formal_v1(self):
        self.assertEqual(INPUT_CHANNELS, 1)
        self.assertEqual(OUTPUT_CHANNELS, 1)
        self.assertEqual(BASE_CHANNELS, 16)
        self.assertEqual(INFERENCE_BATCH_SIZE, 64)
        self.assertEqual(FIXED_THRESHOLD, 0.5)

    def test_model_construction_and_exact_layer_structure(self):
        model = SmallUNet2D()

        for block in [
            model.enc1,
            model.enc2,
            model.bottleneck,
            model.dec2,
            model.dec1,
        ]:
            self.assertIsInstance(block, ConvBlock)
            self.assertEqual(len(block.net), 6)
            self.assertIsInstance(block.net[0], nn.Conv2d)
            self.assertIsInstance(block.net[1], nn.BatchNorm2d)
            self.assertIsInstance(block.net[2], nn.ReLU)
            self.assertIsInstance(block.net[3], nn.Conv2d)
            self.assertIsInstance(block.net[4], nn.BatchNorm2d)
            self.assertIsInstance(block.net[5], nn.ReLU)
            self.assertTrue(block.net[2].inplace)
            self.assertTrue(block.net[5].inplace)

        expected_channels = {
            "enc1": (1, 16),
            "enc2": (16, 32),
            "bottleneck": (32, 64),
            "dec2": (64, 32),
            "dec1": (32, 16),
        }
        for name, (in_channels, out_channels) in expected_channels.items():
            block = getattr(model, name)
            first, second = block.net[0], block.net[3]
            self.assertEqual(first.in_channels, in_channels)
            self.assertEqual(first.out_channels, out_channels)
            self.assertEqual(second.in_channels, out_channels)
            self.assertEqual(second.out_channels, out_channels)
            self.assertEqual(first.kernel_size, (3, 3))
            self.assertEqual(second.kernel_size, (3, 3))
            self.assertEqual(first.padding, (1, 1))
            self.assertEqual(second.padding, (1, 1))

        self.assertEqual(model.pool.kernel_size, 2)
        self.assertEqual(model.pool.stride, 2)
        self.assertEqual(
            (model.up2.in_channels, model.up2.out_channels),
            (64, 32),
        )
        self.assertEqual(
            (model.up1.in_channels, model.up1.out_channels),
            (32, 16),
        )
        self.assertEqual(model.up2.kernel_size, (2, 2))
        self.assertEqual(model.up2.stride, (2, 2))
        self.assertEqual(model.up1.kernel_size, (2, 2))
        self.assertEqual(model.up1.stride, (2, 2))
        self.assertEqual(
            (model.out.in_channels, model.out.out_channels),
            (16, 1),
        )
        self.assertEqual(model.out.kernel_size, (1, 1))

    def test_exact_state_dict_key_structure(self):
        model = SmallUNet2D()
        expected_keys = []
        for block_name in ["enc1", "enc2", "bottleneck", "dec2", "dec1"]:
            for layer_index in [0, 3]:
                expected_keys.extend(
                    [
                        f"{block_name}.net.{layer_index}.weight",
                        f"{block_name}.net.{layer_index}.bias",
                    ]
                )
            for layer_index in [1, 4]:
                expected_keys.extend(
                    [
                        f"{block_name}.net.{layer_index}.weight",
                        f"{block_name}.net.{layer_index}.bias",
                        f"{block_name}.net.{layer_index}.running_mean",
                        f"{block_name}.net.{layer_index}.running_var",
                        f"{block_name}.net.{layer_index}.num_batches_tracked",
                    ]
                )
        expected_keys.extend(
            [
                "up2.weight",
                "up2.bias",
                "up1.weight",
                "up1.bias",
                "out.weight",
                "out.bias",
            ]
        )

        self.assertEqual(set(model.state_dict()), set(expected_keys))
        self.assertEqual(len(model.state_dict()), 76)

    def test_even_and_odd_input_shapes_preserve_spatial_shape_and_dtype(self):
        model = SmallUNet2D().eval()

        for shape in [(2, 1, 32, 28), (2, 1, 31, 29)]:
            inputs = torch.linspace(
                0,
                1,
                int(np.prod(shape)),
                dtype=torch.float32,
            ).reshape(shape)
            with torch.no_grad():
                logits = model(inputs)
            self.assertEqual(tuple(logits.shape), shape)
            self.assertEqual(logits.dtype, torch.float32)

    def test_build_places_model_on_requested_device(self):
        model = build_fixed_baseline("cpu")
        self.assertEqual(next(model.parameters()).device.type, "cpu")

    def test_prediction_sets_eval_mode_disables_grad_and_applies_sigmoid(self):
        class RecordingModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.grad_enabled = []

            def forward(self, inputs):
                self.grad_enabled.append(torch.is_grad_enabled())
                return torch.zeros_like(inputs)

        model = RecordingModel()
        model.train()
        inputs = np.ones((3, 1, 5, 7), dtype=np.float64)

        probabilities = predict_prob(
            model,
            inputs,
            device="cpu",
            batch_size=2,
        )

        self.assertFalse(model.training)
        self.assertEqual(model.grad_enabled, [False, False])
        self.assertEqual(probabilities.shape, (3, 1, 5, 7))
        self.assertEqual(probabilities.dtype, np.dtype(np.float32))
        np.testing.assert_array_equal(
            probabilities,
            np.full(probabilities.shape, 0.5, dtype=np.float32),
        )

    def test_probability_map_matches_literal_notebook_operation_sequence(self):
        torch.manual_seed(42)
        model = SmallUNet2D().eval()
        inputs = np.linspace(
            0,
            1,
            3 * 1 * 16 * 16,
            dtype=np.float32,
        ).reshape(3, 1, 16, 16)

        with torch.no_grad():
            expected = (
                torch.sigmoid(model(torch.from_numpy(inputs).float().to("cpu")))
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )
        actual = predict_prob(model, inputs, device="cpu", batch_size=64)

        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(np.all(actual >= 0))
        self.assertTrue(np.all(actual <= 1))

    def test_thresholding_is_inclusive_and_boolean_without_postprocessing(self):
        probabilities = np.array(
            [[[[0.0, 0.4999, 0.5, 0.75, 1.0]]]],
            dtype=np.float32,
        )
        expected = probabilities >= 0.5
        actual = threshold_probabilities(probabilities, 0.5)

        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.dtype(bool))
        self.assertEqual(actual.shape, probabilities.shape)

    def test_threshold_checkpoint_key_order_and_default(self):
        self.assertEqual(
            get_threshold_from_checkpoint(
                {
                    "threshold": 0.25,
                    "best_threshold": 0.35,
                    "selected_threshold": 0.45,
                    "thr": 0.55,
                }
            ),
            0.25,
        )
        self.assertEqual(
            get_threshold_from_checkpoint({"best_threshold": 0.35}),
            0.35,
        )
        self.assertEqual(get_threshold_from_checkpoint({}), 0.5)

    def test_checkpoint_loading_round_trip_is_strict_and_sets_eval(self):
        torch.manual_seed(42)
        expected_model = SmallUNet2D().eval()
        checkpoint = {
            "fold": 3,
            "model_state_dict": expected_model.state_dict(),
            "threshold": 0.35,
            "train_dice": 0.75,
            "config": {"experiment": "Layer 1 Formal v1"},
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "baseline.pt"
            torch.save(checkpoint, path)
            actual_model, threshold = load_fixed_baseline_checkpoint(
                path,
                device="cpu",
            )

        self.assertFalse(actual_model.training)
        self.assertEqual(threshold, 0.35)
        for key, expected in expected_model.state_dict().items():
            torch.testing.assert_close(
                actual_model.state_dict()[key],
                expected,
                rtol=0,
                atol=0,
            )

    def test_checkpoint_loading_passes_requested_map_location(self):
        model = SmallUNet2D()
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "threshold": 0.5,
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "baseline.pt"
            path.touch()
            with mock.patch(
                "src.models.fixed_baseline.torch.load",
                return_value=checkpoint,
            ) as load:
                load_fixed_baseline_checkpoint(path, device="cpu")

        load.assert_called_once_with(path, map_location="cpu")

    def test_missing_checkpoint_uses_notebook_assertion_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing.pt"
            with self.assertRaises(AssertionError) as raised:
                load_fixed_baseline_checkpoint(missing, device="cpu")
        self.assertEqual(str(raised.exception), str(missing))

    def test_malformed_checkpoint_missing_state_dict_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "malformed.pt"
            torch.save({"threshold": 0.5}, path)
            with self.assertRaises(KeyError) as raised:
                load_fixed_baseline_checkpoint(path, device="cpu")
        self.assertEqual(raised.exception.args, ("model_state_dict",))

    def test_strict_state_dict_failure_propagates(self):
        model = SmallUNet2D()
        state_dict = model.state_dict()
        state_dict.pop("out.weight")

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "incompatible.pt"
            torch.save({"model_state_dict": state_dict}, path)
            with self.assertRaises(RuntimeError):
                load_fixed_baseline_checkpoint(path, device="cpu")

    def test_repeated_inference_is_deterministic(self):
        torch.manual_seed(42)
        model = SmallUNet2D().eval()
        inputs = np.linspace(
            0,
            1,
            2 * 1 * 17 * 19,
            dtype=np.float32,
        ).reshape(2, 1, 17, 19)

        first = predict_prob(model, inputs, device="cpu", batch_size=1)
        second = predict_prob(model, inputs, device="cpu", batch_size=1)

        np.testing.assert_array_equal(first, second)

    def test_module_has_no_out_of_scope_public_logic(self):
        import src.models.fixed_baseline as module

        names = {name.lower() for name in vars(module)}
        forbidden_fragments = [
            "preprocess",
            "dice",
            "iou",
            "naive",
            "pcc",
            "eia",
            "visual",
            "statistic",
        ]
        for fragment in forbidden_fragments:
            self.assertFalse(
                any(fragment in name for name in names),
                fragment,
            )


if __name__ == "__main__":
    unittest.main()
