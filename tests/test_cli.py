from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from tteg._version import __version__
from tteg.cli import DEFAULT_API_URL, _resolve_api_url, main
from tteg.client import TtegAPIError


class CliTests(unittest.TestCase):
    def test_resolve_api_url_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"TTEG_API_URL": "https://api.example.com"}, clear=True):
            self.assertEqual(_resolve_api_url(), "https://api.example.com")

    def test_resolve_api_url_defaults_to_local(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_resolve_api_url(), DEFAULT_API_URL)

    def test_cli_sends_request_and_prints_json(self) -> None:
        runner = CliRunner()
        with patch("tteg.cli.search_images", return_value={"query": "cats", "results": []}) as search_mock:
            result = runner.invoke(main, ["cats", "--count", "3"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"query": "cats"', result.output)
        search_mock.assert_called_once_with(
            "cats",
            count=3,
            orientation="any",
            width=None,
            height=None,
        )

    def test_save_downloads_selected_result(self) -> None:
        runner = CliRunner()
        with patch(
            "tteg.cli.search_and_save_image",
            return_value={
                "query": "cats",
                "saved_to": "/tmp/hero.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 1234,
                "result": {"id": 1, "title": "Orange cat on sofa"},
            },
        ) as save_mock:
            result = runner.invoke(main, ["save", "cats", "hero.jpg"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"saved_to": "/tmp/hero.jpg"', result.output)
        save_mock.assert_called_once_with(
            "cats",
            Path("hero.jpg"),
            index=1,
            orientation="any",
            width=None,
            height=None,
        )

    def test_batch_saves_many_images_from_manifest(self) -> None:
        runner = CliRunner()
        manifest = {
            "images": [
                {
                    "query": "saas dashboard hero",
                    "output": "./public/images/hero",
                    "orientation": "landscape",
                },
                {
                    "query": "team collaboration office",
                    "output": "./public/images/team",
                    "index": 2,
                },
            ]
        }

        with runner.isolated_filesystem():
            manifest_path = Path("landing-images.json")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with patch(
                "tteg.cli.search_and_save_image",
                side_effect=[
                    {"query": "saas dashboard hero", "saved_to": "public/images/hero.jpg"},
                    {"query": "team collaboration office", "saved_to": "public/images/team.jpg"},
                ],
            ) as save_mock:
                result = runner.invoke(main, ["batch", str(manifest_path)])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"saved_to": "public/images/hero.jpg"', result.output)
        self.assertEqual(save_mock.call_count, 2)
        self.assertEqual(save_mock.call_args_list[0].args[0], "saas dashboard hero")
        self.assertEqual(save_mock.call_args_list[0].args[1], Path("./public/images/hero"))
        self.assertEqual(save_mock.call_args_list[1].kwargs["index"], 2)

    def test_cli_surfaces_api_errors(self) -> None:
        runner = CliRunner()
        with patch("tteg.cli.search_images", side_effect=TtegAPIError(429, "rate limited")):
            result = runner.invoke(main, ["cats"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("rate limited", result.output)

    def test_cli_reports_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(__version__, result.output)


if __name__ == "__main__":
    unittest.main()
