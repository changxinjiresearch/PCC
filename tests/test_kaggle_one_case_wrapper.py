from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WRAPPER_NAME = "layer2r-one-case-regression.ipynb"
WRAPPER_PATH = REPOSITORY_ROOT / WRAPPER_NAME
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "layer2r_kaggle_one_case.json"
METADATA_PATH = REPOSITORY_ROOT / "kernel-metadata.json"


class KaggleOneCaseWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads(WRAPPER_PATH.read_text())
        cls.source = "\n".join(
            "".join(cell.get("source", ()))
            for cell in cls.notebook["cells"]
            if cell["cell_type"] == "code"
        )
        cls.config = json.loads(CONFIG_PATH.read_text())
        cls.metadata = json.loads(METADATA_PATH.read_text())

    def test_wrapper_invokes_only_formal_one_case_runner(self):
        self.assertIn("experiments/run_formal_layer2r.py", self.source)
        self.assertIn('"--preflight"', self.source)
        self.assertEqual(self.source.count("subprocess.run"), 2)
        self.assertLess(
            self.source.index("preflight = subprocess.run"),
            self.source.index("execution = subprocess.run"),
        )

    def test_wrapper_establishes_repository_import_path_before_src_import(self):
        path_insertion = "sys.path.insert(0, str(REPOSITORY_ROOT))"
        src_import = "from src.pipelines.formal_layer2r import load_formal_config"

        self.assertLess(self.source.index(path_insertion), self.source.index(src_import))
        self.assertIn('REPOSITORY_MARKERS = ("src", "experiments", "configs")', self.source)
        self.assertIn("current_directory = Path.cwd().resolve()", self.source)
        self.assertIn('kaggle_working = Path("/kaggle/working")', self.source)
        self.assertIn("if not repository_roots:", self.source)
        self.assertIn("if len(repository_roots) != 1:", self.source)
        self.assertIn(
            'CONFIG_PATH = REPOSITORY_ROOT / "configs/layer2r_kaggle_one_case.json"',
            self.source,
        )
        self.assertIn(
            'RUNNER_PATH = REPOSITORY_ROOT / "experiments/run_formal_layer2r.py"',
            self.source,
        )

    def test_config_and_wrapper_enforce_one_case_limit(self):
        self.assertEqual(self.config["max_new_cases"], 1)
        self.assertIn('max_new_cases") != 1', self.source)

    def test_wrapper_references_no_multi_case_execution_path(self):
        forbidden = (
            "pcc-experiments.ipynb",
            "MAX_NEW_CASES = 5",
            "MAX_NEW_CASES = None",
            "remaining cases",
            "40-case",
            "run all",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assertNotIn(text, self.source)

    def test_metadata_selects_wrapper_and_enables_gpu(self):
        self.assertEqual(self.metadata["code_file"], WRAPPER_NAME)
        self.assertIs(self.metadata["enable_gpu"], True)

    def test_metadata_preserves_kernel_identity_and_dataset_attachments(self):
        self.assertEqual(self.metadata["id"], "jeechangxin/pcc-experiments")
        self.assertEqual(self.metadata["title"], "PCC_Experiments")
        self.assertEqual(
            self.metadata["dataset_sources"],
            [
                "jeechangxin/c2-v2-5epoch-backup",
                "jeechangxin/layer1-formal-v1-5fold-results-backup",
                "jeechangxin/model-a-backup-final",
                "stacyvangepuram/mu-glioma-post",
                "jeechangxin/pcc-results-tables-only-backup",
            ],
        )


if __name__ == "__main__":
    unittest.main()
