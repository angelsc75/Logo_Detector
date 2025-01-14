from pydantic import BaseModel
from typing import Dict, List

class BrandStats(BaseModel):
    total_detections: int
    frames_with_detections: int
    percentage_time: float

class DetectionResponse(BaseModel):
    video_name: str
    duration: float
    total_frames: int
    detections: Dict[str, BrandStats]