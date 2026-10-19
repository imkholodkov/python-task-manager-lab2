"""Практическая работа №3, шаг 4: тесты задач (обязательные 4–8)."""


# 4. Создание задачи: 201, done по умолчанию false, владелец сохранён.
async def test_create_task(client, user):
    response = await client.post("/tasks", json={"title": "Write tests", "owner_id": user["id"]})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write tests"
    assert body["done"] is False
    assert body["owner_id"] == user["id"]


# 5. Владельца с id 999 нет (таблицы пустые) — 404.
async def test_create_task_unknown_owner(client):
    response = await client.post("/tasks", json={"title": "Orphan", "owner_id": 999})
    assert response.status_code == 404


# 6. Фильтр done и пагинация limit/offset.
async def test_filter_done_and_pagination(client, user):
    # 5 задач: чётные (0, 2, 4) выполнены, нечётные — нет.
    for i in range(5):
        await client.post(
            "/tasks", json={"title": f"Task {i}", "done": i % 2 == 0, "owner_id": user["id"]}
        )

    # Фильтр done=true возвращает только выполненные задачи.
    done = (await client.get("/tasks", params={"done": True})).json()
    assert [t["title"] for t in done] == ["Task 0", "Task 2", "Task 4"]

    # limit=2, offset=1: пропустить первую задачу и взять две следующие.
    page = (await client.get("/tasks", params={"limit": 2, "offset": 1})).json()
    assert [t["title"] for t in page] == ["Task 1", "Task 2"]


# 7. PATCH меняет только переданные поля, остальные остаются прежними.
async def test_patch_changes_only_given_fields(client, user):
    created = (
        await client.post(
            "/tasks",
            json={"title": "Old", "description": "keep me", "owner_id": user["id"]},
        )
    ).json()

    # Передаём только done — title и description меняться не должны.
    response = await client.patch(f"/tasks/{created['id']}", json={"done": True})
    assert response.status_code == 200
    body = response.json()
    assert body["done"] is True
    assert body["title"] == "Old"
    assert body["description"] == "keep me"


# 8. После DELETE задача больше не находится: GET возвращает 404.
async def test_delete_then_get_404(client, user):
    created = (await client.post("/tasks", json={"title": "Bye", "owner_id": user["id"]})).json()
    assert (await client.delete(f"/tasks/{created['id']}")).status_code == 204
    assert (await client.get(f"/tasks/{created['id']}")).status_code == 404
