"""Drone Detection Dashboard — FastAPI entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import database
from simulation.engine import SimulationEngine
from routers.api import router as api_router
from routers.ws import router as ws_router
from config import HOST, PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    engine = SimulationEngine()
    task = asyncio.create_task(engine.run())
    print(f"Drone Detection Dashboard running at http://localhost:{PORT}")
    yield
    task.cancel()


app = FastAPI(title="Drone Detection Dashboard", lifespan=lifespan)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
