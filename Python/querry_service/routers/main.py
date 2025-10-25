from fastapi import FastAPI
from querry_service.routers.chat_router import router
from querry_service.models.HealthyResponse import HealthyResponse

try:
    app = FastAPI()
    app.include_router(router)
except Exception as e:
    print(e)


@app.get("/health")
def healthChecker():
    healthyResponse = HealthyResponse(status="Healthy")
    return healthyResponse