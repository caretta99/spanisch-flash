import json
import re


def _read_settings_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_writes_file_on_conjugations_save_settings(client):
    from app import app as flask_app

    settings_path = flask_app.config["SETTINGS_FILE_PATH"]

    res = client.post(
        "/quiz/conjugations/save-settings",
        data={
            "verbs": ["traer", "hacer"],
            "tenses": ["presente"],
            "seconds_per_question": "9",
            "seconds_per_answer": "2",
            "num_questions": "11",
            "contestants": ["A", " ", "B"],
        },
        follow_redirects=False,
    )
    assert res.status_code in (302, 303)

    persisted = _read_settings_file(settings_path)
    assert "conjugations" in persisted
    conj = persisted["conjugations"]
    assert conj["selected_verbs"] == ["traer", "hacer"]
    assert conj["selected_tenses"] == ["presente"]
    assert conj["seconds_per_question"] == 9
    assert conj["seconds_per_answer"] == 2
    assert conj["num_questions"] == 11
    assert conj["contestants"] == ["A", "B"]


def test_restores_after_session_cleared_conjugations_options(client):
    from app import app as flask_app

    settings_path = flask_app.config["SETTINGS_FILE_PATH"]

    client.post(
        "/quiz/conjugations/save-settings",
        data={
            "verbs": ["traer"],
            "tenses": ["presente"],
            "seconds_per_question": "8",
            "seconds_per_answer": "3",
            "num_questions": "12",
            "contestants": ["Ana", "Ben"],
        },
    )

    with client.session_transaction() as sess:
        sess.clear()

    html = client.get("/quiz/conjugations/options").get_data(as_text=True)

    # Selected checkbox should be checked (allow arbitrary attribute order/whitespace)
    assert re.search(r'<input[^>]*name="verbs"[^>]*value="traer"[^>]*checked', html) is not None
    assert re.search(r'<input[^>]*name="tenses"[^>]*value="presente"[^>]*checked', html) is not None

    # Numeric inputs restored
    assert re.search(r'<input[^>]*id="seconds_per_question"[^>]*value="8"', html) is not None
    assert re.search(r'<input[^>]*id="seconds_per_answer"[^>]*value="3"', html) is not None
    assert re.search(r'<input[^>]*id="num_questions"[^>]*value="12"', html) is not None

    # Contestants restored
    assert re.search(r'<input[^>]*name="contestants"[^>]*value="Ana"', html) is not None
    assert re.search(r'<input[^>]*name="contestants"[^>]*value="Ben"', html) is not None

    # Sanity: file exists
    persisted = _read_settings_file(settings_path)
    assert persisted["conjugations"]["selected_verbs"] == ["traer"]


def test_corrupt_file_is_ignored_and_quarantined(client, tmp_path):
    from app import app as flask_app

    settings_path = flask_app.config["SETTINGS_FILE_PATH"]

    # Create corrupt JSON
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write("{ this is not valid json")

    res = client.get("/quiz/conjugations/options")
    assert res.status_code == 200

    # Corrupt file should have been moved or removed
    assert not (tmp_path / "quiz_settings.json").exists()
    corrupt_files = list(tmp_path.glob("quiz_settings.json.*.corrupt"))
    assert len(corrupt_files) >= 1
