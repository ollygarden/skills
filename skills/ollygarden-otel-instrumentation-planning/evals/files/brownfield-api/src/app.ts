import express from "express";
import { Pool } from "pg";

const app = express();
const pool = new Pool();

app.get("/healthz", (_request, response) => response.send("ok"));

app.post("/checkout", async (request, response) => {
  const { email, orderId, cardToken } = request.body;
  const order = await pool.query("select * from orders where id = $1", [orderId]);

  try {
    await paymentClient.capture(orderId, cardToken);
  } catch (error) {
    console.error("capture failed", { email, orderId, request: request.body, error });
    await paymentClient.captureWithFallback(orderId, cardToken);
  }

  response.json({ order: order.rows[0] });
});

app.listen(3000);
