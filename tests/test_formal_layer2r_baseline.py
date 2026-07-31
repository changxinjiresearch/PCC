import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    import pandas as pd
    import torch
    import torch.nn as nn

    from src.models.formal_layer2r_baseline import (
        BASE_CHANNELS,
        BASELINE_MAP_FILENAME,
        BATCH_SIZE,
        CHECKPOINT_NAME_TEMPLATE,
        FORMAL_EPOCHS,
        INPUT_CHANNELS,
        LEARNING_RATE,
        OUTPUT_CHANNELS,
        SEED,
        ConvBlock,
        FormalBaselineTrainingResult,
        MiniUNet,
        SliceDataset,
        calculate_pos_weight,
        checkpoint_filename,
        make_formal_checkpoint,
        predict_full_volume,
        save_formal_checkpoint,
        save_baseline_probability,
        seed_formal_run,
        soft_dice_loss_from_logits,
    )

    DEPENDENCIES_AVAILABLE = True
except ModuleNotFoundError:
    DEPENDENCIES_AVAILABLE = False


@unittest.skipUnless(
    DEPENDENCIES_AVAILABLE,
    "PyTorch and pandas are required for formal baseline tests",
)
class FormalLayer2RBaselineTests(unittest.TestCase):
    def test_authoritative_constants(self):
        self.assertEqual(SEED, 42)
        self.assertEqual(FORMAL_EPOCHS, 12)
        self.assertEqual(BATCH_SIZE, 8)
        self.assertEqual(LEARNING_RATE, 1e-3)
        self.assertEqual(BASE_CHANNELS, 16)
        self.assertEqual(INPUT_CHANNELS, 2)
        self.assertEqual(OUTPUT_CHANNELS, 1)
        self.assertEqual(
            CHECKPOINT_NAME_TEMPLATE,
            "{case_id}_baseline_formal_best.pt",
        )
        self.assertEqual(
            BASELINE_MAP_FILENAME,
            "baseline_prob_map_formal_float16.npy",
        )

    def test_dataset_uses_all_slices_and_exact_channel_order(self):
        current = np.arange(3 * 8 * 8, dtype=np.float64).reshape(3, 8, 8)
        mask = np.zeros_like(current)
        mask[1] = 1
        target = np.zeros_like(current)
        target[2, 3:5, 3:5] = 1
        dataset = SliceDataset(current, mask, target)

        self.assertEqual(len(dataset), 3)
        inputs, y, z = dataset[1]
        self.assertEqual(tuple(inputs.shape), (2, 8, 8))
        self.assertEqual(tuple(y.shape), (1, 8, 8))
        self.assertEqual(inputs.dtype, torch.float32)
        self.assertEqual(y.dtype, torch.float32)
        self.assertEqual(z, 1)
        np.testing.assert_array_equal(inputs[0].numpy(), current[1])
        np.testing.assert_array_equal(inputs[1].numpy(), mask[1])
        np.testing.assert_array_equal(y[0].numpy(), target[1])

    def test_exact_model_structure_and_logits_shape(self):
        model = MiniUNet()
        self.assertIsInstance(model.enc1, ConvBlock)
        self.assertEqual(model.enc1.net[0].in_channels, 2)
        self.assertEqual(model.enc1.net[0].out_channels, 16)
        self.assertEqual(model.enc2.net[0].in_channels, 16)
        self.assertEqual(model.enc2.net[0].out_channels, 32)
        self.assertEqual(model.bottleneck.net[0].out_channels, 64)
        self.assertIsInstance(model.pool1, nn.MaxPool2d)
        self.assertIsInstance(model.pool2, nn.MaxPool2d)
        self.assertEqual(model.up2.kernel_size, (2, 2))
        self.assertEqual(model.up2.stride, (2, 2))
        self.assertEqual(model.up1.kernel_size, (2, 2))
        self.assertEqual(model.up1.stride, (2, 2))
        self.assertEqual(model.out.out_channels, 1)
        self.assertEqual(model.out.kernel_size, (1, 1))

        logits = model(torch.zeros((2, 2, 16, 20), dtype=torch.float32))
        self.assertEqual(tuple(logits.shape), (2, 1, 16, 20))

    def test_state_dict_has_formal_two_channel_first_layer(self):
        state = MiniUNet().state_dict()
        self.assertEqual(len(state), 76)
        self.assertEqual(tuple(state["enc1.net.0.weight"].shape), (16, 2, 3, 3))
        self.assertTrue(hasattr(MiniUNet(), "pool1"))
        self.assertTrue(hasattr(MiniUNet(), "pool2"))

    def test_soft_dice_loss_matches_literal_equation(self):
        logits = torch.tensor(
            [[[[0.0, 1.0], [-1.0, 0.5]]]],
            dtype=torch.float32,
        )
        targets = torch.tensor(
            [[[[0.0, 1.0], [1.0, 0.0]]]],
            dtype=torch.float32,
        )
        probabilities = torch.sigmoid(logits)
        intersection = torch.sum(probabilities * targets, (1, 2, 3))
        denominator = torch.sum(probabilities, (1, 2, 3)) + torch.sum(
            targets,
            (1, 2, 3),
        )
        expected = 1 - ((2 * intersection + 1e-6) / (denominator + 1e-6)).mean()
        torch.testing.assert_close(
            soft_dice_loss_from_logits(logits, targets),
            expected,
            rtol=0,
            atol=0,
        )

    def test_pos_weight_exact_clipping(self):
        balanced = np.array([0, 1], dtype=np.uint8)
        rare = np.zeros(1000, dtype=np.uint8)
        rare[0] = 1
        all_positive = np.ones(12, dtype=np.uint8)
        empty = np.zeros(9, dtype=np.uint8)
        self.assertEqual(calculate_pos_weight(balanced), 1.0)
        self.assertEqual(calculate_pos_weight(rare), 80.0)
        self.assertEqual(calculate_pos_weight(all_positive), 1.0)
        self.assertEqual(calculate_pos_weight(empty), 9.0)

    def test_run_seed_sets_python_numpy_torch_and_cuda(self):
        with mock.patch(
            "src.models.formal_layer2r_baseline.random.seed"
        ) as python_seed, mock.patch(
            "src.models.formal_layer2r_baseline.np.random.seed"
        ) as numpy_seed, mock.patch(
            "src.models.formal_layer2r_baseline.torch.manual_seed"
        ) as torch_seed, mock.patch(
            "src.models.formal_layer2r_baseline.torch.cuda.manual_seed_all"
        ) as cuda_seed:
            seed_formal_run()
        python_seed.assert_called_once_with(42)
        numpy_seed.assert_called_once_with(42)
        torch_seed.assert_called_once_with(42)
        cuda_seed.assert_called_once_with(42)

    def test_prediction_is_slice_wise_eval_no_grad_sigmoid_float32(self):
        class RecordingModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.calls = []

            def forward(self, inputs):
                self.calls.append((tuple(inputs.shape), torch.is_grad_enabled()))
                return torch.zeros(
                    (inputs.shape[0], 1, inputs.shape[2], inputs.shape[3]),
                    device=inputs.device,
                )

        model = RecordingModel()
        model.train()
        current = np.ones((3, 8, 8), dtype=np.float64)
        mask = np.zeros_like(current)
        actual = predict_full_volume(model, current, mask, "cpu")

        self.assertFalse(model.training)
        self.assertEqual(model.calls, [((1, 2, 8, 8), False)] * 3)
        self.assertEqual(actual.shape, (3, 8, 8))
        self.assertEqual(actual.dtype, np.float32)
        np.testing.assert_array_equal(
            actual,
            np.full((3, 8, 8), 0.5, dtype=np.float32),
        )

    def test_checkpoint_name_and_mapping_are_exact(self):
        model = MiniUNet()
        result = FormalBaselineTrainingResult(
            model=model,
            baseline_probability=np.zeros((2, 8, 8), dtype=np.float32),
            history=pd.DataFrame(),
            best_dice_topk=0.75,
            elapsed_seconds=1.5,
        )
        protocol = {"run_name": "Layer2R_publication_rebuild_EIA_v1"}
        checkpoint = make_formal_checkpoint("case_a", result, protocol)
        self.assertEqual(
            list(checkpoint),
            [
                "case_id",
                "formal_epochs",
                "model_state_dict",
                "best_dice_topk",
                "protocol",
            ],
        )
        self.assertEqual(checkpoint["case_id"], "case_a")
        self.assertEqual(checkpoint["formal_epochs"], 12)
        self.assertEqual(checkpoint["best_dice_topk"], 0.75)
        self.assertIs(checkpoint["protocol"], protocol)
        self.assertEqual(
            checkpoint_filename("case_a"),
            "case_a_baseline_formal_best.pt",
        )

    def test_checkpoint_save_uses_direct_formal_path(self):
        result = FormalBaselineTrainingResult(
            model=MiniUNet(),
            baseline_probability=np.zeros((1, 8, 8), dtype=np.float32),
            history=pd.DataFrame(),
            best_dice_topk=0.5,
            elapsed_seconds=0.0,
        )
        with tempfile.TemporaryDirectory() as temporary:
            expected = Path(temporary) / "case_a_baseline_formal_best.pt"
            with mock.patch(
                "src.models.formal_layer2r_baseline.torch.save"
            ) as save:
                actual = save_formal_checkpoint(
                    temporary,
                    "case_a",
                    result,
                    {"formal_epochs": 12},
                )
        self.assertEqual(actual, expected)
        save.assert_called_once()
        self.assertEqual(save.call_args.args[1], expected)

    def test_baseline_storage_copy_uses_exact_name_and_float16(self):
        probability = np.linspace(0, 1, 2 * 8 * 8, dtype=np.float32).reshape(
            2,
            8,
            8,
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = save_baseline_probability(temporary, probability)
            stored = np.load(path)
        self.assertEqual(path.name, "baseline_prob_map_formal_float16.npy")
        self.assertEqual(stored.dtype, np.float16)
        np.testing.assert_array_equal(stored, probability.astype(np.float16))

    def test_probability_output_satisfies_order_11_provider_contract(self):
        model = MiniUNet().eval()
        current = np.linspace(0, 1, 2 * 8 * 8, dtype=np.float32).reshape(
            2,
            8,
            8,
        )
        mask = np.zeros_like(current)
        probability = predict_full_volume(model, current, mask, "cpu")
        self.assertEqual(probability.shape, current.shape)
        self.assertEqual(probability.dtype, np.float32)
        self.assertTrue(np.all(probability >= 0))
        self.assertTrue(np.all(probability <= 1))

    def test_training_uses_formal_loader_and_restores_earliest_best_state(self):
        import src.models.formal_layer2r_baseline as module

        class TinyModel(nn.Module):
            def __init__(self, *args, **kwargs):
                super().__init__()
                self.convolution = nn.Conv2d(2, 1, 1)

            def forward(self, inputs):
                return self.convolution(inputs)

        current = np.linspace(0, 1, 2 * 8 * 8, dtype=np.float32).reshape(
            2,
            8,
            8,
        )
        mask = np.zeros_like(current)
        target = np.zeros_like(current)
        target[:, 3:5, 3:5] = 1
        states = []

        def record_prediction(model, *args, **kwargs):
            states.append(
                {
                    key: value.detach().cpu().clone()
                    for key, value in model.state_dict().items()
                }
            )
            return np.full_like(current, 0.5, dtype=np.float32)

        dice_values = [0.2, 0.4, 0.4] + [0.3] * 9

        def metrics(*args, **kwargs):
            dice = dice_values.pop(0)
            return {"dice_topk": dice}

        real_data_loader = torch.utils.data.DataLoader
        with mock.patch.object(module, "MiniUNet", TinyModel), mock.patch.object(
            module,
            "predict_full_volume",
            side_effect=record_prediction,
        ), mock.patch.object(
            module,
            "eval_prob_map",
            side_effect=metrics,
        ), mock.patch.object(
            module,
            "DataLoader",
            wraps=real_data_loader,
        ) as loader:
            result = module.train_case_baseline(
                "case_a",
                current,
                mask,
                target,
                "cpu",
            )

        loader.assert_called_once()
        self.assertEqual(loader.call_args.kwargs["batch_size"], 8)
        self.assertTrue(loader.call_args.kwargs["shuffle"])
        self.assertEqual(loader.call_args.kwargs["num_workers"], 0)
        self.assertNotIn("drop_last", loader.call_args.kwargs)
        self.assertNotIn("pin_memory", loader.call_args.kwargs)
        self.assertEqual(len(result.history), 12)
        self.assertEqual(result.history["epoch"].tolist(), list(range(1, 13)))
        self.assertEqual(result.best_dice_topk, 0.4)
        self.assertEqual(len(states), 13)
        for key, expected in states[1].items():
            torch.testing.assert_close(
                result.model.state_dict()[key],
                expected,
                rtol=0,
                atol=0,
            )
            torch.testing.assert_close(
                states[-1][key],
                expected,
                rtol=0,
                atol=0,
            )


if __name__ == "__main__":
    unittest.main()
