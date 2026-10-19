"""Практическая работа №3, шаг 4: тесты задач (обязательные 4–8)."""


async def test_create_task(client, user):
    response = await client.post("/tasks", json={"title": "Write tests", "owner_id": user["id"]})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write tests"
    assert body["done"] is False
    assert body["owner_id"] == user["id"]


async def test_create_task_unknown_owner(client):
    response = await client.post("/tasks", json={"title": "Orphan", "owner_id": 999})
    assert response.status_code == 404


async def test_filter_done_and_pagination(client, user):
    for i in range(5):
        await client.post(
            "/tasks", json={"title": f"Task {i}", "done": i % 2 == 0, "owner_id": user["id"]}
        )

    done = (await client.get("/tasks", params={"done": True})).json()
    assert [t["title"] for t in done] == ["Task 0", "Task 2", "Task 4"]

    page = (await client.get("/tasks", params={"limit": 2, "offset": 1})).json()
    assert [t["title"] for t in page] == ["Task 1", "Task 2"]


async def test_patch_changes_only_given_fields(client, user):
    created = (
        await client.post(
            "/tasks",
            json={"title": "Old", "description": "keep me", "owner_id": user["id"]},
        )
    ).json()

    response = await client.patch(f"/tasks/{created['id']}", json={"done": True})
    assert response.status_code == 200
    body = response.json()
    assert body["done"] is True
    assert body["title"] == "Old"
    assert body["description"] == "keep me"


async def test_delete_then_get_404(client, user):
    created = (await client.post("/tasks", json={"title": "Bye", "owner_id": user["id"]})).json()
    assert (await client.delete(f"/tasks/{created['id']}")).status_code == 204
    assert (await client.get(f"/tasks/{created['id']}")).status_code == 404
