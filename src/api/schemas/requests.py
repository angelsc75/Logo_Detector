from pydantic import BaseModel

class DetectionRequest(BaseModel):
    conf_threshold: float = 0.25