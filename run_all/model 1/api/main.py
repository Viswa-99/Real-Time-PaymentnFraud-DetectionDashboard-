import time
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Union, Dict, Any, Optional

from fastapi import (
    FastAPI,
    Request,
    Security,
    HTTPException,
    status,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Query,
)
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from . import config
from .schemas import (
    TransactionRequest,
    PredictionResponse,
    HealthResponse,
    ModelInfoResponse,
)
from .model_service import model_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("upi-ml-api")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Persistent In-Memory Blocked Alerts Store
class BlockedAlertsStore:
    def __init__(self, max_items: int = 5000):
        self.max_items = max_items
        self.blocked_alerts: List[Dict[str, Any]] = []

    def add_alert(self, alert_dict: Dict[str, Any]):
        # Add to beginning of list (newest first)
        self.blocked_alerts.insert(0, alert_dict)
        if len(self.blocked_alerts) > self.max_items:
            self.blocked_alerts.pop()

    def get_alerts(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        return self.blocked_alerts[offset : offset + limit]

    def count(self) -> int:
        return len(self.blocked_alerts)

    def clear(self):
        self.blocked_alerts.clear()


blocked_store = BlockedAlertsStore()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = asyncio.Lock()
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        
        payload = jsonable_encoder(message)
        stale = []
        for ws, lock in list(self.active_connections.items()):
            try:
                async with lock:
                    await ws.send_json(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting WS message: {e}")
                stale.append(ws)
        
        for s in stale:
            self.disconnect(s)

    async def broadcast_batch(self, messages: List[Dict[str, Any]]):
        if not self.active_connections or not messages:
            return

        batch_payload = jsonable_encoder({
            "type": "BATCH",
            "count": len(messages),
            "data": messages
        })

        stale = []
        for ws, lock in list(self.active_connections.items()):
            try:
                async with lock:
                    await ws.send_json(batch_payload)
            except Exception as e:
                logger.warning(f"Error broadcasting WS batch: {e}")
                stale.append(ws)
        
        for s in stale:
            self.disconnect(s)


ws_manager = ConnectionManager()


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if config.ML_API_KEY:
        if not api_key or api_key != config.ML_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header."
            )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML models
    logger.info("Initializing UPI Fraud Detection ML API...")
    try:
        model_service.load_models()
    except Exception as e:
        logger.error(f"Failed to load models during startup: {e}", exc_info=True)
    yield
    # Shutdown
    logger.info("Shutting down UPI Fraud Detection ML API...")


app = FastAPI(
    title="UPI Anomaly / Fraud Detection ML API",
    description="Production-style FastAPI service delivering real-time fraud probability and behavioral explanations using a 2-layer ML pipeline.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
origins = config.get_allowed_origins()
logger.info(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Invalid transaction payload."}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."}
    )


# WebSocket Endpoints for UI Live Streaming
@app.websocket("/ws")
@app.websocket("/ws/transactions")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to UPI Fraud ML Live Stream",
            "timestamp": datetime.now().isoformat()
        })
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# System Endpoints
@app.get("/", tags=["System"])
async def root():
    return {
        "status": "online",
        "service": "UPI Fraud Detection ML API",
        "version": "1.0.0",
        "docs": "http://localhost:5001/docs",
        "health": "http://localhost:5001/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded"
        )
    return HealthResponse(
        status="ok",
        service="upi-ml-api",
        layer1="loaded",
        layer2="loaded"
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["System"])
async def model_info():
    if not model_service.is_loaded or model_service.layer2_config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model info unavailable"
        )
    
    threshold = float(model_service.layer2_config.get("threshold", 0.86))
    device = str(model_service.layer2_config.get("device", "cuda"))
    feature_count = int(model_service.layer2_config.get("feature_count", 56))

    return ModelInfoResponse(
        model="Layer 1 Isolation Forest + Layer 2 XGBoost",
        feature_count=feature_count,
        threshold=threshold,
        device=device,
        status="ready"
    )


# Blocked Alerts Endpoints
@app.get("/alerts/blocked", tags=["Alerts"])
async def get_blocked_alerts(
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    """
    Retrieve all stored blocked alerts across the entire session.
    """
    alerts = blocked_store.get_alerts(limit=limit, offset=offset)
    return {
        "total_blocked": blocked_store.count(),
        "returned": len(alerts),
        "limit": limit,
        "offset": offset,
        "alerts": alerts,
    }


@app.post("/alerts/clear", tags=["Alerts"])
async def clear_blocked_alerts():
    """
    Clear stored blocked alerts.
    """
    blocked_store.clear()
    return {"status": "ok", "message": "Blocked alerts store cleared"}


# Core Inference & Simulator Ingestion Endpoints
@app.post("/predict", response_model=PredictionResponse, tags=["Inference"], dependencies=[Depends(verify_api_key)])
async def predict_transaction(req: TransactionRequest):
    start_time = time.perf_counter()
    try:
        response = model_service.predict(req)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"{ts_str} {req.transaction_id} risk={response.risk_score:.2f}% "
            f"decision={response.decision} latency={latency_ms:.1f}ms"
        )

        res_dict = response.model_dump()
        if response.decision == "ANOMALY" or response.risk_probability >= 0.86:
            blocked_store.add_alert(res_dict)

        # Broadcast enriched prediction over WebSocket to UI
        asyncio.create_task(ws_manager.broadcast(res_dict))
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for transaction {req.transaction_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction process failed."
        )


def _process_batch_items(items: list) -> list:
    results = []
    for item in items:
        try:
            if isinstance(item, TransactionRequest):
                req = item
            else:
                req = TransactionRequest.model_validate(item)
            
            res = model_service.predict(req)
            res_dict = res.model_dump()
            results.append(res_dict)

            if res.decision == "ANOMALY" or res.risk_probability >= 0.86:
                blocked_store.add_alert(res_dict)
        except Exception as e:
            logger.warning(f"Error processing transaction item in batch: {e}")
    return results


@app.post("/transactions", tags=["Ingest"])
@app.post("/transactions/batch", tags=["Ingest"])
async def ingest_transactions(payload: Union[TransactionRequest, List[TransactionRequest], Dict[str, Any]]):
    """
    Simulator Ingestion endpoint accepting raw transaction JSON or batch lists.
    Passes each transaction through ML Pipeline and streams predictions live via WebSockets.
    """
    if isinstance(payload, dict):
        if "transactions" in payload and isinstance(payload["transactions"], list):
            items = payload["transactions"]
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        items = [payload]

    results = await asyncio.to_thread(_process_batch_items, items)

    if results:
        asyncio.create_task(ws_manager.broadcast_batch(results))

    if len(results) == 1:
        return results[0]
    return {"status": "ok", "processed": len(results), "predictions": results}


@app.get("/demo/high-risk", response_model=PredictionResponse, tags=["Demo"], dependencies=[Depends(verify_api_key)])
async def demo_high_risk():
    res = model_service.get_demo_prediction(high_risk=True)
    res_dict = res.model_dump()
    blocked_store.add_alert(res_dict)
    asyncio.create_task(ws_manager.broadcast(res_dict))
    return res


@app.get("/demo/normal", response_model=PredictionResponse, tags=["Demo"], dependencies=[Depends(verify_api_key)])
async def demo_normal():
    res = model_service.get_demo_prediction(high_risk=False)
    asyncio.create_task(ws_manager.broadcast(res.model_dump()))
    return res
