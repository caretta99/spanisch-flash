import re


def test_conjugations_question_card_layout(client):
    with client.session_transaction() as sess:
        sess["questions"] = [
            {
                "verb": "traer",
                "tense": "presente",
                "person": "yo",
                "answer": "traigo",
            }
        ]
        sess["current_question"] = 0
        sess["seconds_per_question"] = 3
        sess["seconds_per_answer"] = 4
        sess["contest_mode"] = False

    res = client.get("/quiz/conjugations/run")
    assert res.status_code == 200

    html = res.get_data(as_text=True)

    # Line 1: person + verb with exact connector
    assert 'class="conj-line1"' in html
    assert "yo" in html
    assert "traer" in html
    assert " + " in html

    # Line 2: tense rendered separately
    assert 'class="conj-line2"' in html
    assert "presente" in html

    # Ensure the old layout isn't present anymore
    assert "tense-person" not in html
    assert "verb-infinitive" not in html


def test_conjugations_plus_is_not_bullet_separator(client):
    with client.session_transaction() as sess:
        sess["questions"] = [
            {
                "verb": "traer",
                "tense": "presente",
                "person": "yo",
                "answer": "traigo",
            }
        ]
        sess["current_question"] = 0
        sess["seconds_per_question"] = 3
        sess["seconds_per_answer"] = 4
        sess["contest_mode"] = False

    html = client.get("/quiz/conjugations/run").get_data(as_text=True)

    # There should be no bullet separator in the question card markup.
    assert "•" not in html
    # Sanity: plus exists as its own span with spaces inside.
    assert re.search(r'class="plus"> \+ </span>', html) is not None

