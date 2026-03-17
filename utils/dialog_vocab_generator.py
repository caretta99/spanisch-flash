from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VocabItem:
    spanish: str
    german: str


_DIALOGUE_TEX_RE = re.compile(r"^(?P<num>\d{2})_(?P<slug>.+)\.tex$")
_VOCAB_ITEM_RE = re.compile(r"\\item\s+\\textbf\{(?P<spanish>[^}]+)\}\s+-\s+(?P<german>.+?)\s*$")


def discover_dialogue_tex_files(dialogos_dir: Path) -> list[Path]:
    """
    Returns dialogue source files like '01_foo.tex', sorted by filename.
    Ignores templates, logs, aux files, etc.
    """
    if not dialogos_dir.exists():
        return []
    paths: list[Path] = []
    for entry in dialogos_dir.iterdir():
        if not entry.is_file():
            continue
        m = _DIALOGUE_TEX_RE.match(entry.name)
        if not m:
            continue
        paths.append(entry)
    return sorted(paths, key=lambda p: p.name)


def dialogue_set_key_from_path(path: Path) -> str:
    m = _DIALOGUE_TEX_RE.match(path.name)
    if not m:
        raise ValueError(f"Not a dialogue tex filename: {path.name}")
    return f"dialog_{m.group('num')}_{m.group('slug')}"


def dialogue_display_name_from_path(path: Path) -> str:
    """
    Human-friendly fallback display name (app.py can override further).
    """
    m = _DIALOGUE_TEX_RE.match(path.name)
    if not m:
        raise ValueError(f"Not a dialogue tex filename: {path.name}")
    num = m.group("num")
    slug = m.group("slug").replace("_", " ").strip()
    return f"Dialog {num} — {slug.title()}"


def normalize_spanish_term(term: str) -> str:
    # Lowercase, collapse internal whitespace, strip surrounding punctuation/spaces.
    t = term.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" \t\r\n.,;:¡!¿?()[]\"'")
    return t


def extract_vocabulario_items(tex_content: str) -> list[VocabItem]:
    """
    Extract vocab items from the '\\section*{Vocabulario}' block.
    Only considers '\\item \\textbf{SPANISH} - GERMAN' entries.
    """
    start_idx = tex_content.find(r"\section*{Vocabulario}")
    if start_idx < 0:
        return []

    rest = tex_content[start_idx:]
    # Find end at next \section*{...} after Vocabulario, or \end{document}
    end_candidates: list[int] = []
    next_section = rest.find(r"\section*{", len(r"\section*{Vocabulario}"))
    if next_section >= 0:
        end_candidates.append(next_section)
    end_doc = rest.find(r"\end{document}")
    if end_doc >= 0:
        end_candidates.append(end_doc)
    end_idx = min(end_candidates) if end_candidates else len(rest)
    block = rest[:end_idx]

    items: list[VocabItem] = []
    for line in block.splitlines():
        m = _VOCAB_ITEM_RE.search(line)
        if not m:
            continue
        spanish = m.group("spanish").strip()
        german = m.group("german").strip()
        if spanish and german:
            items.append(VocabItem(spanish=spanish, german=german))
    return items


def load_vocabulary_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_existing_vocab_index(vocabulary_data: dict) -> dict[str, dict]:
    """
    Returns dict keyed by normalized Spanish term -> best entry dict.
    If a Spanish term appears multiple times across sets, first one wins.
    """
    idx: dict[str, dict] = {}
    vocab_sets = vocabulary_data.get("vocab_sets", {})
    if not isinstance(vocab_sets, dict):
        return idx

    for _set_key, entries in vocab_sets.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            spanish = entry.get("spanish")
            if not isinstance(spanish, str) or not spanish.strip():
                continue
            k = normalize_spanish_term(spanish)
            if k and k not in idx:
                idx[k] = entry
    return idx


DEFAULT_BASIC_STOPLIST = {
    # Pronouns / persons
    "yo",
    "tú",
    "tu",
    "él",
    "el",
    "ella",
    "usted",
    "nosotros",
    "nosotras",
    "vosotros",
    "vosotras",
    "ustedes",
    "ellos",
    "ellas",
    # Ultra-basic verbs (requested examples)
    "ser",
    "estar",
    "tener",
    "ir",
    "hacer",
    "llamar",
    "llamarse",
}


def generate_dialogue_vocab_sets(
    dialogos_dir: Path,
    vocabulary_json_path: Path,
    *,
    english_todo_placeholder: str = "[TODO]",
    basic_stoplist: Iterable[str] = DEFAULT_BASIC_STOPLIST,
) -> dict[str, list[dict]]:
    basic_norm = {normalize_spanish_term(x) for x in basic_stoplist}

    vocabulary_data = load_vocabulary_json(vocabulary_json_path)
    existing_idx = build_existing_vocab_index(vocabulary_data)

    result: dict[str, list[dict]] = {}
    for tex_path in discover_dialogue_tex_files(dialogos_dir):
        set_key = dialogue_set_key_from_path(tex_path)
        tex_content = tex_path.read_text(encoding="utf-8")
        vocab_items = extract_vocabulario_items(tex_content)

        seen: set[str] = set()
        entries: list[dict] = []
        for item in vocab_items:
            norm = normalize_spanish_term(item.spanish)
            if not norm or norm in basic_norm:
                continue
            if norm in seen:
                continue
            seen.add(norm)

            existing = existing_idx.get(norm)
            english = None
            if isinstance(existing, dict):
                eng = existing.get("english")
                if isinstance(eng, str) and eng.strip():
                    english = eng.strip()

            entries.append(
                {
                    "spanish": item.spanish.strip(),
                    "german": item.german.strip(),
                    "english": english or english_todo_placeholder,
                }
            )

        result[set_key] = entries

    return result


def merge_dialogue_sets_into_vocabulary_json(
    vocabulary_data: dict, dialogue_sets: dict[str, list[dict]]
) -> dict:
    vocab_sets = vocabulary_data.get("vocab_sets")
    if not isinstance(vocab_sets, dict):
        vocab_sets = {}
        vocabulary_data["vocab_sets"] = vocab_sets

    for set_key, entries in dialogue_sets.items():
        vocab_sets[set_key] = entries

    return vocabulary_data


def write_vocabulary_json(path: Path, vocabulary_data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(vocabulary_data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dialogos_dir = repo_root / "ressources" / "dialogos"
    vocab_path = repo_root / "data" / "vocabulary.json"

    dialogue_sets = generate_dialogue_vocab_sets(dialogos_dir, vocab_path)
    vocab_data = load_vocabulary_json(vocab_path)
    merged = merge_dialogue_sets_into_vocabulary_json(vocab_data, dialogue_sets)
    write_vocabulary_json(vocab_path, merged)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
