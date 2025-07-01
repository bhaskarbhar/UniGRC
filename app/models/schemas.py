from pydantic import BaseModel

class ResponseData(BaseModel):
    id: int
    question: str
    likelihood_scale: int
    impact_scale: int
