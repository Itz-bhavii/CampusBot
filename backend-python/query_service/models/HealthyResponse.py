from pydantic import BaseModel

class HealthyResponse(BaseModel):
    status : str