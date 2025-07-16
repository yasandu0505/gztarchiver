import json
from typing import List, Dict

def load_doc_metadata_file(json_path: str) -> List[Dict[str, str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_doc_metadata(kind):
    return