import os
import json
import uuid
import time
from typing import Any

def write_service_event(topic: str, book_id: str, service: str, storage_root: str = "storage", **extra: Any) -> str:
    """
    Write a service event as a JSON file in the format compatible with shared-core-npm.
    """
    event = {
        "guid": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "topic": topic,
        "bookId": book_id,
        "service": service,
        **extra
    }
    events_dir = os.path.join(storage_root, "events")
    os.makedirs(events_dir, exist_ok=True)
    filename = f"{event['timestamp']}_{topic}_{book_id}_{event['guid']}.json"
    filepath = os.path.join(events_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    return filepath

# Example usage:
# write_service_event("service-start", "book123", "composingservice")
# write_service_event("service-stop", "book123", "composingservice", result="success") 