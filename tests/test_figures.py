import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np

from src.visualization.figures import (
    FIGURE_DPI,
    FIGURE_SIZE,
    PANEL_CMAPS,
    PANEL_TITLES,
    choose_target_slice,
    make_layer2r_formal_figure,
    save_layer2r_formal_figure,
)


def literal_notebook_figure(arrays):
    current_t1c, target, fixed, linear, blend090, blend075, morph, pcc = arrays
    per_slice = target.astype(bool).sum(axis=(1, 2))
    if per_slice.max() > 0:
        z = int(np.argmax(per_slice))
    else:
        z = int(target.shape[0] // 2)

    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    axes = axes.ravel()
    vis_items = [
        ("Current T1c", current_t1c[z], "gray"),
        ("Target", target[z].astype(float), "gray"),
        ("Fixed baseline", fixed[z], "hot"),
        ("EIA-linear", linear[z], "hot"),
        ("EIA-blend-0.90", blend090[z], "hot"),
        ("EIA-blend-0.75", blend075[z], "hot"),
        ("EIA-morph", morph[z], "gray"),
        ("PCC", pcc[z], "hot"),
    ]
    for ax, (title, image, cmap) in zip(axes, vis_items):
        ax.imshow(image, cmap=cmap)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    plt.tight_layout()
    return fig, z


def synthetic_arrays():
    base = np.arange(4 * 5 * 6, dtype=np.float32).reshape(4, 5, 6)
    current = base / base.max()
    target = np.zeros(base.shape, dtype=np.uint8)
    target[1, 1:3, 2:4] = 1
    target[2, 1:4, 1:4] = 1
    return (
        current,
        target,
        np.sin(base / 20.0).astype(np.float32),
        np.cos(base / 30.0).astype(np.float16),
        base / 50.0,
        base / 75.0,
        (base % 3 == 0),
        base[::-1] / 100.0,
    )


def rendered_rgb(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()


class Layer2RFigureRegressionTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_authoritative_constants(self):
        self.assertEqual(FIGURE_SIZE, (18, 8))
        self.assertEqual(FIGURE_DPI, 150)
        self.assertEqual(
            PANEL_TITLES,
            (
                "Current T1c",
                "Target",
                "Fixed baseline",
                "EIA-linear",
                "EIA-blend-0.90",
                "EIA-blend-0.75",
                "EIA-morph",
                "PCC",
            ),
        )
        self.assertEqual(
            PANEL_CMAPS,
            ("gray", "gray", "hot", "hot", "hot", "hot", "gray", "hot"),
        )

    def test_slice_selection_matches_formal_notebook(self):
        target = np.zeros((5, 4, 3), dtype=np.uint8)
        target[1, :2, :2] = 1
        target[3, :, :2] = 1
        self.assertEqual(choose_target_slice(target), 3)

    def test_tied_slice_uses_first_maximum(self):
        target = np.zeros((4, 3, 3), dtype=bool)
        target[1, 0, :2] = True
        target[2, 1, :2] = True
        self.assertEqual(choose_target_slice(target), 1)

    def test_empty_target_uses_integer_middle_slice(self):
        self.assertEqual(choose_target_slice(np.zeros((5, 2, 2))), 2)
        self.assertEqual(choose_target_slice(np.zeros((4, 2, 2))), 2)

    def test_figure_matches_literal_notebook_rendering(self):
        arrays = synthetic_arrays()
        expected, expected_z = literal_notebook_figure(arrays)
        actual, actual_z = make_layer2r_formal_figure(*arrays)
        self.assertEqual(actual_z, expected_z)
        np.testing.assert_array_equal(rendered_rgb(actual), rendered_rgb(expected))

    def test_panel_content_order_titles_colormaps_and_autoscaling(self):
        arrays = synthetic_arrays()
        fig, z = make_layer2r_formal_figure(*arrays)
        self.assertEqual(tuple(fig.get_size_inches()), FIGURE_SIZE)
        self.assertEqual(len(fig.axes), 8)
        self.assertEqual(tuple(ax.get_title() for ax in fig.axes), PANEL_TITLES)
        self.assertEqual(
            tuple(ax.images[0].get_cmap().name for ax in fig.axes),
            PANEL_CMAPS,
        )
        for index, ax in enumerate(fig.axes):
            self.assertFalse(ax.axison)
            expected = arrays[index][z]
            if index == 1:
                expected = expected.astype(float)
            np.testing.assert_array_equal(np.asarray(ax.images[0].get_array()), expected)
            self.assertEqual(
                ax.images[0].get_clim(),
                (float(np.min(expected)), float(np.max(expected))),
            )

    def test_inputs_are_not_clipped_normalized_or_mutated(self):
        arrays = list(synthetic_arrays())
        arrays[2] = arrays[2].copy()
        arrays[2][2, 0, 0] = -7.0
        arrays[2][2, 0, 1] = 9.0
        originals = [array.copy() for array in arrays]
        fig, _ = make_layer2r_formal_figure(*arrays)
        self.assertEqual(fig.axes[2].images[0].get_clim(), (-7.0, 9.0))
        for actual, original in zip(arrays, originals):
            np.testing.assert_array_equal(actual, original)

    def test_repeated_headless_rendering_is_deterministic(self):
        first, _ = make_layer2r_formal_figure(*synthetic_arrays())
        second, _ = make_layer2r_formal_figure(*synthetic_arrays())
        first_digest = hashlib.sha256(rendered_rgb(first)).digest()
        second_digest = hashlib.sha256(rendered_rgb(second)).digest()
        self.assertEqual(first_digest, second_digest)

    def test_save_uses_formal_parameters_and_closes_figure(self):
        arrays = synthetic_arrays()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "Layer2R_formal_synthetic.png"
            with mock.patch("matplotlib.pyplot.savefig", autospec=True) as savefig:
                returned = save_layer2r_formal_figure(output, *arrays)
                savefig.assert_called_once_with(
                    output,
                    dpi=150,
                    bbox_inches="tight",
                )
            self.assertEqual(returned, output)
            self.assertEqual(plt.get_fignums(), [])

    def test_png_export_is_repeatable_and_readable(self):
        arrays = synthetic_arrays()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.png"
            second = Path(directory) / "second.png"
            save_layer2r_formal_figure(first, *arrays)
            save_layer2r_formal_figure(second, *arrays)
            self.assertTrue(first.is_file())
            self.assertTrue(second.is_file())
            self.assertEqual(first.read_bytes(), second.read_bytes())
            image = plt.imread(first)
            self.assertEqual(image.ndim, 3)
            self.assertGreater(image.shape[0], 0)
            self.assertGreater(image.shape[1], 0)

    def test_shape_validation_rejects_non_zhw_and_misalignment(self):
        arrays = list(synthetic_arrays())
        arrays[0] = arrays[0][0]
        with self.assertRaisesRegex(ValueError, r"Expected 3D \[Z, H, W\]"):
            make_layer2r_formal_figure(*arrays)

        arrays = list(synthetic_arrays())
        arrays[-1] = arrays[-1][:-1]
        with self.assertRaisesRegex(ValueError, "Expected aligned arrays"):
            make_layer2r_formal_figure(*arrays)


if __name__ == "__main__":
    unittest.main()
