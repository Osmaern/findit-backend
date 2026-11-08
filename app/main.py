import importlib
import pkgutil
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import routers as routers_package
from app.core.database import get_db

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="FindIt API", version="0.5.0")

# Every module in app/routers that defines `router` is mounted automatically.
# A new feature is therefore one new file, with no edits to this one.
for _module in pkgutil.iter_modules(routers_package.__path__):
    _router = getattr(importlib.import_module(f"app.routers.{_module.name}"), "router", None)
    if _router is not None:
        app.include_router(_router)


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# Serves the web pages. Must stay last so API routes are matched first.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
