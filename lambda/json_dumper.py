import json
from datetime import datetime
from typing import Any, Dict, Optional


def json_decode(
    o: Any
) -> Optional[str]:  # pylint: disable=inconsistent-return-statements
    if isinstance(o, datetime):
        return o.isoformat()
    return None


def dumps(js: Dict[str, Any]) -> str:
    return json.dumps(js, sort_keys=True, default=json_decode)
