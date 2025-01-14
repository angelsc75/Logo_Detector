from fastapi import APIRouter, UploadFile, File
from ..schemas.requests import DetectionRequest
from ..schemas.responses import DetectionResponse
from ..services.detection import DetectionService

router = APIRouter()

@router.post("/video", response_model=DetectionResponse)
async def detect_logos_in_video(
    file: UploadFile = File(...),
    conf_threshold: float = 0.25
):
    detection_service = DetectionService()
    result = await detection_service.process_video(file, conf_threshold)
    return result