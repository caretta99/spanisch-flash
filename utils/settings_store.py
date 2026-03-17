import json
import os
import time
from typing import Any, Dict, Optional
from uuid import uuid4


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _sanitize_section(section: Any, *, allowed_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Keep only known keys with expected primitive shapes.

    allowed_keys maps key -> expected_type where expected_type is one of:
    - "str_list"
    - "int"
    - "str"
    """
    if not isinstance(section, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    for key, expected in allowed_keys.items():
        if key not in section:
            continue
        val = section.get(key)
        if expected == "str_list" and _is_str_list(val):
            sanitized[key] = val
        elif expected == "int" and isinstance(val, int):
            sanitized[key] = val
        elif expected == "str" and isinstance(val, str):
            sanitized[key] = val
    return sanitized


def validate_settings(settings: Any) -> Dict[str, Any]:
    """
    Validate + sanitize the persisted settings structure.

    Returns a dict with up to these top-level keys: conjugations, porpara, vocab.
    Unknown keys are dropped.
    """
    if not isinstance(settings, dict):
        return {}

    conjugations_keys = {
        "selected_verbs": "str_list",
        "selected_tenses": "str_list",
        "seconds_per_question": "int",
        "seconds_per_answer": "int",
        "num_questions": "int",
        "contestants": "str_list",
    }
    porpara_keys = {
        "selected_por_categories": "str_list",
        "selected_para_categories": "str_list",
        "seconds_per_question": "int",
        "seconds_per_answer": "int",
        "num_questions": "int",
        "contestants": "str_list",
    }
    vocab_keys = {
        "selected_vocab_sets": "str_list",
        "direction": "str",
        "seconds_per_question": "int",
        "seconds_per_answer": "int",
        "num_questions": "int",
        "contestants": "str_list",
    }

    out: Dict[str, Any] = {}
    out["conjugations"] = _sanitize_section(settings.get("conjugations"), allowed_keys=conjugations_keys)
    out["porpara"] = _sanitize_section(settings.get("porpara"), allowed_keys=porpara_keys)
    out["vocab"] = _sanitize_section(settings.get("vocab"), allowed_keys=vocab_keys)
    return out


def _quarantine_corrupt_file(path: str) -> None:
    directory = os.path.dirname(path) or "."
    base = os.path.basename(path)
    ts = time.strftime("%Y%m%d-%H%M%S")
    quarantine = os.path.join(directory, f"{base}.{ts}.corrupt")
    try:
        os.replace(path, quarantine)
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass


def load_settings(path: str) -> Optional[Dict[str, Any]]:
    """
    Load settings from JSON file.

    Returns:
    - dict (sanitized) if load succeeded and structure is valid-ish
    - None if file missing or corrupted (corrupted file is quarantined/removed)
    """
    if not path:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        _quarantine_corrupt_file(path)
        return None

    if not isinstance(raw, dict):
        _quarantine_corrupt_file(path)
        return None

    sanitized = validate_settings(raw)
    return sanitized


def save_settings(path: str, settings: Dict[str, Any]) -> None:
    """
    Atomically persist settings to JSON.

    - Writes to a temp file in the same directory and uses os.replace
    - Attempts to fsync the file to reduce partial-write risk
    """
    if not path:
        return

    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    sanitized = validate_settings(settings)

    tmp_path = os.path.join(directory, f".{os.path.basename(path)}.{uuid4().hex}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        try:
            f.flush()
            os.fsync(f.fileno())
        except OSError:
            pass

    os.replace(tmp_path, path)
