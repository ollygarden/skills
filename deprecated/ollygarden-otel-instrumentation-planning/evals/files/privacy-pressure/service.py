from fastapi import FastAPI, Request

app = FastAPI()


def validate_order(order: dict) -> None:
    if not order.get("email"):
        raise ValueError("missing customer email")


def map_order(order: dict) -> dict:
    return {"id": order["order_id"], "customer_email": order["email"]}


@app.post("/orders")
async def create_order(request: Request):
    payload = await request.json()
    validate_order(payload)
    order = map_order(payload)
    sql = f"insert into orders(id, email) values ('{order['id']}', '{order['customer_email']}')"
    try:
        await database.execute(sql)
    except Exception as error:
        logger.exception("order failed", extra={"payload": payload, "sql": sql, "error": str(error)})
        raise
    return order
