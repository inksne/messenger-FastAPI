from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_read_main_page():
    response = client.get('/')
    assert response.status_code == 200


def test_read_about_us_page():
    response = client.get('/about_us')
    assert response.status_code == 200


def test_read_register_page():
    response = client.get('/register')
    assert response.status_code == 200


def test_read_login_page():
    response = client.get('/jwt/login')
    assert response.status_code == 200


def test_search_user():
    companion_name = "inksne"
    response = client.post(f"/authenticated/search/{companion_name}")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0