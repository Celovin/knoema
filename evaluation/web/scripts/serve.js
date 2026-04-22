import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";

const port = Number(process.env.PORT || 4175);
const root = new URL("../public/", import.meta.url).pathname;
const contentTypes = {
  ".css": "text/css",
  ".html": "text/html",
  ".js": "text/javascript",
};

const server = createServer(async (request, response) => {
  const pathname = request.url === "/" ? "/index.html" : request.url || "/index.html";
  const target = join(root, pathname.replace(/^\/+/, ""));
  try {
    const body = await readFile(target);
    response.writeHead(200, {
      "content-type": contentTypes[extname(target)] || "application/octet-stream",
    });
    response.end(body);
  } catch {
    response.writeHead(404, { "content-type": "text/plain" });
    response.end("not found");
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Luvoire evaluation web listening on http://127.0.0.1:${port}`);
});
