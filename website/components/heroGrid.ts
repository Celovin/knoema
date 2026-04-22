// Luvoire — deterministic grid replay (hero + playground)
// Ported from site-snapshot/hero.js

type Agent = {
  x: number;
  y: number;
  role: number;
  trail: { x: number; y: number }[];
};

type RunHeroGridOptions = {
  canvas: HTMLCanvasElement;
  gridW?: number;
  gridH?: number;
  nAgents?: number;
  seed?: number;
  durationMs?: number;
  totalTicks?: number;
  showTrails?: boolean;
  paddingRatio?: number;
  onTick?: (tick: number) => void;
  onFrame?: (t: number, tick: number) => void;
};

export type HeroGridHandle = {
  pause: () => void;
  resume: () => void;
  toggle: () => boolean;
  stop: () => void;
  isPaused: () => boolean;
  redraw: () => void;
};

function seededRand(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

function makeAgents(rand: () => number, n: number, gridW: number, gridH: number): Agent[] {
  const arr: Agent[] = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      x: Math.floor(rand() * gridW),
      y: Math.floor(rand() * gridH),
      role: rand() < 0.12 ? 2 : rand() < 0.45 ? 1 : 0,
      trail: [],
    });
  }
  return arr;
}

function stepAgents(rand: () => number, agents: Agent[], gridW: number, gridH: number) {
  for (const a of agents) {
    if (a.role === 0 && rand() < 0.08) a.role = 1;
    else if (a.role === 1 && rand() < 0.04) a.role = 2;
    else if (a.role === 2 && rand() < 0.12) a.role = 0;

    if (a.role !== 0) {
      a.trail.push({ x: a.x, y: a.y });
      if (a.trail.length > 5) a.trail.shift();
      const dir = Math.floor(rand() * 4);
      if (dir === 0 && a.x > 0) a.x--;
      else if (dir === 1 && a.x < gridW - 1) a.x++;
      else if (dir === 2 && a.y > 0) a.y--;
      else if (dir === 3 && a.y < gridH - 1) a.y++;
    }
  }
}

export function runHeroGrid(opts: RunHeroGridOptions): HeroGridHandle {
  const {
    canvas,
    gridW = 60,
    gridH = 60,
    nAgents = 420,
    seed = 42,
    durationMs = 8000,
    totalTicks = 100,
    showTrails = true,
    onTick = () => {},
    onFrame = () => {},
    paddingRatio = 0.03,
  } = opts;

  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not get 2D context");

  const dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
  }
  resize();
  window.addEventListener("resize", resize);

  let rand = seededRand(seed);
  let agents = makeAgents(rand, nAgents, gridW, gridH);

  let startTime: number | null = null;
  let paused = false;
  let rafId: number | null = null;
  let lastTick = -1;

  function colorFor(role: number) {
    if (role === 2) return "#A8753A";
    if (role === 1) return "#7A8F7B";
    return "#8A7F74";
  }

  function draw(_tick: number) {
    if (!ctx) return;
    const W = canvas.width;
    const H = canvas.height;
    const pad = Math.round(Math.min(W, H) * paddingRatio);
    const cw = (W - pad * 2) / gridW;
    const ch = (H - pad * 2) / gridH;

    ctx.fillStyle = "#FBF8F1";
    ctx.fillRect(0, 0, W, H);

    ctx.strokeStyle = "rgba(92, 81, 72, 0.10)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= gridW; i += 1) {
      const gx = Math.round(pad + i * cw) + 0.5;
      ctx.moveTo(gx, pad);
      ctx.lineTo(gx, H - pad);
    }
    for (let j = 0; j <= gridH; j += 1) {
      const gy = Math.round(pad + j * ch) + 0.5;
      ctx.moveTo(pad, gy);
      ctx.lineTo(W - pad, gy);
    }
    ctx.stroke();

    ctx.strokeStyle = "rgba(168, 117, 58, 0.22)";
    ctx.beginPath();
    for (let i = 0; i <= gridW; i += 10) {
      const gx = Math.round(pad + i * cw) + 0.5;
      ctx.moveTo(gx, pad);
      ctx.lineTo(gx, H - pad);
    }
    for (let j = 0; j <= gridH; j += 10) {
      const gy = Math.round(pad + j * ch) + 0.5;
      ctx.moveTo(pad, gy);
      ctx.lineTo(W - pad, gy);
    }
    ctx.stroke();

    if (showTrails) {
      for (const a of agents) {
        if (!a.trail.length) continue;
        for (let t = 0; t < a.trail.length; t++) {
          const p = a.trail[t];
          const fade = (t + 1) / (a.trail.length + 1);
          ctx.fillStyle = `rgba(201, 154, 99, ${0.12 * fade})`;
          const x = pad + p.x * cw;
          const y = pad + p.y * ch;
          ctx.fillRect(x + 1, y + 1, cw - 2, ch - 2);
        }
      }
    }

    for (const a of agents) {
      ctx.fillStyle = colorFor(a.role);
      const x = pad + a.x * cw;
      const y = pad + a.y * ch;
      const r = Math.max(1.2, Math.min(cw, ch) * 0.35);
      ctx.beginPath();
      ctx.arc(x + cw / 2, y + ch / 2, r, 0, Math.PI * 2);
      ctx.fill();
      if (a.role === 2) {
        ctx.strokeStyle = "rgba(168,117,58,0.4)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(x + cw / 2, y + ch / 2, r * 2.2, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }

  function frame(ts: number) {
    if (paused) {
      rafId = requestAnimationFrame(frame);
      return;
    }
    if (startTime === null) startTime = ts;
    const elapsed = ts - startTime;
    const t = (elapsed % durationMs) / durationMs;
    const tick = Math.floor(t * totalTicks);

    if (tick !== lastTick) {
      stepAgents(rand, agents, gridW, gridH);
      lastTick = tick;
      onTick(tick);
    }
    if (elapsed > durationMs) {
      startTime = ts;
      rand = seededRand(seed);
      agents = makeAgents(rand, nAgents, gridW, gridH);
      lastTick = -1;
    }

    draw(tick);
    onFrame(t, tick);
    rafId = requestAnimationFrame(frame);
  }

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduced) {
    rafId = requestAnimationFrame(frame);
  } else {
    draw(0);
  }

  return {
    pause() {
      paused = true;
    },
    resume() {
      paused = false;
    },
    toggle() {
      paused = !paused;
      return paused;
    },
    stop() {
      if (rafId !== null) cancelAnimationFrame(rafId);
    },
    isPaused() {
      return paused;
    },
    redraw: () => draw(0),
  };
}
