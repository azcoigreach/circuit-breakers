import uuid


def test_event_stream_http(app_client, create_player):
    app_client.post("/v1/admin/world/reset")
    token = f"stream-{uuid.uuid4()}"
    actor = create_player(f"streamer-{uuid.uuid4()}", token, balance=0)

    app_client.post(
        "/v1/actions",
        json={
            "actions": [
                {
                    "type": "work",
                    "actor_id": str(actor.id),
                    "payload": {"reward": 10},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    app_client.post("/v1/admin/tick/advance")

    events_res = app_client.get("/v1/events", params={"since_tick": 0})
    assert events_res.status_code == 200
    events = events_res.json()
    assert any(event["kind"] == "tick.advance" for event in events)
