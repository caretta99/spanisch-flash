from __future__ import annotations

from pathlib import Path

import pytest

from utils.dialog_vocab_generator import (
    DEFAULT_BASIC_STOPLIST,
    discover_dialogue_tex_files,
    dialogue_set_key_from_path,
    extract_vocabulario_items,
    normalize_spanish_term,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _dialogos_dir() -> Path:
    return _repo_root() / "ressources" / "dialogos"


def _vocabulary_json_path() -> Path:
    return _repo_root() / "data" / "vocabulary.json"


@pytest.fixture(scope="module")
def vocabulary_data():
    import json

    with _vocabulary_json_path().open("r", encoding="utf-8") as f:
        return json.load(f)


def test_every_dialogue_has_a_vocab_set(vocabulary_data):
    vocab_sets = vocabulary_data.get("vocab_sets", {})
    assert isinstance(vocab_sets, dict)

    dialogue_files = discover_dialogue_tex_files(_dialogos_dir())
    assert dialogue_files, "No dialogue .tex files discovered"

    missing = []
    for tex_path in dialogue_files:
        set_key = dialogue_set_key_from_path(tex_path)
        if set_key not in vocab_sets:
            missing.append(set_key)

    assert not missing, f"Missing vocab sets for: {missing}"


def test_no_dropped_vocabulario_items_except_stoplist(vocabulary_data):
    vocab_sets = vocabulary_data.get("vocab_sets", {})
    assert isinstance(vocab_sets, dict)

    basic_norm = {normalize_spanish_term(x) for x in DEFAULT_BASIC_STOPLIST}

    for tex_path in discover_dialogue_tex_files(_dialogos_dir()):
        set_key = dialogue_set_key_from_path(tex_path)
        entries = vocab_sets.get(set_key)
        assert isinstance(entries, list), f"{set_key} is not a list"

        tex = tex_path.read_text(encoding="utf-8")
        extracted = extract_vocabulario_items(tex)

        expected_terms = []
        seen = set()
        for item in extracted:
            norm = normalize_spanish_term(item.spanish)
            if not norm or norm in basic_norm:
                continue
            if norm in seen:
                continue
            seen.add(norm)
            expected_terms.append(norm)

        got_terms = [normalize_spanish_term(e.get("spanish", "")) for e in entries if isinstance(e, dict)]

        assert set(got_terms) == set(
            expected_terms
        ), f"{set_key}: mismatch between extracted vocabulario and JSON set"


def test_dialogue_vocab_entries_have_required_fields(vocabulary_data):
    vocab_sets = vocabulary_data.get("vocab_sets", {})
    assert isinstance(vocab_sets, dict)

    for tex_path in discover_dialogue_tex_files(_dialogos_dir()):
        set_key = dialogue_set_key_from_path(tex_path)
        entries = vocab_sets.get(set_key)
        assert isinstance(entries, list)
        assert len(entries) > 0, f"{set_key} has no entries (stoplist too aggressive?)"

        for entry in entries:
            assert isinstance(entry, dict)
            for k in ("spanish", "german", "english"):
                assert k in entry, f"{set_key}: entry missing {k}"
                assert isinstance(entry[k], str) and entry[k].strip(), f"{set_key}: empty {k}"


def test_todo_english_is_tracked(vocabulary_data):
    """
    Not a hard failure condition, but ensures we can see placeholder usage.
    """
    vocab_sets = vocabulary_data.get("vocab_sets", {})
    assert isinstance(vocab_sets, dict)

    todo_count = 0
    dialogue_set_count = 0
    for tex_path in discover_dialogue_tex_files(_dialogos_dir()):
        dialogue_set_count += 1
        set_key = dialogue_set_key_from_path(tex_path)
        entries = vocab_sets.get(set_key, [])
        for entry in entries:
            if isinstance(entry, dict) and entry.get("english") == "[TODO]":
                todo_count += 1

    assert dialogue_set_count > 0
    assert todo_count >= 0
