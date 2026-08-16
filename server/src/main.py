from pathlib import Path

import yaml
from fastapi import APIRouter, FastAPI, Depends
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from routes.package import router as package_router
from routes.search import router as search_router
from routes.stats import router as stats_router
# from collector.src.collector.collect import collect
from shared.classes import Registry
from shared.models import LastUpdated

app = FastAPI(
    # lifespan=lifespan,
    root_path="/"
)

router = APIRouter(prefix="/api")
app.include_router(router)
app.include_router(stats_router, tags=["stats"])
router.include_router(package_router, tags=["packages"])
router.include_router(search_router, tags=["search"])
REGISTRIES = []


def read_registries():
    print("Reading registries")
    with open("registries.yaml", "r") as f:
        data = yaml.safe_load(f)
        global REGISTRIES
        print(f"OLD {REGISTRIES}")
        REGISTRIES = [
            Registry(**fields)
            for _, fields in data["registries"].items()
        ]
        print(f"NEW {REGISTRIES}")


@router.get("/registries")
def get_registries():
    if len(REGISTRIES) < 1:
        read_registries()
    return REGISTRIES


@router.get("/last-updated")
async def get_last_updated(session: AsyncSession = Depends(get_session)) -> dict:
    row = await session.get(LastUpdated, 1)
    if row is None:
        return {"timestamp": None}
    return {"timestamp": row.timestamp.isoformat()}


# app.mount("/", StaticFiles(directory="static", html=True), name="static")


# @app.get("/{full_path:path}")
# async def spa_fallback(full_path: str, request: Request):
#     # If it's a real file in dist (favicon.ico, manifest.json, etc), serve it
#     DIST_DIR = Path("static")
#     candidate = DIST_DIR / full_path
#     if full_path and candidate.is_file():
#         return FileResponse(candidate)
#     # Otherwise hand control to the client-side router
#     return FileResponse(DIST_DIR / "index.html")
@app.get("/{path:path}")
async def spa(path: str):
    STATIC = Path("static")
    file = STATIC / path

    if path and file.exists() and file.is_file():
        return FileResponse(file)

    return FileResponse(STATIC / "index.html")
