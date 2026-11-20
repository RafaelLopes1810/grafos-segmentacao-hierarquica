"""Validação executável com unittest; pytest também descobre esta classe."""
import unittest
import numpy as np

from app.evaluation.metrics import color_homogeneity_mse
from app.segmentation.hierarchy import HierarchyTree


def assert_nested(fine, coarse):
    np.testing.assert_equal(fine.shape, coarse.shape)
    for region in np.unique(fine):
        np.testing.assert_equal(np.unique(coarse[fine == region]).size, 1)


class HierarchyInvariantTests(unittest.TestCase):
    def test_all_count_cuts_and_merge_identity(self):
        for shape in [(1, 1), (1, 7), (7, 1), (3, 4)]:
            for seed in [0, 19, 2026]:
                for constant in [False, True]:
                    with self.subTest(shape=shape, seed=seed, constant=constant):
                        image = np.random.default_rng(seed).integers(0, 256, (*shape, 3), dtype=np.uint8)
                        if constant:
                            image[:] = 73
                        labels = np.arange(np.prod(shape)).reshape(shape) * 11 + 10
                        tree = HierarchyTree(image, labels)
                        count = labels.size
                        self.assertEqual(len(tree.merges), count - 1)
                        self.assertEqual(len(tree.nodes), 2 * count - 1)
                        self.assertIsNone(tree.nodes[tree.root_id].parent)
                        for node in tree.merges:
                            self.assertEqual(len(set(node.children)), 2)
                            for child in node.children:
                                self.assertEqual(tree.nodes[child].parent, node.node_id)
                                self.assertLessEqual(tree.nodes[child].height, node.height)
                        fine = tree.cut_by_num_regions(count).labels
                        previous = color_homogeneity_mse(image, fine)
                        self.assertEqual(previous, 0)
                        for n in range(count - 1, 0, -1):
                            cut = tree.cut_by_num_regions(n)
                            coarse = cut.labels
                            self.assertEqual(np.unique(coarse).size, n)
                            self.assertEqual(cut.num_regions, n)
                            self.assertEqual(sum(r.area for r in cut.rag.regions.values()), labels.size)
                            assert_nested(fine, coarse)
                            groups = [np.unique(fine[coarse == r]) for r in np.unique(coarse)]
                            pairs = [group for group in groups if len(group) == 2]
                            self.assertEqual(len(pairs), 1)
                            a, b = pairs[0]
                            x = image[fine == a].astype(float)
                            y = image[fine == b].astype(float)
                            delta = (len(x) * len(y) / (len(x) + len(y))
                                     * np.sum((x.mean(0) - y.mean(0)) ** 2) / image.size)
                            current = color_homogeneity_mse(image, coarse)
                            self.assertGreaterEqual(current, previous - 1e-9)
                            self.assertAlmostEqual(current - previous, delta, places=8)
                            fine, previous = coarse, current

    def test_non_singleton_regions_and_thresholds(self):
        image = np.random.default_rng(7).integers(0, 256, (4, 4, 3), dtype=np.uint8)
        labels = np.array([[10, 10, 30, 30], [10, 10, 30, 30],
                           [70, 70, 90, 90], [70, 70, 90, 90]])
        tree = HierarchyTree(image, labels)
        fine = tree.cut_by_num_regions(4).labels
        mse = color_homogeneity_mse(image, fine)
        for threshold in sorted({0.0, *(node.height for node in tree.merges)}):
            coarse = tree.cut_by_threshold(threshold).labels
            assert_nested(fine, coarse)
            current = color_homogeneity_mse(image, coarse)
            self.assertGreaterEqual(current, mse - 1e-9)
            fine, mse = coarse, current
        self.assertEqual(np.unique(fine).size, 1)
        levels = tree.build_levels(100)
        self.assertLessEqual(len(levels), 4)
        for a, b in zip(levels, levels[1:]):
            assert_nested(a.labels, b.labels)

    def test_invalid_cuts(self):
        tree = HierarchyTree(np.zeros((2, 2, 3), dtype=np.uint8), np.arange(4).reshape(2, 2))
        for n in [0, -1, True, 1.5, 5]:
            with self.subTest(count=n), self.assertRaises(ValueError):
                tree.cut_by_num_regions(n)
        for threshold in [-1, float("nan"), float("inf"), True]:
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                tree.cut_by_threshold(threshold)
