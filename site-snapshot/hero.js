// Luvoire — deterministic grid replay (hero + playground)

function seededRand(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xFFFFFFFF;
  };
}

function makeAgents(rand, n, gridW, gridH) {
  const arr = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      x: Math.floor(rand() * gridW),
      y: Math.floor(rand() * gridH),
      role: rand() < 0.12 ? 2 : (rand() < 0.45 ? 1 : 0), // 2=active, 1=moving, 0=idle
      trail: [],
    });
  }
  return arr;
}

function stepAgents(rand, agents, gridW, gridH) {
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

function runHeroGrid(opts) {
  const {
    canvas,
    gridW = 60, gridH = 60,
    nAgents = 420,
    seed = 42,
    durationMs = 8000,
    totalTicks = 100,
    showTrails = true,
    onTick = () => {},
    onFrame = () => {},
    paddingRatio = 0.03,
  } = opts;

  const ctx = canvas.getContext('2d');
  const dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
  }
  resize();
  window.addEventListener('resize', resize);

  // Seeded state
  let rand = seededRand(seed);
  let agents = makeAgents(rand, nAgents, gridW, gridH);

  let startTime = null;
  let paused = false;
  let pausedAt = 0;
  let rafId = null;

  function colorFor(role) {
    if (role === 2) return '#A8753A';
    if (role === 1) return '#7A8F7B';
    return '#8A7F74';
  }

  function draw(tick) {
    const W = canvas.width, H = canvas.height;
    const pad = Math.round(Math.min(W, H) * paddingRatio);
    const cw = (W - pad * 2) / gridW;
    const ch = (H - pad * 2) / gridH;

    // bg
    ctx.fillStyle = '#FBF8F1';
    ctx.fillRect(0, 0, W, H);

    // grid lines
    ctx.strokeStyle = 'rgba(92, 81, 72, 0.10)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= gridW; i += 1) {
      const gx = Math.round(pad + i * cw) + 0.5;
      ctx.moveTo(gx, pad); ctx.lineTo(gx, H - pad);
    }
    for (let j = 0; j <= gridH; j += 1) {
      const gy = Math.round(pad + j * ch) + 0.5;
      ctx.moveTo(pad, gy); ctx.lineTo(W - pad, gy);
    }
    ctx.stroke();

    // heavier cross lines every 10
    ctx.strokeStyle = 'rgba(168, 117, 58, 0.22)';
    ctx.beginPath();
    for (let i = 0; i <= gridW; i += 10) {
      const gx = Math.round(pad + i * cw) + 0.5;
      ctx.moveTo(gx, pad); ctx.lineTo(gx, H - pad);
    }
    for (let j = 0; j <= gridH; j += 10) {
      const gy = Math.round(pad + j * ch) + 0.5;
      ctx.moveTo(pad, gy); ctx.lineTo(W - pad, gy);
    }
    ctx.stroke();

    // trails
    if (showTrails) {
      for (const a of agents) {
        if (!a.trail.length) continue;
        for (let t = 0; t < a.trail.length; t++) {
          const p = a.trail[t];
          const fade = (t + 1) / (a.trail.length + 1);
          ctx.fillStyle = `rgba(201, 154, 99, ${0.12 * fade})`;
          const x = pad + p.x * cw, y = pad + p.y * ch;
          ctx.fillRect(x + 1, y + 1, cw - 2, ch - 2);
        }
      }
    }

    // agents
    for (const a of agents) {
      ctx.fillStyle = colorFor(a.role);
      const x = pad + a.x * cw, y = pad + a.y * ch;
      const r = Math.max(1.2, Math.min(cw, ch) * 0.35);
      ctx.beginPath();
      ctx.arc(x + cw/2, y + ch/2, r, 0, Math.PI * 2);
      ctx.fill();
      if (a.role === 2) {
        ctx.strokeStyle = 'rgba(168,117,58,0.4)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(x + cw/2, y + ch/2, r * 2.2, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }

  function frame(ts) {
    if (paused) { rafId = requestAnimationFrame(frame); return; }
    if (startTime === null) startTime = ts;
    const elapsed = ts - startTime;
    const t = (elapsed % durationMs) / durationMs; // 0..1
    const tick = Math.floor(t * totalTicks);

    // advance one tick when crossing
    if (tick !== (frame._lastTick || -1)) {
      stepAgents(rand, agents, gridW, gridH);
      frame._lastTick = tick;
      onTick(tick);
    }
    // reset loop
    if (elapsed > durationMs) {
      startTime = ts;
      rand = seededRand(seed);
      agents = makeAgents(rand, nAgents, gridW, gridH);
      frame._lastTick = -1;
    }

    draw(tick);
    onFrame(t, tick);
    rafId = requestAnimationFrame(frame);
  }

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduced) {
    rafId = requestAnimationFrame(frame);
  } else {
    draw(0);
  }

  return {
    pause() { paused = true; },
    resume() { paused = false; },
    toggle() { paused = !paused; return paused; },
    stop() { cancelAnimationFrame(rafId); },
    setSpeed(mult) { /* adjust duration */ },
    setDuration(ms) { /* external */ },
    setPaused(p) { paused = p; },
    isPaused() { return paused; },
    redraw: () => draw(0),
  };
}

window.runHeroGrid = runHeroGrid;
