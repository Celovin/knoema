import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = dirname(dirname(root));
const demoDir = join(root, "demo");
const websiteWasmDir = join(repoRoot, "website", "public", "wasm");
const websiteDemoDir = join(websiteWasmDir, "demo");
const source = join(root, "src", "luvoire-core.ts");
const target = join(demoDir, "luvoire-core.js");
const pages = ["2-agent.html", "5-agent.html", "sally-anne.html"];

await mkdir(demoDir, { recursive: true });
await mkdir(websiteDemoDir, { recursive: true });
await copyFile(source, target);
await copyFile(join(root, "index.html"), join(websiteWasmDir, "index.html"));
for (const page of pages) {
  await copyFile(join(root, page), join(demoDir, page));
  await copyFile(join(root, page), join(websiteDemoDir, page));
}
await copyFile(target, join(websiteDemoDir, "luvoire-core.js"));

const payload = await readFile(target);
if (payload.byteLength > 500_000) {
  throw new Error(`WASM demo bundle exceeds 500KB: ${payload.byteLength}`);
}

await writeFile(
  join(demoDir, "manifest.json"),
  `${JSON.stringify(
    {
      name: "Luvoire Browser Runtime Demo",
      bundle: "luvoire-core.js",
      bundle_bytes: payload.byteLength,
      pages,
    },
    null,
    2,
  )}\n`,
  "utf-8",
);
await copyFile(join(demoDir, "manifest.json"), join(websiteWasmDir, "manifest.json"));

console.log(JSON.stringify({ bundle: target, bytes: payload.byteLength }, null, 2));
