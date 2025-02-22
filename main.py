from fastapi import FastAPI
from contextlib import asynccontextmanager
from postgres import init_postgres, close_postgres
from controller import router
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_postgres()
    yield
    await close_postgres()


app: FastAPI = FastAPI(lifespan=lifespan, title="Prompt Buddy FastAPI PostgreSQL")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)