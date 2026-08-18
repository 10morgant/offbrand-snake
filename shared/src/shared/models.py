from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field, Relationship, Session, BigInteger

class LastUpdated(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Package(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # MySQL/MariaDB requires a length for indexed/text columns
    name: str = Field(max_length=255, index=True)
    self_hosted: bool = False
    src_registry: str = "?"
    summary: str | None = None
    author: str | None = None
    license: str | None = None
    author_email: str | None = None
    bugtrack_url: str | None = None
    classifiers: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    description_content_type: str | None = None
    docs_url: str | None = None
    home_page: str | None = None
    keywords: str | None = None
    license_expression: str | None = None
    license_files: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    maintainer: str | None = None
    maintainer_email: str | None = None
    package_url: str | None = None
    platform: str | None = None
    project_url: str | None = None
    project_urls: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    provides_extra: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    release_url: str | None = None
    requires_dist: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    requires_python: str | None = None
    version: str | None = None
    yanked: bool = False

    versions: List["PackageVersion"] = Relationship(back_populates="package")


class PackageVersion(SQLModel, table=True):
    __tablename__ = "versions"

    id: int | None = Field(default=None, primary_key=True)
    package_id: int = Field(foreign_key="package.id", index=True)
    version: str = Field(index=True)
    requires_python: str | None = None
    created_at: datetime | None = Field(default=None, index=True)
    yanked: bool = False
    yanked_reason: str | None = None
    src_registry: str = Field(index=True)

    package: Package = Relationship(back_populates="versions")
    files: List["PackageVersionFile"] = Relationship(back_populates="version")


class PackageVersionFile(SQLModel, table=True):
    __tablename__ = "version_files"

    id: int | None = Field(default=None, primary_key=True)
    version_id: int = Field(foreign_key="versions.id", index=True)
    filename: str = Field(index=True)
    requires_python: str | None = None
    packagetype: str | None = None
    digest: str | None = Field(default=None, index=True)
    size: int | None = Field(default=None, sa_type=BigInteger)
    created_at: datetime | None = Field(default=None, index=True)
    yanked: bool = False
    yanked_reason: str | None = None
    url: str | None = None
    src_registry: str = Field(index=True)

    version: PackageVersion = Relationship(back_populates="files")


# ---- Read view shared ----

class PackageVersionFileRead(SQLModel):
    id: int
    version_id: Optional[int] = None
    filename: str
    requires_python: str | None = None
    packagetype: str | None = None
    digest: str | None = None
    size: int | None = None
    created_at: datetime | None = None
    yanked: bool = False
    yanked_reason: str | None = None
    url: str | None = None


class PackageVersionRead(SQLModel):
    id: int
    package_id: Optional[int] = None
    version: str
    requires_python: str | None = None
    created_at: datetime | None = None
    yanked: bool = False
    yanked_reason: str | None = None
    files: List[PackageVersionFileRead] = Field(default_factory=list)


class PackageRead(SQLModel):
    id: int
    name: str
    self_hosted: bool
    versions: List[PackageVersionRead] = Field(default_factory=list)
    registry: str
    summary: str | None = None
    author: str | None = None
    license: str | None = None
    author_email: str | None = None
    bugtrack_url: str | None = None
    classifiers: list[str] = Field(default_factory=list)
    description: str | None = None
    description_content_type: str | None = None
    docs_url: str | None = None
    home_page: str | None = None
    keywords: str | None = None
    license_expression: str | None = None
    license_files: list[str] = Field(default_factory=list)
    maintainer: str | None = None
    maintainer_email: str | None = None
    package_url: str | None = None
    platform: str | None = None
    project_url: str | None = None
    project_urls: dict[str, str] = Field(default_factory=dict)
    provides_extra: list[str] = Field(default_factory=list)
    release_url: str | None = None
    requires_dist: list[str] = Field(default_factory=list)
    requires_python: str | None = None
    version: str | None = None
    yanked: bool = False


class PackagePage(SQLModel):
    total: int
    limit: int
    offset: int
    items: List[PackageRead]


class Stats(SQLModel):
    packages: int
    versions: int

def set_last_updated(session: Session) -> LastUpdated:
    row = session.get(LastUpdated, 1)
    now = datetime.now(timezone.utc)
    if row is None:
        row = LastUpdated(id=1, timestamp=now)
    else:
        row.timestamp = now
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def VersionFileDBOtoRead(dbo: PackageVersionFile) -> PackageVersionFileRead:
    return PackageVersionFileRead(
        id=dbo.id,
        version_id=dbo.version_id,
        filename=dbo.filename,
        requires_python=dbo.requires_python,
        packagetype=dbo.packagetype,
        digest=dbo.digest,
        size=dbo.size,
        created_at=dbo.created_at,
        yanked=dbo.yanked,
        yanked_reason=dbo.yanked_reason,
        url=dbo.url,
    )


def VersionDBOtoRead(dbo: PackageVersion):
    return PackageVersionRead(
        id=dbo.id,
        version=dbo.version,
        package_id=dbo.package_id,
        requires_python=dbo.requires_python,
        created_at=dbo.created_at,
        yanked=dbo.yanked,
        yanked_reason=dbo.yanked_reason,
        files=[VersionFileDBOtoRead(f) for f in dbo.files],
    )



def PackageDBOtoRead(dbo: Package, versions: bool = False) -> PackageRead:
    return PackageRead(
        id=dbo.id,
        name=dbo.name,
        self_hosted=dbo.self_hosted,
        registry=dbo.src_registry,
        summary=dbo.summary,
        author=dbo.author,
        license=dbo.license,
        author_email=dbo.author_email,
        bugtrack_url=dbo.bugtrack_url,
        classifiers=dbo.classifiers,
        description=dbo.description,
        description_content_type=dbo.description_content_type,
        docs_url=dbo.docs_url,
        home_page=dbo.home_page,
        keywords=dbo.keywords,
        license_expression=dbo.license_expression,
        license_files=dbo.license_files,
        maintainer=dbo.maintainer,
        maintainer_email=dbo.maintainer_email,
        package_url=dbo.package_url,
        platform=dbo.platform,
        project_url=dbo.project_url,
        project_urls=dbo.project_urls,
        provides_extra=dbo.provides_extra,
        release_url=dbo.release_url,
        requires_dist=dbo.requires_dist,
        requires_python=dbo.requires_python,
        version=dbo.version,
        yanked=dbo.yanked,
        versions=[VersionDBOtoRead(v) for v in dbo.versions] if versions else []
    )


class PackageRequirement(SQLModel):
    package_id: int
    name: str
    url: str | None = None
    extras: set[str] = Field(default_factory=set)
    specifier: str | None = None
    marker: str | None = None