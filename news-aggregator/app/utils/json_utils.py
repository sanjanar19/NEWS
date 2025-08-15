from datetime import datetime
from typing import Any
from fastapi.encoders import jsonable_encoder

def custom_json_encoder(obj: Any) -> Any:
    """Custom JSON encoder that handles datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return jsonable_encoder(obj)