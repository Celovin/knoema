import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Game Demos | Luvoire",
  description:
    "Embedded Godot and Unity tavern demos for a replay-only Luvoire NPC interaction loop.",
  alternates: {
    canonical: "/game-demos",
  },
};

const repoRoot = path.join(process.cwd(), "..");
const godotDemoHtml = fs.readFileSync(
  path.join(repoRoot, "adapters", "godot", "samples", "tavern_demo", "web_build", "index.html"),
  "utf8",
);
const unityDemoHtml = fs.readFileSync(
  path.join(
    repoRoot,
    "adapters",
    "unity",
    "Samples~",
    "TavernDemo",
    "web_build",
    "index.html",
  ),
  "utf8",
);

const frameStyle = {
  width: "100%",
  minHeight: "760px",
  border: "1px solid var(--line)",
  borderRadius: "8px",
  background: "var(--panel)",
} as const;

export default function GameDemosPage() {
  return (
    <main className="subpage">
      <Link className="back-link" href="/showcase">
        Showcase
      </Link>
      <h1>Game Demo Mirrors</h1>
      <p>
        These embedded browser builds mirror the Godot and Unity tavern loops so a reviewer can
        walk up to Bjorn, type a line, and see the replay-only fallback path without a local engine
        install.
      </p>
      <div className="path-list">
        <article>
          <h2>Godot Tavern Demo</h2>
          <p>Top-down tavern loop with WASD movement, 64px proximity gating, and Bjorn fallback dialogue.</p>
          <iframe
            title="Godot Tavern Demo"
            srcDoc={godotDemoHtml}
            sandbox="allow-scripts"
            style={frameStyle}
          />
        </article>
        <article>
          <h2>Unity Tavern Demo</h2>
          <p>Equivalent Bjorn loop wired around the Unity `NPCAgent` sample contract.</p>
          <iframe
            title="Unity Tavern Demo"
            srcDoc={unityDemoHtml}
            sandbox="allow-scripts"
            style={frameStyle}
          />
        </article>
      </div>
    </main>
  );
}
