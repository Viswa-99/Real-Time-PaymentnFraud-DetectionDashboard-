from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title="NSO Survey Data Validation Platform",
    description="Intelligent survey data validation using probabilistic and machine learning techniques",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/")
async def root():
    return {"message": "NSO Survey Data Validation Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "survey-validation-platform"}