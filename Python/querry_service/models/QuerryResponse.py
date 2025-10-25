from pydantic import BaseModel


class QuerryResponse(BaseModel):
    message : str