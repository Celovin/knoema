import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = join(root, "src", "extension.ts");
const targetDir = join(root, "compiled");
const target = join(targetDir, "extension.js");

await mkdir(targetDir, { recursive: true });
await copyFile(source, target);

const payload = await readFile(target, "utf-8");
if (!payload.includes("activate") || !payload.includes("validateScenarioText")) {
  throw new Error("compiled extension is missing required exports");
}
await writeFile(join(targetDir, "manifest.json"), `${JSON.stringify({ main: "extension.js" })}\n`);
console.log(JSON.stringify({ compiled: target }, null, 2));
