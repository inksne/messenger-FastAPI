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


def test_login():
    username = "inksne"
    password = "ink"
    response = client.post(
        "/jwt/login/",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200

    cookies = response.cookies
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    assert access_token is not None
    assert refresh_token is not None

    assert len(access_token) > 0
    assert len(refresh_token) > 0