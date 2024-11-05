import uvicorn

from fastapi import FastAPI

from epg_test_task.src.user.router import router as users_router

app = FastAPI(
    title="epg_test_task",
)

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8009, reload=True)