"""Testa a dispersão e as saídas com observações conhecidas."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "reproducible", Path(__file__).resolve().parents[2] / "scripts/benchmark_reproducivel.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class BenchmarkSummaryTests(unittest.TestCase):
    def test_sample_statistics_and_exports(self):
        rows = [{"resolucao": 160, "repeticao": i, "tempo_total_ms": value,
                 "homogeneidade_mse": 7} for i, value in enumerate([1, 2, 3], 1)]
        result = benchmark.summarize(rows)[0]
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["tempo_total_ms_media"], 2)
        self.assertEqual(result["tempo_total_ms_desvio"], 1)
        self.assertEqual(result["tempo_total_ms_mediana"], 2)
        self.assertEqual(result["tempo_total_ms_min"], 1)
        self.assertEqual(result["tempo_total_ms_max"], 3)
        self.assertEqual(result["homogeneidade_mse_desvio"], 0)
        with tempfile.TemporaryDirectory() as temp:
            benchmark.export_results(rows, temp, {"origem": "Teste determinístico"})
            self.assertEqual(len(list(Path(temp).iterdir())), 6)
            self.assertEqual(json.loads((Path(temp)/"metadados.json").read_text(encoding="utf-8"))["origem"],
                             "Teste determinístico")
            import xml.etree.ElementTree as ET
            ET.parse(Path(temp)/"tempo_total_ms.svg")

    def test_invalid_observations(self):
        valid = {"resolucao": 160, "repeticao": 1, "tempo_total_ms": 1}
        for rows in ([], [valid], [valid, valid],
                     [valid, {**valid, "repeticao": 2, "tempo_total_ms": float("nan")}],
                     [valid, {**valid, "repeticao": 2, "tempo_total_ms": -1}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                benchmark.summarize(rows)
