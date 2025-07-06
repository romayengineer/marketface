import json
from pathlib import Path
from typing import Dict


def read_creds(path_str: str) -> Dict[str, str]:
    path = Path(path_str)
    if not path.exists():
        return {}
    with open(path.absolute(), "r") as f:
        return json.loads(f.read())