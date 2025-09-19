import uuid


def test_mint_and_decrypt_packet(app_client, create_player):
    app_client.post("/v1/admin/world/reset")
    token = f"packet-{uuid.uuid4()}"
    create_player(f"packet-{uuid.uuid4()}", token, balance=0)

    mint_res = app_client.post(
        "/v1/currency/mint_encrypted",
        json={
            "denom": "mAMP",
            "payload": {
                "type": "hash-chain",
                "difficulty": 2,
                "target_prefix": "00",
                "seed": "seed",
                "reward_mamp": 2000,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mint_res.status_code == 200
    packet_id = mint_res.json()["id"]

    decrypt_res = app_client.post(
        "/v1/currency/decrypt",
        json={"packet_id": packet_id, "solution": {"nonce": "293"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert decrypt_res.status_code == 200
    assert decrypt_res.json()["balance_mamp"] == 2000
