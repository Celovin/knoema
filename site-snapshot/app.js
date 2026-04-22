// Luvoire — app controller
(function () {
  // ---------- Reveal on scroll ----------
  document.documentElement.classList.add('js-ready');
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    }
  }, { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
  // Above-fold: force-show immediately
  requestAnimationFrame(() => {
    document.querySelectorAll('.hero .reveal').forEach(el => el.classList.add('in'));
  });

  // ---------- Nav progress ----------
  const navProgress = document.getElementById('navProgress');
  function updateProgress() {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    if (navProgress) navProgress.style.transform = `scaleX(${p})`;
  }
  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();

  // ---------- Hero canvas ----------
  const heroCanvas = document.getElementById('heroCanvas');
  const tickLabel = document.getElementById('tickLabel');
  const statusLabel = document.getElementById('statusLabel');
  const scrubFill = document.getElementById('scrubFill');
  const timeLabel = document.getElementById('timeLabel');
  const playBtn = document.getElementById('playBtn');
  const playIcon = document.getElementById('playIcon');

  const hero = window.runHeroGrid({
    canvas: heroCanvas,
    gridW: 60, gridH: 60,
    nAgents: 380,
    seed: 42,
    durationMs: 8000,
    totalTicks: 100,
    onTick: (t) => {
      if (tickLabel) tickLabel.textContent = String(t).padStart(3, '0');
    },
    onFrame: (p, t) => {
      if (scrubFill) scrubFill.style.width = (p * 100).toFixed(1) + '%';
      if (timeLabel) {
        const s = Math.floor(p * 8);
        timeLabel.textContent = `00:0${s} / 00:08`;
      }
    },
  });

  playBtn?.addEventListener('click', () => {
    const paused = hero.toggle();
    if (statusLabel) statusLabel.textContent = paused ? 'paused' : 'live';
    if (playIcon) {
      if (paused) {
        playIcon.innerHTML = '<rect x="1.5" y="1" width="2" height="8"/><rect x="5.5" y="1" width="2" height="8"/>';
      } else {
        playIcon.innerHTML = '<path d="M1 1l7 4-7 4V1z"/>';
      }
    }
  });

  // ---------- Playground canvas (bigger, denser) ----------
  const pgCanvas = document.getElementById('pgCanvas');
  const pgTick = document.getElementById('pgTick');
  const pgActive = document.getElementById('pgActive');
  const pgMoves = document.getElementById('pgMoves');

  if (pgCanvas) {
    window.runHeroGrid({
      canvas: pgCanvas,
      gridW: 60, gridH: 60,
      nAgents: 900,
      seed: 1337,
      durationMs: 11000,
      totalTicks: 100,
      paddingRatio: 0.01,
      onTick: (t) => {
        if (pgTick) pgTick.textContent = String(t).padStart(3, '0');
        if (pgActive) pgActive.textContent = String(90 + Math.floor(Math.random() * 20));
        if (pgMoves) pgMoves.textContent = String(540 + Math.floor(Math.random() * 160));
      },
    });
  }

  // ---------- Copy install ----------
  const copyBtn = document.getElementById('copyInstall');
  copyBtn?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText('pip install luvoire-engine');
      const prev = copyBtn.textContent;
      copyBtn.textContent = 'Copied';
      setTimeout(() => copyBtn.textContent = prev, 1400);
    } catch {}
  });

  // ---------- Quickstart tabs ----------
  const snippets = {
    py: {
      file: 'luvoire_demo.py',
      html: `<span class="k">import</span> <span class="n">luvoire</span>

sim = <span class="n">luvoire</span>.<span class="f">City</span>(
    <span class="k">grid</span>=(<span class="n">60</span>, <span class="n">60</span>),
    <span class="k">agents</span>=<span class="n">10_000</span>,
    <span class="k">seed</span>=<span class="n">42</span>,
)

replay = sim.<span class="f">run</span>(<span class="k">ticks</span>=<span class="n">100</span>)
replay.<span class="f">save</span>(<span class="s">"my_run.msgpack"</span>)

<span class="c"># deterministic: same seed → same bytes</span>
<span class="k">assert</span> replay.<span class="f">sha256</span>() == <span class="s">"a9f3e8b2…c02137d4"</span>`,
    },
    cli: {
      file: 'run.sh',
      html: `<span class="c"># install</span>
$ pip install luvoire-engine

<span class="c"># reproduce the Gangnam 7 p.m. scenario</span>
$ luvoire run <span class="s">--scenario</span> gangnam_7pm \\
              <span class="s">--agents</span> <span class="n">10000</span> \\
              <span class="s">--seed</span> <span class="n">42</span> \\
              <span class="s">--out</span> run.msgpack

$ luvoire verify run.msgpack
<span class="c">→ sha256 matches: a9f3e8b2…c02137d4</span>`,
    },
    rest: {
      file: 'request.sh',
      html: `<span class="c"># POST a run</span>
$ curl -X POST https://api.luvoire.com/v1/runs \\
    -H <span class="s">"Authorization: Bearer $LUVOIRE_KEY"</span> \\
    -d '{
      <span class="k">"seed"</span>: <span class="n">42</span>,
      <span class="k">"agents"</span>: <span class="n">10000</span>,
      <span class="k">"scenario"</span>: <span class="s">"gangnam_7pm"</span>
    }'

<span class="c"># webhook signed with HMAC-SHA256</span>
<span class="c"># { "run_id": "r_9f32", "replay_url": "...", "sha256": "a9f3…" }</span>`,
    },
  };
  const qsPre = document.getElementById('qsPre');
  const qsFile = document.getElementById('qsFile');
  document.querySelectorAll('[data-qs]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-qs]').forEach(b => { b.classList.remove('on'); b.setAttribute('aria-selected','false'); });
      btn.classList.add('on'); btn.setAttribute('aria-selected','true');
      const key = btn.dataset.qs;
      qsPre.innerHTML = snippets[key].html;
      qsFile.textContent = snippets[key].file;
    });
  });

  // ---------- Language toggle (EN/KO) ----------
  const I18N = {
    en: {
      h1: 'Agent simulation<br>that <em>remembers</em><span class="dot-end">.</span>',
      sub: "City-scale multi-agent simulation with deterministic replay, a layered memory stack, and 28 research-grounded personality archetypes. Open methodology, reproducible artifacts, commercial tiers.",
      cta1: 'Try the playground',
      cta2: 'Read the paper',
    },
    ko: {
      h1: '기억하는<br><em>에이전트</em> 시뮬레이션<span class="dot-end">.</span>',
      sub: '결정적으로 재생 가능한 도시 규모 멀티 에이전트 시뮬레이션. 계층형 메모리 스택과 28개의 학술 근거 성격 아키타입. 개방된 방법론, 재현 가능한 산출물, 상업 티어.',
      cta1: '플레이그라운드 열기',
      cta2: '논문 읽기',
    },
  };
  function setLang(lang) {
    const t = I18N[lang];
    document.querySelectorAll('[data-t="h1"]').forEach(el => el.innerHTML = t.h1);
    document.querySelectorAll('[data-t="sub"]').forEach(el => el.textContent = t.sub);
    document.querySelectorAll('[data-t="cta1"]').forEach(el => {
      el.firstElementChild.textContent = t.cta1;
      el.firstElementChild.nextElementSibling; // keep arrow
      el.querySelector('span').textContent = t.cta1;
    });
    document.querySelectorAll('[data-t="cta2"]').forEach(el => {
      el.childNodes[0].nodeValue = t.cta2 + ' ';
    });
    document.documentElement.setAttribute('lang', lang);
  }
  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-lang]').forEach(b => { b.classList.remove('on'); b.setAttribute('aria-selected','false'); });
      btn.classList.add('on'); btn.setAttribute('aria-selected','true');
      setLang(btn.dataset.lang);
    });
  });

  // ---------- Smooth scroll ----------
  document.querySelectorAll('[data-nav]').forEach(a => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href');
      if (href && href.startsWith('#')) {
        const el = document.querySelector(href);
        if (el) { e.preventDefault(); window.scrollTo({ top: el.offsetTop - 60, behavior: 'smooth' }); }
      }
    });
  });

  // ---------- Tweaks ----------
  const tweaks = document.getElementById('tweaks');
  const state = Object.assign({}, window.TWEAK_DEFAULTS || {
    accent: '#A8753A', base: '#F7F3EC', h1Variant: '1', serif: 'Source Serif 4', motion: 'on'
  });

  function applyState() {
    document.documentElement.style.setProperty('--bronze', state.accent);
    // derive bronze-deep
    document.documentElement.style.setProperty('--bronze-deep', shade(state.accent, -0.18));
    document.documentElement.style.setProperty('--cream', state.base);

    // serif
    const serifRule = document.querySelectorAll('.serif, h1.serif, h2, h3, .brand .wm, .foot-brand .wm');
    serifRule.forEach(el => el.style.fontFamily = `'${state.serif}', Georgia, serif`);

    // h1 variant
    const h1 = document.querySelector('[data-t="h1"]');
    if (h1) {
      if (state.h1Variant === '2') h1.innerHTML = 'Deterministic<br>multi-agent <em>simulation</em><span class="dot-end">.</span>';
      else if (state.h1Variant === '3') h1.innerHTML = 'Replayable <em>city-scale</em><br>simulation<span class="dot-end">.</span>';
      else h1.innerHTML = 'Agent simulation<br>that <em>remembers</em><span class="dot-end">.</span>';
    }

    // motion
    if (state.motion === 'off') hero.pause();
    else hero.resume();

    // mark swatches
    document.querySelectorAll('#swAccent .sw').forEach(s => s.classList.toggle('on', s.dataset.accent === state.accent));
    document.querySelectorAll('#swBase .sw').forEach(s => s.classList.toggle('on', s.dataset.base === state.base));
    const h1Sel = document.getElementById('h1Variant'); if (h1Sel) h1Sel.value = state.h1Variant;
    const serifSel = document.getElementById('serifPick'); if (serifSel) serifSel.value = state.serif;
    const motionSel = document.getElementById('motionPick'); if (motionSel) motionSel.value = state.motion;
  }

  function shade(hex, amt) {
    const c = hex.replace('#','');
    const num = parseInt(c, 16);
    let r = (num >> 16) & 0xff, g = (num >> 8) & 0xff, b = num & 0xff;
    r = Math.max(0, Math.min(255, Math.round(r + 255 * amt)));
    g = Math.max(0, Math.min(255, Math.round(g + 255 * amt)));
    b = Math.max(0, Math.min(255, Math.round(b + 255 * amt)));
    return '#' + [r,g,b].map(v => v.toString(16).padStart(2,'0')).join('');
  }

  function setKey(k, v) {
    state[k] = v;
    applyState();
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { [k]: v } }, '*');
  }

  document.querySelectorAll('#swAccent .sw').forEach(sw => {
    sw.addEventListener('click', () => setKey('accent', sw.dataset.accent));
  });
  document.querySelectorAll('#swBase .sw').forEach(sw => {
    sw.addEventListener('click', () => setKey('base', sw.dataset.base));
  });
  document.getElementById('h1Variant')?.addEventListener('change', (e) => setKey('h1Variant', e.target.value));
  document.getElementById('serifPick')?.addEventListener('change', (e) => setKey('serif', e.target.value));
  document.getElementById('motionPick')?.addEventListener('change', (e) => setKey('motion', e.target.value));

  applyState();

  // Tweaks protocol
  window.addEventListener('message', (ev) => {
    const d = ev.data;
    if (!d) return;
    if (d.type === '__activate_edit_mode') tweaks?.classList.add('on');
    if (d.type === '__deactivate_edit_mode') tweaks?.classList.remove('on');
  });
  window.parent.postMessage({ type: '__edit_mode_available' }, '*');
})();
