from __future__ import annotations

import json
from pathlib import Path

from datetime import datetime
from typing import Any, Callable

import httpx
from rich.console import Console

from .http_client import async_request_with_retries
from .shared import PackagePayload, VersionFile

console = Console()


def parse_upload_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def fetch_package_metadata(
        client: httpx.AsyncClient,
        index: str,
        package_name: str,
        skip_versions: frozenset[str] = frozenset(),
        on_versions_discovered: Callable[[int], None] | None = None,
        on_version_processed: Callable[[], None] | None = None,
        log: Callable[[str], None] | None = None,
        save: bool = True,
) -> tuple[PackagePayload | None, int]:
    log_fn = log or console.log
    try:
        response = await async_request_with_retries(client, "GET", f"{index}/pypi/{package_name}/json", log=log)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            log_fn(f"[yellow]skip[/yellow] no metadata for {package_name}")
            return None, 0
        raise

    data = response.json()
    info = data.get("info") or {}
    releases: dict[str, list[dict[str, Any]]] = data.get("releases") or {}
    if data and save:
        out = Path("data/pypi") / package_name
        log_fn(f"Saving {package_name} {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(data, open(out, "w"), indent=4)

    pending = [version for version in releases if version not in skip_versions]
    skipped = len(releases) - len(pending)
    if on_versions_discovered:
        on_versions_discovered(len(pending))

    versions: list[VersionFile] = []
    for version in pending:
        if on_version_processed:
            on_version_processed()
        for file_info in releases.get(version) or []:
            digests = file_info.get("digests") or {}
            versions.append(VersionFile(
                version=version,
                filename=file_info.get("filename") or "",
                packagetype=file_info.get("packagetype"),
                size=file_info.get("size"),
                digest=digests.get("sha256"),
                created_at=parse_upload_time(file_info.get("upload_time_iso_8601")),
                requires_python=file_info.get("requires_python"),
                yanked=bool(file_info.get("yanked", False)),
                yanked_reason=file_info.get("yanked_reason"),
            ))

    payload = PackagePayload(
        name=package_name,
        summary=info.get("summary"),
        author=info.get("author"),
        license=info.get("license"),
        author_email=info.get("author_email"),
        bugtrack_url=info.get("bugtrack_url"),
        classifiers=info.get("classifiers") or [],
        description=info.get("description"),
        description_content_type=info.get("description_content_type"),
        docs_url=info.get("docs_url"),
        home_page=info.get("home_page"),
        keywords=info.get("keywords"),
        license_expression=info.get("license_expression"),
        license_files=info.get("license_files") or [],
        maintainer=info.get("maintainer"),
        maintainer_email=info.get("maintainer_email"),
        package_url=info.get("package_url"),
        platform=info.get("platform"),
        project_url=info.get("project_url"),
        project_urls=info.get("project_urls") or {},
        provides_extra=info.get("provides_extra") or [],
        release_url=info.get("release_url"),
        requires_dist=info.get("requires_dist") or [],
        requires_python=info.get("requires_python"),
        version=info.get("version"),
        yanked=bool(info.get("yanked", False)),
        yanked_reason=info.get("yanked_reason"),
        versions=versions,
    )
    return payload, skipped
