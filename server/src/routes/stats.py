from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlmodel import SQLModel, select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.models import Package, Stats, PackageVersion, PackageVersionFile

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import selectinload

from db import get_session

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/")
async def stats(session: AsyncSession = Depends(get_session)) -> Stats:

    pack_result = await session.exec(
        select(func.count()).select_from(
            Package)
    )
    packs = pack_result.one()

    versions_result = await session.exec(
        select(func.count()).select_from(PackageVersion)
    )
    versions = versions_result.one()

    files_result = await session.exec(
        select(func.count()).select_from(PackageVersionFile)
    )
    files = files_result.one()
    print(files)

    return Stats(packages=packs, versions=versions, files=files)

