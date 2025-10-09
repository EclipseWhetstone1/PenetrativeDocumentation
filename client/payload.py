import uuid
from datetime import datetime

def assemble_payload(event, data=None):
    return {
        "machine_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "data": data if data else {}
    }
