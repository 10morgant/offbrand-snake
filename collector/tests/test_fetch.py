from __future__ import annotations

import asyncio

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from collector.utils.pypi import fetch_package_metadata, parse_upload_time
from collector.utils.shared import PackagePayload, chunked
from collector.utils.storage import persist_name_chunk, persist_package_payload_batch
from shared.models import Package


@pytest.mark.parametrize(
    ("items", "chunk_size", "expected"),
    [
        (["a", "b", "c", "d"], 2, [["a", "b"], ["c", "d"]]),
    ],
)
def test_chunked_splits_items_into_fixed_sized_groups(
    items: list[str], chunk_size: int, expected: list[list[str]]
) -> None:
    assert list(chunked(items, chunk_size)) == expected


def test_parse_upload_time_parses_iso8601_with_z_suffix() -> None:
    parsed = parse_upload_time("2024-01-02T03:04:05Z")

    assert parsed is not None
    assert parsed.isoformat() == "2024-01-02T03:04:05+00:00"


def test_persist_name_chunk_creates_packages() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        packages = persist_name_chunk(session, "https://pypi.org", False, ["requests", "flask", "numpy"])

        assert packages == 3

        package_rows = session.exec(select(Package)).all()
        assert {row.name for row in package_rows} == {"requests", "flask", "numpy"}


def test_persist_package_payload_stores_core_metadata() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    payload = PackagePayload(
        name="rich",
        summary="Rich terminal formatting",
        author="Will McGugan",
        license="MIT",
        description="# Rich",
        description_content_type="text/markdown",
        project_urls={"Documentation": "https://rich.readthedocs.io"},
        provides_extra=["jupyter"],
        requires_dist=["markdown-it-py>=2.2.0"],
    )

    with Session(engine) as session:
        persist_package_payload_batch(session, "https://pypi.org", False, [payload])
        package = session.exec(select(Package).where(Package.name == "rich")).one()

        assert package.description == "# Rich"
        assert package.description_content_type == "text/markdown"
        assert package.project_urls == {"Documentation": "https://rich.readthedocs.io"}
        assert package.provides_extra == ["jupyter"]
        assert package.requires_dist == ["markdown-it-py>=2.2.0"]
        assert package.classifiers == []


def test_fetch_package_metadata_builds_payload_from_release_files() -> None:
    payload_json = {
        "info": {
            "summary": "A test package",
            "author": "Jane Doe",
            "license": "MIT",
            "description": "# Example",
            "description_content_type": "text/markdown",
            "project_urls": {"Documentation": "https://example.test/docs"},
            "provides_extra": ["jupyter"],
            "requires_dist": ["widgets>=1; extra == 'jupyter'"],
        },
        "releases": {
            "1.0.0": [
                {
                    "filename": "example-1.0.0.tar.gz",
                    "packagetype": "sdist",
                    "size": 1234,
                    "digests": {"sha256": "abc123"},
                    "upload_time_iso_8601": "2024-01-02T03:04:05Z",
                    "requires_python": ">=3.8",
                    "yanked": False,
                },
            ],
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/pypi/example/json"
        return httpx.Response(200, json=payload_json)

    async def run() -> tuple:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_package_metadata(client, "https://pypi.org", "example")

    payload, skipped = asyncio.run(run())

    assert payload is not None
    assert skipped == 0
    assert payload.summary == "A test package"
    assert payload.author == "Jane Doe"
    assert payload.license == "MIT"
    assert payload.description == "# Example"
    assert payload.description_content_type == "text/markdown"
    assert payload.project_urls == {"Documentation": "https://example.test/docs"}
    assert payload.provides_extra == ["jupyter"]
    assert payload.requires_dist == ["widgets>=1; extra == 'jupyter'"]
    assert len(payload.versions) == 1
    version = payload.versions[0]
    assert version.version == "1.0.0"
    assert version.filename == "example-1.0.0.tar.gz"
    assert version.packagetype == "sdist"
    assert version.digest == "abc123"
    assert version.requires_python == ">=3.8"
    assert version.yanked is False


def test_fetch_package_metadata_defaults_missing_metadata_safely() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"releases": {}})

    async def run() -> tuple:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_package_metadata(client, "https://pypi.org", "example")

    payload, _ = asyncio.run(run())

    assert payload is not None
    assert payload.description is None
    assert payload.description_content_type is None
    assert payload.project_urls == {}
    assert payload.provides_extra == []
    assert payload.requires_dist == []

