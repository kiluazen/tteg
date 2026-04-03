from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from click.testing import CliRunner

from tteg._version import __version__
from tteg.cli import DEFAULT_API_URL, _resolve_api_url, main


class CliTests(unittest.TestCase):
    def test_resolve_api_url_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"TTEG_API_URL": "https://api.example.com"}, clear=True):
            self.assertEqual(_resolve_api_url(), "https://api.example.com")

    def test_resolve_api_url_defaults_to_local(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_resolve_api_url(), DEFAULT_API_URL)

    def test_cli_sends_request_and_prints_json(self) -> None:
        response = Mock()
        response.ok = True
        response.json.return_value = {"query": "cats", "results": []}

        runner = CliRunner()
        with patch("tteg.cli.requests.get", return_value=response) as get_mock:
            result = runner.invoke(main, ["cats", "--count", "3"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"query": "cats"', result.output)
        get_mock.assert_called_once()
        _, kwargs = get_mock.call_args
        self.assertEqual(kwargs["params"]["q"], "cats")
        self.assertEqual(kwargs["params"]["n"], 3)

    def test_cli_surfaces_api_errors(self) -> None:
        response = Mock()
        response.ok = False
        response.status_code = 429
        response.json.return_value = {"detail": "rate limited"}

        runner = CliRunner()
        with patch("tteg.cli.requests.get", return_value=response):
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
