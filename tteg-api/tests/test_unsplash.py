from __future__ import annotations

import unittest

from sources.unsplash import _build_image_url, _normalize_result


class UnsplashTests(unittest.TestCase):
    def test_build_image_url_applies_size_params(self) -> None:
        actual = _build_image_url(
            "https://images.unsplash.com/photo-123",
            "https://images.unsplash.com/fallback",
            1920,
            1080,
        )
        self.assertEqual(
            actual,
            "https://images.unsplash.com/photo-123?w=1920&h=1080&fit=crop&q=80",
        )

    def test_normalize_result_keeps_compliance_fields(self) -> None:
        photo = {
            "id": "abc",
            "description": "Golden hour",
            "width": 4000,
            "height": 3000,
            "urls": {
                "raw": "https://images.unsplash.com/raw",
                "regular": "https://images.unsplash.com/regular",
                "thumb": "https://images.unsplash.com/thumb",
            },
            "links": {
                "html": "https://unsplash.com/photos/abc",
                "download_location": "https://api.unsplash.com/photos/abc/download",
            },
            "user": {"name": "Jane Doe"},
        }

        normalized = _normalize_result(photo, 1600, 900)

        self.assertEqual(normalized.id, "abc")
        self.assertEqual(normalized.photographer, "Jane Doe")
        self.assertEqual(normalized.html_url, "https://unsplash.com/photos/abc")
        self.assertEqual(
            normalized.download_location,
            "https://api.unsplash.com/photos/abc/download",
        )
        self.assertIn("w=1600", normalized.image_url)


if __name__ == "__main__":
    unittest.main()
