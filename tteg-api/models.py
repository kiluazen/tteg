from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class ImageResult:
    id: str
    source: str
    image_url: str
    thumb_url: str
    photographer: str | None
    width: int | None
    height: int | None
    title: str | None
    html_url: str | None
    download_location: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
