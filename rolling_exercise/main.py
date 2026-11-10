
import uvicorn
from fastapi import FastAPI

from api.exception_handlers import register_exception_handlers
from api.routes.air_quality import router as air_quality_router
from api.routes.alerts import router as alerts_router

app = FastAPI()

app.include_router(air_quality_router)
app.include_router(alerts_router)

register_exception_handlers(app)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
