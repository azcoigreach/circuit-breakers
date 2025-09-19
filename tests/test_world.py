def test_world_state_advances(app_client):
    app_client.post("/v1/admin/world/reset")
    res = app_client.get("/v1/world/")
    assert res.status_code == 200
    payload = res.json()
    tick = payload["tick"]

    advance = app_client.post("/v1/admin/tick/advance")
    assert advance.status_code == 200
    next_state = app_client.get("/v1/world/")
    assert next_state.json()["tick"] == tick + 1
