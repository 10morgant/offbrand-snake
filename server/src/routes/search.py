from fastapi import APIRouter, Query, Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from shared.models import Package, PackageDBOtoRead, PackagePage

router = APIRouter(prefix="/search", tags=["search"])


async def search_table(
        session: AsyncSession,
        model,
        url: str,
        q: str,
        limit: int = 25,
        return_stmt: bool = False,
):
    stmt = select(model).where(model.src_registry == url).where(
        model.name.ilike(f"{q}%")).limit(limit)
    if return_stmt:
        return stmt
    result = await session.exec(stmt)
    return result.all()


@router.get("/", tags=["search"])
async def search(
        url: str = Query(),
        q: str = Query(..., min_length=1, max_length=100),
        session: AsyncSession = Depends(get_session)
):
    query = q.strip()
    query = query.removesuffix("/")
    query = query.split(":")[0] if ":" in query else query

    packages = await search_table(session, Package, url, query)
    return {
        "packages": [r.dict() for r in packages],
    }


@router.get("/page", tags=["search"])
async def search_page(
        url: str = Query(),
        q: str = Query(..., min_length=1, max_length=100),
        limit: int = Query(50, ge=0, le=500),
        offset: int = Query(0, ge=0),
        session: AsyncSession = Depends(get_session),
):
    print("namespace: ", url, limit, offset)
    total_result = await session.exec(
        select(func.count()).select_from(Package).where(
            Package.src_registry == url)
    )
    total = total_result.one()

    query = q.strip()
    query = query.removesuffix("/")
    query = query.split(":")[0] if ":" in query else query

    stmt = await search_table(session, Package, url, query,True)
    # return {
    #     "packages": [r.dict() for r in packages],
    # }
    if limit > 0:
        stmt = stmt.offset(offset).limit(limit)

    result = await session.exec(stmt)
    items = [
        PackageDBOtoRead(package, False)
        for package in result.all()
    ]

    return PackagePage(total=total, limit=limit, offset=offset, items=items)
