"""Практическая работа №3, шаг 4: тесты пользователей (обязательные 1–3)."""


async def test_create_user(client):
    response = await client.post("/users", json={"email": "a@example.com", "name": "Alice"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert body["name"] == "Alice"
    assert isinstance(body["id"], int)


async def test_duplicate_email(client):
    payload = {"email": "dup@example.com", "name": "Bob"}
    assert (await client.post("/users", json=payload)).status_code == 201
    response = await client.post("/users", json=payload)
    assert response.status_code == 409


async def test_invalid_email(client):
    response = await client.post("/users", json={"email": "not-an-email", "name": "Eve"})
    assert response.status_code == 422
