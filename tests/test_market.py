import uuid


def test_market_buy_flow(app_client, create_player):
    app_client.post("/v1/admin/world/reset")
    seller_token = f"seller-{uuid.uuid4()}"
    buyer_token = f"buyer-{uuid.uuid4()}"
    create_player(f"seller-{uuid.uuid4()}", seller_token, balance=0)
    create_player(f"buyer-{uuid.uuid4()}", buyer_token, balance=10_000)

    listing_res = app_client.post(
        "/v1/market/listings",
        json={"item_type": "raw-data", "price_amp": 1_500, "item_attrs": {}},
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert listing_res.status_code == 200
    listing_id = listing_res.json()["id"]

    buy_res = app_client.post(
        f"/v1/market/listings/{listing_id}/buy",
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert buy_res.status_code == 200
    assert buy_res.json()["status"] == "filled"

    seller_balance = app_client.get(
        "/v1/currency/balance", headers={"Authorization": f"Bearer {seller_token}"}
    )
    buyer_balance = app_client.get(
        "/v1/currency/balance", headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert seller_balance.json()["balance_mamp"] == 1_500
    assert buyer_balance.json()["balance_mamp"] == 8_500
