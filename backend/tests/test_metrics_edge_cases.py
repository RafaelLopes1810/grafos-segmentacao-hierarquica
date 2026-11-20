"""Oráculos pequenos e casos-limite das métricas, sem bibliotecas externas de métricas."""
import itertools
import math
import unittest

import numpy as np

from app.evaluation.metrics import (
    color_homogeneity_mse, rand_index, region_statistics,
    variation_of_information,
)


class MetricEdgeTests(unittest.TestCase):
    def test_rand_matches_pair_enumeration(self):
        rng = np.random.default_rng(2026)
        for size in range(1, 20):
            a = rng.integers(-3, 4, size).reshape(1, -1)
            b = rng.integers(10, 14, size).reshape(1, -1)
            pairs = list(itertools.combinations(range(size), 2))
            oracle = (sum((a[0, i] == a[0, j]) == (b[0, i] == b[0, j])
                          for i, j in pairs) / len(pairs)) if pairs else 1.0
            self.assertAlmostEqual(rand_index(a, b), oracle)
            self.assertAlmostEqual(rand_index(a, b), rand_index(b, a))

    def test_vi_known_entropy_and_symmetry(self):
        for size in (1, 2, 4, 8):
            singleton = np.arange(size).reshape(1, -1)
            merged = np.full((1, size), -100)
            self.assertAlmostEqual(variation_of_information(singleton, merged), math.log2(size))
            self.assertAlmostEqual(variation_of_information(merged, singleton), math.log2(size))
            self.assertAlmostEqual(variation_of_information(singleton, singleton * 17 + 9), 0)
        a = np.array([[0, 0], [1, 1]])
        b = a.T
        self.assertAlmostEqual(rand_index(a, b), 1 / 3)
        self.assertAlmostEqual(variation_of_information(a, b), 2)

    def test_mse_weighted_by_pixels_and_channels(self):
        image = np.array([[[0, 0, 0], [2, 4, 6], [99, 99, 99]]], np.uint8)
        labels = np.array([[-7, -7, 1000]])
        # First block contributes 2*(1+4+9); second contributes zero.
        self.assertAlmostEqual(color_homogeneity_mse(image, labels), 28 / 9)
        self.assertAlmostEqual(color_homogeneity_mse(image, labels * 19), 28 / 9)
        self.assertEqual(color_homogeneity_mse(image, np.arange(3).reshape(1, 3)), 0)
        constant = np.full((1, 3, 3), 255, np.uint8)
        self.assertEqual(color_homogeneity_mse(constant, labels), 0)

    def test_statistics_for_sparse_negative_ids(self):
        self.assertEqual(region_statistics([[-100, -100, 700], [700, 700, 999]]), {
            "num_pixels": 6, "num_regions": 3, "min_region_size": 1,
            "max_region_size": 3, "mean_region_size": 2.0, "median_region_size": 2.0,
        })
        self.assertEqual(region_statistics([[1]])["num_regions"], 1)

    def test_invalid_partitions(self):
        bad = [[], np.empty((0, 3), int), [1, 2], [[[1]]],
               [[0.0]], [[True]], [["x"]], [[float("nan")]]]
        for labels in bad:
            with self.subTest(labels=repr(labels)):
                for metric in (region_statistics,
                               lambda x: rand_index(x, [[1]]),
                               lambda x: variation_of_information([[1]], x),
                               lambda x: color_homogeneity_mse(np.zeros((1, 1, 3)), x)):
                    with self.assertRaises(ValueError):
                        metric(labels)
        for metric in (rand_index, variation_of_information):
            with self.assertRaises(ValueError):
                metric([[1]], [[1, 2]])

    def test_invalid_images(self):
        for image in (np.zeros((1, 1)), np.zeros((1, 1, 4)),
                      np.zeros((2, 1, 3)), np.full((1, 1, 3), np.inf),
                      np.full((1, 1, 3), np.nan), np.full((1, 1, 3), "red")):
            with self.subTest(shape=image.shape):
                with self.assertRaises(ValueError):
                    color_homogeneity_mse(image, [[1]])
