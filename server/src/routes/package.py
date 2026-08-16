import markdown
from docutils.core import publish_string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from shared.models import Package, PackageRead, PackageDBOtoRead

router = APIRouter(prefix="/package", tags=["packages"])


@router.get("/{package:str}", response_model=PackageRead, tags=["packages"])
async def get_namespace(
        package: str,
        session: AsyncSession = Depends(get_session),
):
    print(package)
    stmt = (
        select(Package)
        .options(selectinload(Package.versions))
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
        .options(selectinload(Package.versions))
        .where(Package.name == package)
    )

    result = await session.exec(stmt)
    dbo: Package | None = result.first()
    if dbo and dbo.description and dbo.description_content_type:
        if "markdown" in dbo.description_content_type:
            return markdown.markdown(
                dbo.description,
                extensions=["fenced_code", "tables", "sane_lists"],
            )
        elif "rst" in dbo.description_content_type:
            return publish_string(dbo.description, writer_name="html5").decode("utf-8")
        return dbo.description
    raise HTTPException(404, f"{package} not found")
