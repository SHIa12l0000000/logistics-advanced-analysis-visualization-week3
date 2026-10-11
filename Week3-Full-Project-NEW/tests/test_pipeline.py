"""Basic reproducibility and analysis validation tests. Run from repository root."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from generate_data import generate
from analyze_logistics import read_and_validate, write_results


class PipelineTests(unittest.TestCase):
    def test_reproducible_generator(self):
        left = generate(n=30, seed=2026)
        right = generate(n=30, seed=2026)
        self.assertTrue(left.equals(right))
        self.assertEqual(left['shipment_id'].nunique(), 30)
        self.assertFalse(left.isna().any().any())

    def test_kpis_and_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / 'shipments.csv'
            generate(n=60, seed=2026).to_csv(input_path, index=False)
            df = read_and_validate(input_path)
            summary = write_results(df, root / 'outputs')
            self.assertEqual(summary['number_of_shipments'], 60)
            self.assertEqual(int(df['on_time'].sum()) + summary['late_count'], 60)
            self.assertEqual(len(list((root/'outputs'/'figures').glob('*.png'))), 8)
            self.assertTrue((root/'outputs'/'tables'/'correlations_pearson.csv').is_file())

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.csv'
            bad = generate(n=2, seed=2026)
            bad.loc[1, 'shipment_id'] = bad.loc[0, 'shipment_id']
            bad.to_csv(path, index=False)
            with self.assertRaises(ValueError):
                read_and_validate(path)

if __name__ == '__main__':
    unittest.main()
