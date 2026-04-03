from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models import ImageResult


class ApiTests(unittest.TestCase):
    def test_search_endpoint_returns_results(self) -> None:
        fake_results = [
            ImageResult(
                id="1",
                source="unsplash",
                image_url="https://images.example/full.jpg",
                thumb_url="https://images.example/thumb.jpg",
                photographer="Jane",
                width=1000,
                height=800,
                title="Title",
                html_url="https://unsplash.com/photos/x",
                download_location="https://api.unsplash.com/photos/x/download",
            )
        ]

        with patch("main._resolve_access_key", return_value="secret"), patch(
            "main.search_unsplash",
            return_value=fake_results,
        ):
            client = TestClient(app)
            response = client.get("/search", params={"q": "cats"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "cats")
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(
            payload["results"][0],
            {
                "id": 1,
                "title": "Title",
                "image_url": "https://images.example/full.jpg",
                "thumb_url": "https://images.example/thumb.jpg",
            },
        )

    def test_missing_secret_returns_500(self) -> None:
        with patch("main._resolve_access_key", return_value=""):
            client = TestClient(app)
            response = client.get("/search", params={"q": "cats"})

        self.assertEqual(response.status_code, 500)
        self.assertIn("UNSPLASH_ACCESS_KEY", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
