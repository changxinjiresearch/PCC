import tempfile
import unittest
from pathlib import Path

import nibabel as nib
import numpy as np

from src.data.dataset_loader import (
    load_nii_raw,
    load_nii_zhw,
    to_zhw,
    validate_shape_compatibility,
)


def notebook_load_nii_raw(path):
    image = nib.load(str(path))
    array = image.get_fdata(dtype=np.float32)
    return array, image.affine, image.header


def notebook_to_zhw(array):
    array = np.asarray(array)
    if array.ndim != 3:
        raise ValueError(f"Expected 3D array, got {array.shape}")
    if array.shape[0] == array.shape[1] and array.shape[-1] < array.shape[0]:
        array = np.transpose(array, (2, 0, 1))
    return array.astype(np.float32)


def save_nifti(path, array, affine):
    nib.save(nib.Nifti1Image(array, affine), str(path))


class DatasetLoaderRegressionTests(unittest.TestCase):
    def test_load_nii_raw_matches_notebook_values_dtype_and_metadata(self):
        source = np.arange(4 * 4 * 3, dtype=np.int16).reshape(4, 4, 3)
        affine = np.array(
            [
                [2.0, 0.0, 0.0, 10.0],
                [0.0, 3.0, 0.0, 20.0],
                [0.0, 0.0, 4.0, 30.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "volume.nii"
            save_nifti(path, source, affine)

            actual_array, actual_affine, actual_header = load_nii_raw(path)
            expected_array, expected_affine, expected_header = (
                notebook_load_nii_raw(path)
            )

        np.testing.assert_array_equal(actual_array, expected_array)
        np.testing.assert_array_equal(actual_affine, expected_affine)
        self.assertEqual(actual_array.dtype, np.dtype(np.float32))
        self.assertEqual(
            actual_header.get_data_shape(),
            expected_header.get_data_shape(),
        )

    def test_load_nii_zhw_matches_notebook_and_returns_raw_shape(self):
        source = np.arange(5 * 5 * 3, dtype=np.float64).reshape(5, 5, 3)
        affine = np.eye(4)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "volume.nii.gz"
            save_nifti(path, source, affine)

            array, loaded_affine, header, raw_shape = load_nii_zhw(path)
            raw, expected_affine, expected_header = notebook_load_nii_raw(path)

        np.testing.assert_array_equal(array, notebook_to_zhw(raw))
        np.testing.assert_array_equal(loaded_affine, expected_affine)
        self.assertEqual(header.get_data_shape(), expected_header.get_data_shape())
        self.assertEqual(raw_shape, source.shape)
        self.assertEqual(array.shape, (3, 5, 5))
        self.assertEqual(array.dtype, np.dtype(np.float32))

    def test_to_zhw_transposes_only_when_notebook_condition_is_true(self):
        hwz = np.arange(6 * 6 * 4).reshape(6, 6, 4)
        zhw = np.arange(4 * 6 * 6).reshape(4, 6, 6)
        unequal_hw = np.arange(6 * 5 * 4).reshape(6, 5, 4)

        for source in (hwz, zhw, unequal_hw):
            np.testing.assert_array_equal(to_zhw(source), notebook_to_zhw(source))

        self.assertEqual(to_zhw(hwz).shape, (4, 6, 6))
        self.assertEqual(to_zhw(zhw).shape, (4, 6, 6))
        self.assertEqual(to_zhw(unequal_hw).shape, (6, 5, 4))

    def test_to_zhw_non_3d_errors_match_notebook(self):
        for source in (np.zeros((4, 4)), np.zeros((2, 4, 4, 3))):
            with self.assertRaises(ValueError) as expected:
                notebook_to_zhw(source)
            with self.assertRaises(ValueError) as actual:
                to_zhw(source)
            self.assertEqual(str(actual.exception), str(expected.exception))

    def test_mask_values_are_not_binarized(self):
        mask = np.array(
            [
                [[0.0, 0.25], [0.5, 1.0]],
                [[2.0, -1.0], [0.75, 0.0]],
            ],
            dtype=np.float32,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "mask.nii"
            save_nifti(path, mask, np.eye(4))
            loaded, _, _ = load_nii_raw(path)

        np.testing.assert_array_equal(loaded, mask)
        self.assertEqual(loaded.dtype, np.dtype(np.float32))

    def test_missing_file_propagates_nibabel_file_not_found(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missing.nii"
            with self.assertRaises(FileNotFoundError):
                load_nii_raw(path)

    def test_shape_compatibility_accepts_equal_shapes(self):
        arrays = [
            np.zeros((3, 5, 5), dtype=np.float32),
            np.ones((3, 5, 5), dtype=np.float32),
            np.zeros((3, 5, 5), dtype=bool),
            np.ones((3, 5, 5), dtype=bool),
        ]
        self.assertIsNone(validate_shape_compatibility(*arrays))

    def test_shape_compatibility_uses_notebook_assertion_message(self):
        arrays = [
            np.zeros((3, 5, 5), dtype=np.float32),
            np.zeros((4, 5, 5), dtype=np.float32),
        ]
        with self.assertRaises(AssertionError) as raised:
            validate_shape_compatibility(*arrays)
        self.assertEqual(
            str(raised.exception),
            "Shape mismatch after ZHW conversion.",
        )


if __name__ == "__main__":
    unittest.main()
