from sys import base_prefix

import uvicorn
from fastapi import FastAPI
from user.router import router as users_router

app = FastAPI(
    title="epg_test_task",
    base_prefix="api/"
)

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8008, reload=True)