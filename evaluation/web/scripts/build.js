import { copyFile, mkdir, readdir, stat } from "node:fs/promises";

const publicDir = new URL("../public/", import.meta.url);
const distDir = new URL("../dist/", import.meta.url);

async function copyDir(fromUrl, toUrl) {
  await mkdir(toUrl, { recursive: true });
  const entries = await readdir(fromUrl, { withFileTypes: true });
  for (const entry of entries) {
    const from = new URL(entry.name, fromUrl);
    const to = new URL(entry.name, toUrl);
    if (entry.isDirectory()) {
      await copyDir(new URL(`${entry.name}/`, fromUrl), new URL(`${entry.name}/`, toUrl));
    } else {
      await copyFile(from, to);
    }
  }
}

await copyDir(publicDir, distDir);
const indexStats = await stat(new URL("index.html", distDir));
if (indexStats.size < 100) {
  throw new Error("evaluation web build produced an empty index");
}
console.log("built evaluation web scaffold");
