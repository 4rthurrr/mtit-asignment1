from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routes import auth as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Auth Module",
    description="JWT-based authentication with FastAPI + SQLite",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
