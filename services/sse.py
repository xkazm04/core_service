import asyncio
from typing import Dict
import json
from fastapi import Request
from pydantic import BaseModel

class EventData(BaseModel):
    event: str
    data: dict

CONNECTIONS: Dict[str, asyncio.Queue] = {}

async def add_client(client_id: str) -> asyncio.Queue:
    queue = asyncio.Queue()
    CONNECTIONS[client_id] = queue
    return queue

def remove_client(client_id: str):
    if client_id in CONNECTIONS:
        del CONNECTIONS[client_id]
        
def format_sse_event(data: dict, event: str = None) -> str:
    message = f"data: {json.dumps(data)}\n"
    if event is not None:
        message = f"event: {event}\n{message}"
    message += "\n"
    return message

async def event_generator(request: Request, client_id: str):
    queue = await add_client(client_id)
    try:
        yield format_sse_event({"message": "Connection established"}, event="connected")
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield format_sse_event(data["data"], event=data["event"])
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
    finally:
        remove_client(client_id)

async def broadcast_event(event_data=None, event: str = None, data: dict = None):
    """Broadcast an event to all connected clients."""
    if event_data:
        # Handle when passed an EventData object
        event = event_data.event
        data = event_data.data
    
    # Ensure we have valid event and data
    if not event or not data:
        raise ValueError("Either event_data or both event and data must be provided")
        
    for client_id, queue in CONNECTIONS.items():
        await queue.put({
            "event": event,
            "data": data
        })

async def background_task():
    count = 0
    while True:
        count += 1
        if CONNECTIONS:
            for client_id, queue in CONNECTIONS.items():
                await queue.put({
                    "event": "background-update",
                    "data": {"count": count, "message": "Automatic update"}
                })
        await asyncio.sleep(10)