import assert from "node:assert/strict";
import { createReadStream } from "node:fs";
import { createServer } from "node:http";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import playwright from "../../../website/node_modules/playwright/index.js";

const { chromium } = playwright;
const demoDir = fileURLToPath(new URL("../demo", import.meta.url));
const contentTypes = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
]);
const server = createServer((request, response) => {
  const path = request.url === "/" ? "/2-agent.html" : request.url || "/2-agent.html";
  const filePath = join(demoDir, path.replace(/^\/+/, ""));
  response.setHeader("Content-Type", contentTypes.get(extname(filePath)) || "text/plain");
  createReadStream(filePath)
    .on("error", () => {
      response.statusCode = 404;
      response.end("not found");
    })
    .pipe(response);
});
await new Promise((resolve) => {
  server.listen(0, "127.0.0.1", resolve);
});
const address = server.address();
assert.equal(typeof address, "object");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto(`http://127.0.0.1:${address.port}/2-agent.html`);
await page.getByRole("button", { name: "Run 100 ticks" }).click();
await page.waitForFunction(() => document.querySelector("#result")?.textContent?.includes('"actions": 200'));
const text = await page.locator("#result").textContent();
assert.ok(text.includes('"agents": 2'));
assert.ok(text.includes('"actions": 200'));
await browser.close();
await new Promise((resolve) => {
  server.close(resolve);
});
