import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
const js = await readFile(new URL("../public/main.js", import.meta.url), "utf8");

if (!html.includes("Pairwise Preference")) {
  throw new Error("missing pairwise preference UI");
}
if (!js.includes("localStorage")) {
  throw new Error("missing local rating persistence");
}
console.log("evaluation web smoke passed");
