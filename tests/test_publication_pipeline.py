import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.publication.pipeline import (
    FIGURE_NAME_TEMPLATE,
    PUBLICATION_TABLE_NAMES,
    collect_publication_outputs,
)
from src.statistics.statistics import (
    METHOD_ORDER,
    METHOD_SUMMARY_COLUMNS,
    PAIRWISE_SUMMARY_COLUMNS,
)


def create_publication_inputs(root: Path) -> tuple[str, ...]:
    figures = root / "figures"
    tables = root / "tables"
    formal_results = root / "formal_results"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(exist_ok=True)
    formal_results.mkdir(exist_ok=True)

    case_ids = tuple(f"case_{index:02d}" for index in range(40))
    pd.DataFrame({"case_id": case_ids}).to_csv(
        tables / "locked_40_cases.csv",
        index=False,
    )
    for case_id in case_ids:
        (figures / FIGURE_NAME_TEMPLATE.format(case_id=case_id)).write_bytes(
            b"existing order-9 figure"
        )

    method_rows = []
    for method in sorted(METHOD_ORDER):
        method_rows.append(
            dict.fromkeys(METHOD_SUMMARY_COLUMNS, 0)
            | {"method": method, "n": 40}
        )
    pd.DataFrame(method_rows, columns=METHOD_SUMMARY_COLUMNS).to_csv(
        formal_results / PUBLICATION_TABLE_NAMES[0],
        index=False,
    )

    comparisons = sorted(f"PCC vs {method}" for method in METHOD_ORDER[:-1])
    pairwise_rows = []
    for comparison in comparisons:
        pairwise_rows.append(
            dict.fromkeys(PAIRWISE_SUMMARY_COLUMNS, 0)
            | {"comparison": comparison, "n": 40}
        )
    pd.DataFrame(pairwise_rows, columns=PAIRWISE_SUMMARY_COLUMNS).to_csv(
        formal_results / PUBLICATION_TABLE_NAMES[1],
        index=False,
    )
    return case_ids


class PublicationPipelineTests(unittest.TestCase):
    def test_collects_exact_notebook_names_and_order_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Layer2R_publication_rebuild_EIA_v1"
            case_ids = create_publication_inputs(root)
            before = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            outputs = collect_publication_outputs(root)

            self.assertEqual(outputs.output_dir, root)
            self.assertEqual(outputs.case_ids, case_ids)
            self.assertEqual(
                outputs.figures,
                tuple(
                    root / "figures" / f"Layer2R_formal_{case_id}.png"
                    for case_id in case_ids
                ),
            )
            self.assertEqual(
                outputs.tables,
                tuple(root / "formal_results" / name for name in PUBLICATION_TABLE_NAMES),
            )
            after = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_missing_figure_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_ids = create_publication_inputs(root)
            missing = root / "figures" / f"Layer2R_formal_{case_ids[3]}.png"
            missing.unlink()
            with self.assertRaisesRegex(FileNotFoundError, str(missing)):
                collect_publication_outputs(root)

    def test_requires_exact_locked_cohort_and_lexicographic_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_ids = list(create_publication_inputs(root))
            case_ids[0], case_ids[1] = case_ids[1], case_ids[0]
            pd.DataFrame({"case_id": case_ids}).to_csv(
                root / "tables" / "locked_40_cases.csv",
                index=False,
            )
            with self.assertRaisesRegex(ValueError, "lexicographic"):
                collect_publication_outputs(root)

            pd.DataFrame({"case_id": case_ids[:-1]}).to_csv(
                root / "tables" / "locked_40_cases.csv",
                index=False,
            )
            with self.assertRaisesRegex(ValueError, "Expected 40"):
                collect_publication_outputs(root)

    def test_rejects_changed_table_columns_or_group_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_publication_inputs(root)
            method_path = root / "formal_results" / PUBLICATION_TABLE_NAMES[0]
            methods = pd.read_csv(method_path)
            methods.iloc[::-1].to_csv(method_path, index=False)
            with self.assertRaisesRegex(ValueError, "method ordering"):
                collect_publication_outputs(root)

            create_publication_inputs(root)
            pairwise_path = root / "formal_results" / PUBLICATION_TABLE_NAMES[1]
            pairwise = pd.read_csv(pairwise_path).drop(columns=["iou_win_rate"])
            pairwise.to_csv(pairwise_path, index=False)
            with self.assertRaisesRegex(ValueError, "Unexpected columns"):
                collect_publication_outputs(root)

    def test_rejects_incomplete_summary_case_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_publication_inputs(root)
            method_path = root / "formal_results" / PUBLICATION_TABLE_NAMES[0]
            methods = pd.read_csv(method_path)
            methods.loc[0, "n"] = 39
            methods.to_csv(method_path, index=False)
            with self.assertRaisesRegex(ValueError, "all 40 locked cases"):
                collect_publication_outputs(root)


if __name__ == "__main__":
    unittest.main()
