from __future__ import annotations

from datetime import timezone

from sqlmodel import Session, col, select

from shared.models import Package, PackageVersion, PackageVersionFile

from .shared import PackagePayload


def _as_naive(dt):
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def ensure_packages(session: Session, registry: str, self_hosted: bool, names: set[str]) -> dict[str, Package]:
    if not names:
        return {}
    existing = session.exec(select(Package).where(Package.src_registry == registry, Package.self_hosted == self_hosted, col(Package.name).in_(names))).all()
    package_by_name = {package.name: package for package in existing}
    missing = names - set(package_by_name)
    if missing:
        session.add_all([Package(name=name, self_hosted=self_hosted, src_registry=registry) for name in sorted(missing)])
        session.flush()
        for package in session.exec(select(Package).where(Package.src_registry == registry, Package.self_hosted == self_hosted, col(Package.name).in_(missing))).all():
            package_by_name[package.name] = package
    return package_by_name


def upsert_versions_for_payloads(session: Session, registry: str, package_by_name: dict[str, Package], payloads: list[PackagePayload]) -> tuple[int, int]:
    package_ids = {package.id for package in package_by_name.values() if package.id is not None}
    version_keys = {(package_by_name[payload.name].id, version.version) for payload in payloads if payload.name in package_by_name for version in payload.versions}
    existing_versions: dict[tuple[int, str], PackageVersion] = {}
    if version_keys:
        pkg_ids = {pkg_id for pkg_id, _ in version_keys if pkg_id is not None}
        version_names = {version for _, version in version_keys}
        if pkg_ids and version_names:
            existing_versions = {(row.package_id, row.version): row for row in session.exec(select(PackageVersion).where(col(PackageVersion.package_id).in_(pkg_ids), col(PackageVersion.version).in_(version_names))).all()}
    existing_files: dict[tuple[int, str], PackageVersionFile] = {}
    if existing_versions:
        version_ids = {row.id for row in existing_versions.values() if row.id is not None}
        filenames = {version.filename for payload in payloads for version in payload.versions}
        if version_ids and filenames:
            existing_files = {(row.version_id, row.filename): row for row in session.exec(select(PackageVersionFile).where(col(PackageVersionFile.version_id).in_(version_ids), col(PackageVersionFile.filename).in_(filenames))).all()}
    inserted = updated = 0
    for payload in payloads:
        package = package_by_name.get(payload.name)
        if package is None or package.id is None:
            continue
        for field_name in (
            "summary", "author", "license", "author_email", "bugtrack_url", "classifiers",
            "description", "description_content_type", "docs_url", "home_page", "keywords",
            "license_expression", "license_files", "maintainer", "maintainer_email", "package_url",
            "platform", "project_url", "project_urls", "provides_extra", "release_url",
            "requires_dist", "requires_python", "version", "yanked",
        ):
            setattr(package, field_name, getattr(payload, field_name))
        session.add(package)
        # group the payload's files by version string so each version is one row
        for file in payload.versions:
            version_row = existing_versions.get((package.id, file.version))
            if version_row is None:
                version_row = PackageVersion(
                    package_id=package.id,
                    version=file.version,
                    requires_python=file.requires_python,
                    created_at=_as_naive(file.created_at),
                    yanked=file.yanked,
                    yanked_reason=file.yanked_reason,
                    src_registry=registry,
                )
                session.add(version_row)
                session.flush()
                existing_versions[(package.id, file.version)] = version_row
                inserted += 1
            else:
                version_row.requires_python = file.requires_python or version_row.requires_python
                file_created_at = _as_naive(file.created_at)
                existing_created_at = _as_naive(version_row.created_at)
                if file_created_at is not None and (existing_created_at is None or file_created_at < existing_created_at):
                    version_row.created_at = file_created_at
                else:
                    version_row.created_at = existing_created_at
                version_row.yanked, version_row.yanked_reason = file.yanked, file.yanked_reason
                version_row.src_registry = registry
                updated += 1
            file_row = existing_files.get((version_row.id, file.filename))
            if file_row is None:
                session.add(PackageVersionFile(
                    version_id=version_row.id,
                    filename=file.filename,
                    requires_python=file.requires_python,
                    packagetype=file.packagetype,
                    digest=file.digest,
                    size=file.size,
                    created_at=_as_naive(file.created_at),
                    yanked=file.yanked,
                    yanked_reason=file.yanked_reason,
                    url=file.url,
                    src_registry=registry,
                ))
                inserted += 1
            else:
                file_row.requires_python, file_row.packagetype = file.requires_python, file.packagetype
                file_row.digest, file_row.size = file.digest, file.size
                file_row.created_at, file_row.yanked, file_row.src_registry = _as_naive(file.created_at), file.yanked, registry
                file_row.yanked_reason, file_row.url = file.yanked_reason, file.url
                updated += 1
    return inserted, updated


def persist_name_chunk(session: Session, registry: str, self_hosted: bool, names: list[str]) -> int:
    packages = ensure_packages(session, registry, self_hosted, set(names))
    session.commit()
    return len(packages)


def persist_package_payload_batch(session: Session, registry: str, self_hosted: bool, payloads: list[PackagePayload]) -> tuple[int, int]:
    packages = ensure_packages(session, registry, self_hosted, {payload.name for payload in payloads})
    inserted, updated = upsert_versions_for_payloads(session, registry, packages, payloads)
    session.commit()
    return len(packages), inserted + updated

