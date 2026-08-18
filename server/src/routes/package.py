import markdown
from docutils.core import publish_string
from fastapi import APIRouter, Depends, HTTPException, Query
from packaging.requirements import Requirement
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from shared.models import Package, PackageVersion, PackageRead, PackageDBOtoRead, PackageRequirement, PackagePage

router = APIRouter(prefix="/package", tags=["packages"])


@router.get("/", response_model=PackagePage, tags=["packages"])
async def get_all_packages(
        limit: int = Query(50, ge=0, le=500),
        offset: int = Query(0, ge=0),
        session: AsyncSession = Depends(get_session),
):
    total_result = await session.exec(
        select(func.count()).select_from(Package)
    )
    total = total_result.one()

    stmt = (
        select(Package).order_by(Package.name)
    )
    if limit > 0:
        stmt = stmt.offset(offset).limit(limit)

    result = await session.exec(stmt)
    items = [
        PackageDBOtoRead(pack)
        for pack in result.all()
    ]

    return PackagePage(total=total, limit=limit, offset=offset, items=items)


@router.get("/{package:str}", response_model=PackageRead, tags=["packages"])
async def get_namespace(
        package: str,
        session: AsyncSession = Depends(get_session),
):
    print(package)
    stmt = (
        select(Package)
        .options(selectinload(Package.versions).selectinload(PackageVersion.files))
        .where(Package.name == package)
    )

    result = await session.exec(stmt)
    dbo = result.first()
    if dbo:
        return PackageDBOtoRead(dbo, True)
    raise HTTPException(404, f"{package} not found")


@router.get("/{package:str}/readme", tags=["packages"])
async def get_markdown(
        package: str,
        session: AsyncSession = Depends(get_session),
):
    print(package)
    stmt = (
        select(Package)
        .where(Package.name == package)
    )

    result = await session.exec(stmt)
    dbo: Package | None = result.first()
    if dbo:
        if dbo.description and dbo.description_content_type:
            if "markdown" in dbo.description_content_type:
                return markdown.markdown(
                    dbo.description,
                    extensions=["fenced_code", "tables", "sane_lists"],
                )
            elif "rst" in dbo.description_content_type:
                return publish_string(dbo.description, writer_name="html5").decode("utf-8")
        return dbo.description
    raise HTTPException(404, f"{package} not found")


@router.get("/{package:str}/deps", response_model=list[PackageRequirement], tags=["packages"])
async def det_deps(
        package: str,
        session: AsyncSession = Depends(get_session),
):
    print(package)
    stmt = (
        select(Package)
        .where(Package.name == package)
    )

    result = await session.exec(stmt)
    dbo: Package | None = result.first()
    if dbo:
        requires = dbo.requires_dist
        res = [Requirement(req) for req in requires]
        return [
            PackageRequirement(
                package_id=dbo.id,
                name=req.name,
                url=req.url,
                extra=set(str(s) for s in req.extras),
                specifier=str(req.specifier),
                marker=str(req.marker)
            )
            for req in res
        ]

    raise HTTPException(404, f"{package} not found")
