from __future__ import annotations

from sqlmodel import Session, col, select

from shared.models import Package, PackageVersion

from .shared import PackagePayload


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
    filenames = {version.filename for payload in payloads for version in payload.versions}
    existing_by_key: dict[tuple[int, str], PackageVersion] = {}
    if package_ids and filenames:
        existing_by_key = {(row.package_id, row.filename): row for row in session.exec(select(PackageVersion).where(col(PackageVersion.package_id).in_(package_ids), col(PackageVersion.filename).in_(filenames))).all() if row.filename is not None}
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
        for version in payload.versions:
            row = existing_by_key.get((package.id, version.filename))
            if row is None:
                session.add(PackageVersion(
                    package_id=package.id,
                    version=version.version,
                    requires_python=version.requires_python,
                    packagetype=version.packagetype,
                    filename=version.filename,
                    digest=version.digest,
                    size=version.size,
                    created_at=version.created_at,
                    yanked=version.yanked,
                    yanked_reason=version.yanked_reason,
                    src_registry=registry,
                    url=version.url
                ))
                inserted += 1
            else:
                row.requires_python, row.packagetype = version.requires_python, version.packagetype
                row.digest, row.size = version.digest, version.size
                row.created_at, row.yanked, row.src_registry = version.created_at, version.yanked, registry
                row.yanked_reason, row.url = version.yanked_reason, version.url
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

