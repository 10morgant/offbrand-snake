from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

DEFAULT_DB_URL = "postgresql+psycopg2://appuser:StrongPassword123@localhost:5432/python"
DEFAULT_NAMES_FOLDER = Path("data/")
DEFAULT_NAMES_FOLDER.mkdir(parents=True, exist_ok=True)
DEFAULT_NAMES_FILE = DEFAULT_NAMES_FOLDER / "package_names.txt"
REQUEST_TIMEOUT_SECONDS = 180.0
RETRY_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
MAX_RETRIES = 6
RETRY_BASE_DELAY = 1.0


@dataclass
class VersionFile:
    version: str
    filename: str
    packagetype: str | None
    size: int | None
    digest: str | None
    created_at: datetime | None
    requires_python: str | None
    yanked: bool
    yanked_reason: str | None


@dataclass
class PackagePayload:
    name: str
    summary: str | None
    author: str | None
    license: str | None
    author_email: str | None = None
    bugtrack_url: str | None = None
    classifiers: list[str] = field(default_factory=list)
    description: str | None = None
    description_content_type: str | None = None
    docs_url: str | None = None
    home_page: str | None = None
    keywords: str | None = None
    license_expression: str | None = None
    license_files: list[str] = field(default_factory=list)
    maintainer: str | None = None
    maintainer_email: str | None = None
    package_url: str | None = None
    platform: str | None = None
    project_url: str | None = None
    project_urls: dict[str, str] = field(default_factory=dict)
    provides_extra: list[str] = field(default_factory=list)
    release_url: str | None = None
    requires_dist: list[str] = field(default_factory=list)
    requires_python: str | None = None
    version: str | None = None
    yanked: bool = False
    yanked_reason: str | None = None
    versions: list[VersionFile] = field(default_factory=list)


def iter_name_file(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as file:
        for raw in file:
            name = raw.strip()
            if name:
                yield name


def count_names(path: Path) -> int:
    return sum(1 for name in iter_name_file(path) if name)


def chunked(items: Iterable[str], chunk_size: int) -> Iterator[list[str]]:
    batch: list[str] = []
    for item in items:
        batch.append(item)
        if len(batch) >= chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch
