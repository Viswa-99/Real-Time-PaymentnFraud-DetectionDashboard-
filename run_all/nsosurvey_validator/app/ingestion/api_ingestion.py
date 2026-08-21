from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import json
import asyncio
import aiohttp

from app.core.db import get_async_db, engine
from app.core.config import settings

router = APIRouter(prefix="/ingestion", tags=["data-ingestion"])


@router.post("/upload_csv/", status_code=202)
async def upload_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db)
):
    """Upload CSV data for batch ingestion."""
    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Basic validation and normalization
        result = {
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {c: str(d) for c, d in df.dtypes.items()},
            "missing_values": int(df.isnull().sum().sum()),
        }
        
        # Store in database
        df.to_sql(
            name=settings.TABLE_NAME if hasattr(settings, 'TABLE_NAME') else "survey_responses",
            con=engine,
            if_exists="append",
            index=False
        )
        
        # Schedule background processing
        background_tasks.add_task(
            process_ingested_data.delay(df.to_dict(orient="records"))
        )
        
        return {"status": "uploaded", "data_summary": result}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.post("/upload_json/", status_code=202)
async def upload_json(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db)
):
    """Upload JSON data for batch ingestion."""
    try:
        contents = await file.read()
        data = json.loads(contents)
        df = pd.DataFrame(data)
        
        # Store in database
        df.to_sql(
            name="survey_responses",
            con=engine,
            if_exists="append",
            index=False
        )
        
        background_tasks.add_task(
            process_ingested_data.delay(df.to_dict(orient="records"))
        )
        
        return {"status": "uploaded", "data_summary": {"rows": len(df), "columns": list(df.columns)}}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.post("/sync_from_api/", status_code=202)
async def sync_from_api(
    source_url: str,
    parameters: Optional[Dict] = None,
    background_tasks: BackgroundTasks,
):
    """Synchronize data from external API endpoint."""
    async def _fetch_and_store():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(source_url, params=parameters or {}) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = pd.json_normalize(data)
                        
                        # Store in database
                        df.to_sql(
                            name="survey_responses",
                            con=engine,
                            if_exists="append",
                            index=False
                        )
                        
                        return {"status": "synced", "rows": len(df)}
                    else:
                        return {"status": "error", "message": f"API returned status {response.status}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
    
    background_tasks.add_task(asyncio.create_task, _fetch_and_store())
    return {"status": "sync_initiated", "source": source_url}


async def process_ingested_data(records: List[Dict]):
    """Background task to process newly ingested data."""
    import time
    time.sleep(2)  # Simulate processing delay
    
    # Here we would:
    # 1. Run integrity checks
    # 2. Apply anomaly detection models
    # 3. Flag any inconsistencies
    # 4. Store results in database
    
    pass