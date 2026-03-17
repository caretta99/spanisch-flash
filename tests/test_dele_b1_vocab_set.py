from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _vocabulary_json_path() -> Path:
    return _repo_root() / "data" / "vocabulary.json"


def test_dele_b1_vocab_set_exists_and_is_well_formed():
    data = json.loads(_vocabulary_json_path().read_text(encoding="utf-8"))
    vocab_sets = data.get("vocab_sets", {})
    assert isinstance(vocab_sets, dict)

    entries = vocab_sets.get("dele_b1_info")
    assert isinstance(entries, list)
    assert len(entries) >= 10

    seen = set()
    for entry in entries:
        assert isinstance(entry, dict)
        for k in ("spanish", "german", "english"):
            assert k in entry
            assert isinstance(entry[k], str) and entry[k].strip()
            assert entry[k] != "[TODO]"

        norm = " ".join(entry["spanish"].strip().lower().split())
        assert norm not in seen, f"duplicate spanish term in dele_b1_info: {entry['spanish']!r}"
        seen.add(norm)

