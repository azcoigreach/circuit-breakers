import uuid


def test_work_action_increases_balance(app_client, create_player):
    app_client.post("/v1/admin/world/reset")
    token = f"token-{uuid.uuid4()}"
    player = create_player(f"worker-{uuid.uuid4()}", token, balance=0)

    response = app_client.post(
        "/v1/actions",
        json={
            "actions": [
                {
                    "type": "work",
                    "actor_id": str(player.id),
                    "payload": {"reward": 250},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["accepted"]) == 1

    app_client.post("/v1/admin/tick/advance")

    balance_res = app_client.get(
        "/v1/currency/balance", headers={"Authorization": f"Bearer {token}"}
    )
    assert balance_res.status_code == 200
    assert balance_res.json()["balance_mamp"] == 250
