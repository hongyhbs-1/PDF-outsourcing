#!/usr/bin/env python3
"""render_all_samples CLI 选择逻辑测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import render_all_samples


class RenderAllSamplesCliTest(unittest.TestCase):
    def test_discover_sample_files_returns_sorted_json_names(self) -> None:
        with TemporaryDirectory() as temp_dir:
            samples_dir = Path(temp_dir)
            (samples_dir / "b.json").write_text("{}", encoding="utf-8")
            (samples_dir / "a.json").write_text("{}", encoding="utf-8")
            (samples_dir / "notes.txt").write_text("ignore", encoding="utf-8")

            self.assertEqual(
                render_all_samples.discover_sample_files(samples_dir),
                ["a.json", "b.json"],
            )

    def test_discover_sample_files_rejects_empty_json_dir(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                render_all_samples.discover_sample_files(Path(temp_dir))

    def test_select_samples_without_limit_returns_all(self) -> None:
        sample_files = ["a.json", "b.json"]

        self.assertEqual(
            render_all_samples.select_samples(sample_files, None),
            sample_files,
        )

    def test_select_samples_with_one_returns_first_sample(self) -> None:
        sample_files = ["a.json", "b.json"]

        self.assertEqual(
            render_all_samples.select_samples(sample_files, 1),
            sample_files[:1],
        )

    def test_select_samples_with_two_returns_first_two_samples(self) -> None:
        sample_files = ["a.json", "b.json", "c.json"]

        self.assertEqual(
            render_all_samples.select_samples(sample_files, 2),
            sample_files[:2],
        )

    def test_select_samples_rejects_zero(self) -> None:
        with self.assertRaises(ValueError):
            render_all_samples.select_samples(["a.json"], 0)

    def test_select_samples_rejects_out_of_range_value(self) -> None:
        with self.assertRaises(ValueError):
            render_all_samples.select_samples(["a.json"], 2)


if __name__ == "__main__":
    unittest.main()
