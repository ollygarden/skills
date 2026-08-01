import assert from "node:assert/strict";
import test from "node:test";
import { shouldTrace } from "../src/server.js";

test("ordinary routes are traced", () => {
  assert.equal(shouldTrace("/cart"), true);
});
