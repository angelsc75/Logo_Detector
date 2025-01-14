from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import detect, train

app = FastAPI(
    title="Logo Detection API",
    description="API for detecting logos in videos and images",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(detect.router, prefix="/api/v1/detect", tags=["detect"])
app.include_router(train.router, prefix="/api/v1/train", tags=["train"])






    




