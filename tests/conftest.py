import pytest


@pytest.fixture()
def client(tmp_path):
    from app import app as flask_app

    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        SETTINGS_FILE_PATH=str(tmp_path / "quiz_settings.json"),
    )

    with flask_app.test_client() as client:
        yield client

