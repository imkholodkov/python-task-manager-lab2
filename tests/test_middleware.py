"""Практическая работа №3, шаг 4: заголовок X-Process-Time (обязательный 9)."""


async def test_process_time_header(client):
    response = await client.get("/tasks")
    assert response.status_code == 200
    assert float(response.headers["X-Process-Time"]) >= 0
