from fastapi.responses import StreamingResponse
from services.sse import event_generator, broadcast_event
from pydantic import BaseModel 
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["SSE"])

# Important: Put more specific routes first to avoid conflicts
@router.get("/ping")
async def sse_ping_endpoint():
    """
    SSE ping endpoint to keep the connection alive.
    """
    return {"status": "ping"}

@router.get("/{client_id}")
async def sse_endpoint(request: Request, client_id: str):
    logger.info(f"New SSE connection from client: {client_id}")
    return StreamingResponse(
        event_generator(request, client_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" 
        }
    )
    
# Broadcast an event to all connected clients    
class EventData(BaseModel):
    event: str
    data: dict
    
example_event = EventData(event="example-event", data={"key": "value"})
    
@router.post("/broadcast")
async def broadcast_event_endpoint(event_data: EventData):
    try:
        await broadcast_event(event_data)
        return JSONResponse(status_code=200, content={"message": "Event broadcasted successfully"})
    except Exception as e:
        logger.error(f"Error broadcasting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Error broadcasting event")