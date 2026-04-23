"use client";

import { useEffect, useRef, useState } from "react";
import { runHeroGrid, type HeroGridHandle } from "./heroGrid";

type Lang = "en" | "ko";
type QsKey = "py" | "cli" | "rest";

const I18N = {
  en: {
    h1: 'Agent simulation<br/>that <em>remembers</em><span class="dot-end">.</span>',
    sub: "City-scale multi-agent simulation with deterministic replay, a layered memory stack, and 28 research-grounded personality archetypes. Open methodology, reproducible artifacts, commercial tiers.",
    cta1: "Try the playground",
    cta2: "Read the paper",
  },
  ko: {
    h1: '재생 가능한 <em>도시 규모</em><br/>시뮬레이션<span class="dot-end">.</span>',
    sub: "결정적으로 재생 가능한 도시 규모 멀티 에이전트 시뮬레이션. 계층형 메모리 스택과 28개의 학술 근거 성격 아키타입. 개방된 방법론, 재현 가능한 산출물, 상업 티어.",
    cta1: "플레이그라운드 열기",
    cta2: "논문 읽기",
  },
};

const SNIPPETS: Record<QsKey, { file: string; html: string }> = {
  py: {
    file: "luvoire_demo.py",
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
    file: "run.sh",
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
    file: "request.sh",
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

const H1_VARIANTS: Record<string, { en: string; ko: string }> = {
  "1": {
    en: 'Agent simulation<br/>that <em>remembers</em><span class="dot-end">.</span>',
    ko: '기억하는 <em>에이전트</em><br/>시뮬레이션<span class="dot-end">.</span>',
  },
  "2": {
    en: 'Deterministic<br/>multi-agent <em>simulation</em><span class="dot-end">.</span>',
    ko: '결정적 멀티에이전트<br/><em>시뮬레이션</em><span class="dot-end">.</span>',
  },
  "3": {
    en: 'Replayable <em>city-scale</em><br/>simulation<span class="dot-end">.</span>',
    ko: '재생 가능한 <em>도시 규모</em><br/>시뮬레이션<span class="dot-end">.</span>',
  },
};

const H1_VARIANT: "1" | "2" | "3" = "3";

type LuvoireLandingProps = {
  initialLang?: Lang;
};

export default function LuvoireLanding({ initialLang = "en" }: LuvoireLandingProps) {
  const heroCanvasRef = useRef<HTMLCanvasElement>(null);
  const pgCanvasRef = useRef<HTMLCanvasElement>(null);
  const heroHandleRef = useRef<HeroGridHandle | null>(null);
  const navProgressRef = useRef<HTMLDivElement>(null);

  const [lang, setLang] = useState<Lang>(initialLang);
  const [qs, setQs] = useState<QsKey>("py");
  const [heroStatus, setHeroStatus] = useState<"live" | "paused">("live");
  const [heroTick, setHeroTick] = useState("000");
  const [heroTime, setHeroTime] = useState("00:00 / 00:08");
  const [heroFill, setHeroFill] = useState(0);
  const [pgTick, setPgTick] = useState("000");
  const [pgActive, setPgActive] = useState("0");
  const [pgMoves, setPgMoves] = useState("0");
  const [copyLabel, setCopyLabel] = useState("Copy");

  // Hero canvas
  useEffect(() => {
    if (!heroCanvasRef.current) return;
    const handle = runHeroGrid({
      canvas: heroCanvasRef.current,
      gridW: 60,
      gridH: 60,
      nAgents: 380,
      seed: 42,
      durationMs: 8000,
      totalTicks: 100,
      onTick: (t) => setHeroTick(String(t).padStart(3, "0")),
      onFrame: (p) => {
        setHeroFill(p * 100);
        const s = Math.floor(p * 8);
        setHeroTime(`00:0${s} / 00:08`);
      },
    });
    heroHandleRef.current = handle;
    return () => {
      handle.stop();
    };
  }, []);

  // Playground canvas
  useEffect(() => {
    if (!pgCanvasRef.current) return;
    const handle = runHeroGrid({
      canvas: pgCanvasRef.current,
      gridW: 60,
      gridH: 60,
      nAgents: 900,
      seed: 1337,
      durationMs: 11000,
      totalTicks: 100,
      paddingRatio: 0.01,
      onTick: (t) => {
        setPgTick(String(t).padStart(3, "0"));
        setPgActive(String(90 + Math.floor(Math.random() * 20)));
        setPgMoves(String(540 + Math.floor(Math.random() * 160)));
      },
    });
    return () => handle.stop();
  }, []);

  // Reveal on scroll
  useEffect(() => {
    document.documentElement.classList.add("js-ready");
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0.08, rootMargin: "0px 0px -5% 0px" }
    );
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
    requestAnimationFrame(() => {
      document.querySelectorAll(".hero .reveal").forEach((el) => el.classList.add("in"));
    });
    return () => io.disconnect();
  }, []);

  // Nav progress
  useEffect(() => {
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      if (navProgressRef.current) navProgressRef.current.style.transform = `scaleX(${p})`;
    };
    window.addEventListener("scroll", update, { passive: true });
    update();
    return () => window.removeEventListener("scroll", update);
  }, []);

  const toggleHero = () => {
    const h = heroHandleRef.current;
    if (!h) return;
    const paused = h.toggle();
    setHeroStatus(paused ? "paused" : "live");
  };

  const copyInstall = async () => {
    try {
      await navigator.clipboard.writeText("pip install luvoire-engine");
      setCopyLabel("Copied");
      setTimeout(() => setCopyLabel("Copy"), 1400);
    } catch {
      // ignore
    }
  };

  const smoothTo = (e: React.MouseEvent<HTMLAnchorElement>, hash: string) => {
    if (!hash.startsWith("#")) return;
    const el = document.querySelector(hash);
    if (el) {
      e.preventDefault();
      window.scrollTo({ top: (el as HTMLElement).offsetTop - 60, behavior: "smooth" });
    }
  };

  const h1Html = H1_VARIANTS[H1_VARIANT][lang];
  const subText = I18N[lang].sub;
  const cta1 = I18N[lang].cta1;
  const cta2 = I18N[lang].cta2;

  return (
    <>
      {/* NAV */}
      <header className="nav">
        <div className="shell nav-inner">
          <a className="brand" href="#">
            <span className="wm">
              Luv<em>oire</em>
            </span>
            <span className="pron mono" title="Pronounced 'loo-vwahr'">
              /luː.vwɑːr/
            </span>
          </a>
          <nav className="nav-links" aria-label="Primary">
            <a href="#capabilities" data-nav onClick={(e) => smoothTo(e, "#capabilities")}>
              Features
            </a>
            <a href="#research" data-nav onClick={(e) => smoothTo(e, "#research")}>
              Research
            </a>
            <a href="#pricing" data-nav onClick={(e) => smoothTo(e, "#pricing")}>
              Pricing
            </a>
            <a href="#quickstart" data-nav onClick={(e) => smoothTo(e, "#quickstart")}>
              Docs
            </a>
            <a href="/status.html">Status</a>
          </nav>
          <div className="nav-right">
            <div className="lang" role="tablist" aria-label="Language">
              <button
                type="button"
                className={lang === "en" ? "on" : ""}
                onClick={() => setLang("en")}
                role="tab"
                aria-selected={lang === "en" ? "true" : "false"}
              >
                EN
              </button>
              <button
                type="button"
                className={lang === "ko" ? "on" : ""}
                onClick={() => setLang("ko")}
                role="tab"
                aria-selected={lang === "ko" ? "true" : "false"}
              >
                KO
              </button>
            </div>
            <a className="icon-link" href="https://github.com/Celovin/luvoire" aria-label="GitHub">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 .5C5.65.5.5 5.65.5 12a11.5 11.5 0 0 0 7.86 10.93c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.33-1.29-1.68-1.29-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.2 1.77 1.2 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.08-.12-.3-.52-1.47.11-3.07 0 0 .97-.31 3.19 1.18a11 11 0 0 1 5.8 0c2.22-1.49 3.19-1.18 3.19-1.18.63 1.6.23 2.77.11 3.07.74.8 1.19 1.82 1.19 3.08 0 4.41-2.7 5.38-5.27 5.67.41.35.78 1.05.78 2.11v3.13c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
              </svg>
              <span>GitHub</span>
            </a>
            <a className="btn-ghost" href="#">
              Sign in
            </a>
            <a className="btn-primary" href="#pricing" onClick={(e) => smoothTo(e, "#pricing")}>
              Start free
            </a>
          </div>
        </div>
        <div className="nav-progress" ref={navProgressRef}></div>
      </header>

      {/* HERO */}
      <section className="hero">
        <div className="shell">
          <div className="hero-grid">
            <div>
              <div className="meta-row reveal">
                <span className="mono">
                  <span className="dot"></span>&nbsp; v0.12 · beta
                </span>
                <span className="sep">/</span>
                <span className="mono">Celovin Research</span>
                <span className="sep">/</span>
                <span className="mono">Seoul · Open methodology</span>
              </div>

              <h1
                className="serif reveal"
                dangerouslySetInnerHTML={{ __html: h1Html }}
              ></h1>
              <p className="sub reveal">{subText}</p>

              <div className="cta-row reveal">
                <a className="cta-primary" href="#">
                  <span>{cta1}</span>
                  <svg
                    className="arrow"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M5 12h14M13 5l7 7-7 7" />
                  </svg>
                </a>
                <a className="cta-secondary" href="#">
                  {cta2}
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M7 17L17 7M9 7h8v8" />
                  </svg>
                </a>
              </div>

              <div className="install reveal" aria-label="Install">
                <code>
                  <span className="dim">$</span>&nbsp;pip install luvoire-engine
                </code>
                <button type="button" className="copy" onClick={copyInstall}>
                  {copyLabel}
                </button>
              </div>
            </div>

            <div className="stage reveal" aria-label="Deterministic replay preview">
              <div className="stage-header">
                <span>
                  Replay · gangnam_7pm · tick <span>{heroTick}</span>/100
                </span>
                <span className="pill">
                  <span className="dot"></span>
                  <span>{heroStatus}</span>
                </span>
              </div>

              <canvas
                ref={heroCanvasRef}
                className="grid-canvas"
                width={720}
                height={720}
                aria-hidden="true"
              ></canvas>

              <div className="stage-timeline">
                <button type="button" className="play" onClick={toggleHero} aria-label="Play/Pause">
                  {heroStatus === "paused" ? (
                    <svg width="9" height="10" viewBox="0 0 9 10" fill="currentColor" aria-hidden="true">
                      <rect x="1.5" y="1" width="2" height="8" />
                      <rect x="5.5" y="1" width="2" height="8" />
                    </svg>
                  ) : (
                    <svg width="9" height="10" viewBox="0 0 9 10" fill="currentColor" aria-hidden="true">
                      <path d="M1 1l7 4-7 4V1z" />
                    </svg>
                  )}
                </button>
                <div className="scrub">
                  <div className="fill" style={{ width: `${heroFill.toFixed(1)}%` }}></div>
                  <span className="tick" style={{ left: "25%" }}></span>
                  <span className="tick" style={{ left: "50%" }}></span>
                  <span className="tick" style={{ left: "75%" }}></span>
                </div>
                <span>{heroTime}</span>
              </div>

              <div className="stage-footer">
                <div>
                  <span className="k">Grid</span>
                  <span className="v">60 × 60</span>
                </div>
                <div>
                  <span className="k">Agents</span>
                  <span className="v">10,000</span>
                </div>
                <div>
                  <span className="k">SHA256</span>
                  <span className="v sha" style={{ color: "var(--bronze)" }}>
                    a9f3…c021
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ETYMOLOGY */}
      <section className="etym">
        <div className="shell etym-grid">
          <div className="etym-label">
            <div className="eyebrow">
              <span className="num">—</span>Etymology
            </div>
            <div className="etym-word serif">
              Luv<em>oire</em>
            </div>
            <div
              className="mono"
              style={{ fontSize: "11px", color: "var(--taupe-soft)", letterSpacing: "0.05em" }}
            >
              /luː.vwɑːr/ · 루부아르
            </div>
          </div>
          <div className="etym-trio">
            <div className="etym-card">
              <div className="etym-fr serif">
                mém<em>oire</em>
              </div>
              <div className="etym-gloss mono">memory</div>
              <p>
                A three-layer stack — working, episodic, long-term — persisted across sessions, with forgetting
                dynamics.
              </p>
            </div>
            <div className="etym-card">
              <div className="etym-fr serif">
                hist<em>oire</em>
              </div>
              <div className="etym-gloss mono">history · replay</div>
              <p>Every tick is recorded to msgpack. Same seed, byte-identical. Citable and auditable.</p>
            </div>
            <div className="etym-card">
              <div className="etym-fr serif">
                répert<em>oire</em>
              </div>
              <div className="etym-gloss mono">library · personas</div>
              <p>28 research-grounded archetypes (CAT-28) plus criminology Tier 1/2. Each card carries its own bibliography.</p>
            </div>
          </div>
        </div>
      </section>

      {/* PROOF */}
      <section className="proof">
        <div className="shell proof-grid">
          <div className="label">Context&nbsp;/&nbsp;affiliations</div>
          <div className="proof-items">
            <span className="item">Submitted to ASC 2026</span>
            <span className="item">Part of Celovin&apos;s research stack</span>
            <span className="item mono">Nemotron-Personas-Korea · NVIDIA · CC-BY-4.0</span>
            <span className="item mono">KOSIS demographic base</span>
          </div>
        </div>
      </section>

      {/* CAPABILITIES */}
      <section className="sec" id="capabilities">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 01</span>Capabilities
            </div>
            <div>
              <h2 className="serif">
                What Luvoire <em>gives you</em>.
              </h2>
              <p className="lede">
                Four engine guarantees, written as primitives rather than marketing. Each maps to a public artifact, benchmark, or citation.
              </p>
            </div>
          </div>

          <div className="caps">
            <div className="cap reveal">
              <div className="ix">01</div>
              <svg className="glyph" viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">
                <rect x="3" y="3" width="38" height="38" stroke="#A8753A" />
                <path d="M3 15h38M3 27h38M15 3v38M27 3v38" stroke="#D9D1C2" />
                <rect x="15" y="15" width="12" height="12" fill="#A8753A" opacity=".18" stroke="#A8753A" />
                <circle cx="21" cy="21" r="1.5" fill="#A8753A" />
              </svg>
              <h3>Deterministic replay</h3>
              <p>Same seed, byte-identical msgpack. Verified at 10,000 agents on a 60×60 grid, weekly regression guarded at 15%.</p>
              <a className="more" href="#">Learn more →</a>
              <span className="meta">
                replay_10000agents_gangnam_7pm.msgpack · <span className="v">9.5 MB</span>
              </span>
            </div>

            <div className="cap reveal">
              <div className="ix">02</div>
              <svg className="glyph" viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">
                <ellipse cx="22" cy="10" rx="16" ry="4" stroke="#A8753A" />
                <ellipse cx="22" cy="22" rx="16" ry="4" stroke="#5C5148" />
                <ellipse cx="22" cy="34" rx="16" ry="4" stroke="#8A7F74" />
                <path d="M6 10v24M38 10v24" stroke="#D9D1C2" />
              </svg>
              <h3>Layered memory stack</h3>
              <p>Working, episodic, and long-term memory modeled separately. Session-persistent with explicit forgetting dynamics.</p>
              <a className="more" href="#">Learn more →</a>
              <span className="meta">
                3 layers · <span className="v">O(log n) recall</span>
              </span>
            </div>

            <div className="cap reveal">
              <div className="ix">03</div>
              <svg className="glyph" viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">
                <circle cx="22" cy="22" r="16" stroke="#A8753A" />
                <circle cx="22" cy="22" r="10" stroke="#D9D1C2" />
                <circle cx="22" cy="22" r="4" fill="#A8753A" opacity=".2" stroke="#A8753A" />
                <path d="M22 6v8M22 30v8M6 22h8M30 22h8M10.3 10.3l5.7 5.7M27.9 27.9l5.7 5.7M10.3 33.7l5.7-5.7M27.9 16l5.7-5.7" stroke="#8A7F74" />
              </svg>
              <h3>28 archetypes, cited</h3>
              <p>CAT-28 (22 single + 6 composite) plus criminology Tier 1/2 types. Each with DOI/ISBN/ISSN references in the methods appendix.</p>
              <a className="more" href="#">Learn more →</a>
              <span className="meta">
                22 single · 6 composite · <span className="v">12 peer-reviewed</span>
              </span>
            </div>

            <div className="cap reveal">
              <div className="ix">04</div>
              <svg className="glyph" viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">
                <rect x="8" y="5" width="28" height="34" stroke="#A8753A" />
                <path d="M13 14h18M13 20h18M13 26h12M13 32h8" stroke="#8A7F74" />
                <path d="M28 30l3 3 5-6" stroke="#A8753A" strokeWidth="1.6" />
              </svg>
              <h3>Open methodology</h3>
              <p>CycloneDX SBOM, attribution, audit log, reproducible artifacts. Written to clear research review and compliance.</p>
              <a className="more" href="#">Learn more →</a>
              <span className="meta">
                SBOM · Audit log · <span className="v">PIPA / GDPR ready</span>
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* PLAYGROUND */}
      <section className="sec" id="playground">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 02</span>Playground
            </div>
            <div>
              <h2 className="serif">
                See it <em>replay</em>.
              </h2>
              <p className="lede">
                A recorded run of 10,000 agents on a 60×60 grid, Gangnam 7 p.m. scenario. Every frame is deterministically reproducible from the seed below.
              </p>
            </div>
          </div>

          <div className="pg reveal">
            <div className="pg-head">
              <div className="tabs">
                <span className="t on">replay</span>
                <span className="t">inspect</span>
                <span className="t">log</span>
              </div>
              <div>
                seed = <span style={{ color: "var(--bronze-deep)" }}>42</span> · ticks 0–100 · 60 × 60
              </div>
            </div>
            <div className="pg-body">
              <div className="pg-canvas-wrap">
                <canvas ref={pgCanvasRef} width={1000} height={620}></canvas>
              </div>
              <aside className="pg-side">
                <div className="row">
                  <span className="k">File</span>
                  <span></span>
                </div>
                <div className="row">
                  <span className="v" style={{ fontSize: "11px" }}>replay_gangnam_7pm.msgpack</span>
                  <span className="v bronze">9.5 MB</span>
                </div>
                <div className="row">
                  <span className="k">SHA256</span>
                  <span></span>
                </div>
                <div className="row">
                  <span className="v bronze" style={{ fontSize: "10.5px" }}>a9f3e8b2…c02137d4</span>
                  <span></span>
                </div>

                <h4>Layers</h4>
                <div className="legend">
                  <div className="li"><span className="sw" style={{ background: "#A8753A" }}></span>Decision active</div>
                  <div className="li"><span className="sw" style={{ background: "#7A8F7B" }}></span>Moving</div>
                  <div className="li"><span className="sw" style={{ background: "#8A7F74" }}></span>Idle</div>
                  <div className="li"><span className="sw" style={{ background: "#C99A63", opacity: 0.5 }}></span>Memory trail</div>
                </div>

                <h4>Frame</h4>
                <div className="row"><span className="k">Tick</span><span className="v mono">{pgTick}</span></div>
                <div className="row"><span className="k">Active</span><span className="v mono">{pgActive}</span></div>
                <div className="row"><span className="k">Moves</span><span className="v mono">{pgMoves}</span></div>
              </aside>
            </div>
            <div className="pg-foot">
              <span>60×60 grid · 10,000 agents · gangnam_7pm · deterministic</span>
              <a href="#">Open full playground →</a>
            </div>
          </div>
        </div>
      </section>

      {/* RESEARCH */}
      <section className="sec" id="research">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 03</span>Research
            </div>
            <div>
              <h2 className="serif">
                Built for <em>research-grade</em> work.
              </h2>
              <p className="lede">
                Citations, provenance, artifacts, and licensing written to hold up in peer review and in a commercial procurement pass.
              </p>
            </div>
          </div>

          <div className="research reveal">
            <div className="rcell">
              <div className="ix">01 · Citations</div>
              <h3>Bibliography-backed archetypes</h3>
              <p>CAT-28 rests on twelve peer-reviewed citations and six monographs. Every archetype card surfaces its DOI, ISBN, and ISSN inline.</p>
              <div className="cites">
                <span className="c">DOI <span className="y">10.1037/…</span></span>
                <span className="c">ISBN <span className="y">978-0-19…</span></span>
                <span className="c">ISSN <span className="y">0033-…</span></span>
                <span className="c">+ 9 more</span>
              </div>
              <br />
              <a className="more" href="#">View citations →</a>
            </div>
            <div className="rcell">
              <div className="ix">02 · Provenance</div>
              <h3>Dataset lineage, pinned</h3>
              <p>Nemotron-Personas-Korea from NVIDIA, 2025, CC-BY-4.0. Grounded in KOSIS demographics. Revision SHA pinned per release.</p>
              <div className="cites">
                <span className="c">License <span className="y">CC-BY-4.0</span></span>
                <span className="c">Source <span className="y">KOSIS</span></span>
                <span className="c">Rev <span className="y">#a41f88c</span></span>
              </div>
              <br />
              <a className="more" href="#">Read attribution →</a>
            </div>
            <div className="rcell">
              <div className="ix">03 · Artifacts</div>
              <h3>Reproducible replay files</h3>
              <p>Five public msgpack runs, SHA256 fixed, guarded against 15% regression by a weekly CI run. Replay on any machine, any OS.</p>
              <div className="cites">
                <span className="c">Runs <span className="y">5</span></span>
                <span className="c">Guard <span className="y">15%</span></span>
                <span className="c">CI <span className="y">weekly</span></span>
              </div>
              <br />
              <a className="more" href="#">Download artifacts →</a>
            </div>
            <div className="rcell">
              <div className="ix">04 · Commerce</div>
              <h3>Commercial-ready, without drama</h3>
              <p>MIT core with commercial tiers. Toss Payments for KR, Paddle globally. PIPA and GDPR-aligned privacy drafts available.</p>
              <div className="cites">
                <span className="c">License <span className="y">MIT</span></span>
                <span className="c">Billing <span className="y">Toss · Paddle</span></span>
                <span className="c">Privacy <span className="y">PIPA · GDPR</span></span>
              </div>
              <br />
              <a className="more" href="#">Read the DPA →</a>
            </div>
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section className="sec" id="pricing">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 04</span>Pricing
            </div>
            <div>
              <h2 className="serif">
                Four tiers. <em>No mysteries.</em>
              </h2>
              <p className="lede">Full comparison table lives on the pricing page. These are the core numbers.</p>
            </div>
          </div>

          <div className="pricing reveal">
            <div className="tier">
              <h3 className="name">Free</h3>
              <p className="tagline">For coursework, replication studies, and first runs.</p>
              <div className="price">
                $0<span className="unit">&nbsp;/ mo</span>
              </div>
              <div className="incl">Community support</div>
              <ul>
                <li><span className="bullet">—</span>Up to 500 agents</li>
                <li><span className="bullet">—</span>Single-machine replay</li>
                <li><span className="bullet">—</span>Public artifacts</li>
                <li><span className="bullet">—</span>MIT core</li>
              </ul>
              <button type="button" className="cta">Start free</button>
            </div>

            <div className="tier featured">
              <h3 className="name">Pro</h3>
              <p className="tagline">For the paper you&apos;re writing this semester.</p>
              <div className="price">
                $49<span className="unit">&nbsp;/ mo</span>
              </div>
              <div className="incl">Priority email · Citable DOI</div>
              <ul>
                <li><span className="bullet">—</span>Up to 10,000 agents</li>
                <li><span className="bullet">—</span>Hosted replays</li>
                <li><span className="bullet">—</span>Private archetypes</li>
                <li><span className="bullet">—</span>BibTeX generator</li>
              </ul>
              <button type="button" className="cta">Start Pro</button>
            </div>

            <div className="tier">
              <h3 className="name">Team</h3>
              <p className="tagline">For labs and small studios.</p>
              <div className="price">
                $199<span className="unit">&nbsp;/ mo</span>
              </div>
              <div className="incl">SSO · shared seeds</div>
              <ul>
                <li><span className="bullet">—</span>Up to 50,000 agents</li>
                <li><span className="bullet">—</span>Seat pooling</li>
                <li><span className="bullet">—</span>Unity adapter</li>
                <li><span className="bullet">—</span>Audit log export</li>
              </ul>
              <button type="button" className="cta">Start Team</button>
            </div>

            <div className="tier">
              <h3 className="name">Enterprise</h3>
              <p className="tagline">For R&amp;D labs and policy teams.</p>
              <div className="price serif">Contact</div>
              <div className="incl">On-prem · DPA · SLA</div>
              <ul>
                <li><span className="bullet">—</span>Unbounded scale</li>
                <li><span className="bullet">—</span>Self-hosted or VPC</li>
                <li><span className="bullet">—</span>Custom archetypes</li>
                <li><span className="bullet">—</span>Procurement support</li>
              </ul>
              <button type="button" className="cta">Book a call</button>
            </div>
          </div>
        </div>
      </section>

      {/* USE CASES */}
      <section className="sec" id="usecases">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 05</span>Use cases
            </div>
            <div>
              <h2 className="serif">
                Three audiences, <em>one engine</em>.
              </h2>
            </div>
          </div>

          <div className="usecases">
            <div className="uc reveal">
              <div className="tag">For researchers</div>
              <h3>Cite Luvoire in your methods section.</h3>
              <pre
                className="sample"
                dangerouslySetInnerHTML={{
                  __html: `<span class="c">% BibTeX</span>
<span class="k">@software</span>{<span class="n">luvoire2026</span>,
  <span class="k">title</span>  = {<span class="s">Luvoire</span>},
  <span class="k">author</span> = {<span class="s">Choi, J.</span>},
  <span class="k">year</span>   = {<span class="s">2026</span>},
  <span class="k">doi</span>    = {<span class="s">10.5281/...</span>}
}`,
                }}
              />
              <a className="more" href="#">How to cite →</a>
            </div>

            <div className="uc reveal">
              <div className="tag">For game studios</div>
              <h3>Ship NPCs with behavior that holds up to playtest.</h3>
              <pre
                className="sample"
                dangerouslySetInnerHTML={{
                  __html: `<span class="c"># Unity adapter</span>
<span class="k">using</span> <span class="n">Luvoire</span>;

<span class="k">var</span> npc = <span class="k">new</span> <span class="n">Agent</span>(
  <span class="s">archetype:</span> <span class="n">CAT28</span>.Guardian,
  <span class="s">seed:</span> <span class="n">42</span>
);`,
                }}
              />
              <a className="more" href="#">Get a Team license →</a>
            </div>

            <div className="uc reveal">
              <div className="tag">For R&amp;D labs</div>
              <h3>Run scenario simulations with auditable replay.</h3>
              <pre
                className="sample"
                dangerouslySetInnerHTML={{
                  __html: `<span class="c"># curl</span>
curl <span class="s">-X POST</span> \\
  api.luvoire.com/v1/runs \\
  <span class="s">-d</span> '<span class="k">seed</span>=<span class="n">42</span>,
       <span class="k">agents</span>=<span class="n">10000</span>,
       <span class="k">scenario</span>=<span class="s">crisis</span>'`,
                }}
              />
              <a className="more" href="#">Talk to sales →</a>
            </div>
          </div>
        </div>
      </section>

      {/* QUICKSTART */}
      <section className="sec" id="quickstart">
        <div className="shell">
          <div className="sec-head reveal">
            <div className="meta">
              <span className="num">§ 06</span>Quickstart
            </div>
            <div>
              <h2 className="serif">
                Get running in <em>sixty seconds</em>.
              </h2>
              <p className="lede">
                Three idioms, one engine. Pick Python for notebooks, CLI for reproducible batches, REST for service integration.
              </p>
            </div>
          </div>

          <div className="qs reveal">
            <div className="qs-notes">
              <div className="qs-tabs" role="tablist">
                {(["py", "cli", "rest"] as QsKey[]).map((k) => (
                  <button
                    type="button"
                    key={k}
                    className={qs === k ? "on" : ""}
                    onClick={() => setQs(k)}
                    role="tab"
                    aria-selected={qs === k ? "true" : "false"}
                  >
                    {k === "py" ? "Python" : k === "cli" ? "CLI" : "REST"}
                  </button>
                ))}
              </div>
              <div className="item">
                <div className="n">01</div>
                <div>
                  <h4>Declare the world</h4>
                  <p>A grid, an agent count, and a seed fully specify a run.</p>
                </div>
              </div>
              <div className="item">
                <div className="n">02</div>
                <div>
                  <h4>Step the simulation</h4>
                  <p>Each tick advances decision, memory, and movement layers together.</p>
                </div>
              </div>
              <div className="item">
                <div className="n">03</div>
                <div>
                  <h4>Save a replay</h4>
                  <p>Msgpack output is byte-identical for equal seeds — safe to cite.</p>
                </div>
              </div>
              <div className="item">
                <div className="n">04</div>
                <div>
                  <h4>Re-open anywhere</h4>
                  <p>Any machine, any OS. Replay verifies its own SHA256 on load.</p>
                </div>
              </div>
            </div>

            <div className="qs-code">
              <div className="bar">
                <span>{SNIPPETS[qs].file}</span>
                <span>press ⌘C</span>
              </div>
              <pre dangerouslySetInnerHTML={{ __html: SNIPPETS[qs].html }} />
            </div>
          </div>
        </div>
      </section>

      {/* TRUST */}
      <section className="sec" id="trust" style={{ padding: "64px 0" }}>
        <div className="shell">
          <div className="trust reveal">
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 7l8-4 8 4v5c0 5-8 9-8 9s-8-4-8-9V7z" />
              </svg>{" "}
              CC-BY-4.0 dataset
            </a>
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 4h16v16H4z" />
                <path d="M8 8h8M8 12h8M8 16h5" />
              </svg>{" "}
              MIT core license
            </a>
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 3v18M3 12h18" />
              </svg>{" "}
              CycloneDX SBOM
            </a>
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="4" y="4" width="16" height="16" />
                <path d="M8 10h8M8 14h6" />
              </svg>{" "}
              Audit log, PIPA-ready
            </a>
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v10M9 10h5a2 2 0 010 4H9" />
              </svg>{" "}
              Stripe metering
            </a>
            <a className="tr" href="#">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2l3 7h7l-5.5 4 2 8-6.5-5-6.5 5 2-8L2 9h7z" />
              </svg>{" "}
              HMAC-SHA256 webhooks
            </a>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="shell">
          <div className="foot-grid">
            <div className="foot-brand">
              <div className="wm serif">
                Luv<em>oire</em>
              </div>
              <p>A research engine by Celovin. Built in Seoul, designed to be cited.</p>
              <div className="pron mono">Luvoire /luː.vwɑːr/ · 루부아르</div>
            </div>
            <div>
              <h5>Product</h5>
              <ul>
                <li><a href="#playground">Playground</a></li>
                <li><a href="#capabilities">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="https://github.com/Celovin/luvoire/blob/main/CHANGELOG.md">Changelog</a></li>
              </ul>
            </div>
            <div>
              <h5>Research</h5>
              <ul>
                <li><a href="#research">Paper (preprint)</a></li>
                <li><a href="#research">CAT-28 bibliography</a></li>
                <li><a href="https://github.com/Celovin/luvoire/releases">Replay artifacts</a></li>
                <li><a href="https://github.com/Celovin/luvoire/blob/main/sbom.cdx.json">SBOM</a></li>
              </ul>
            </div>
            <div>
              <h5>Company</h5>
              <ul>
                <li><a href="https://celovin.com">About Celovin</a></li>
                <li><a href="mailto:hello@celovin.com">hello@celovin.com</a></li>
                <li><a href="https://github.com/Celovin/luvoire">GitHub</a></li>
                <li><a href="https://github.com/Celovin/luvoire/blob/main/POLICIES/civilian_use.md">Civilian Use</a></li>
                <li><a href="/status.html">Status</a></li>
              </ul>
            </div>
          </div>
          <div className="foot-bottom">
            <span>© 2026 Celovin</span>
            <span>Terms &nbsp;·&nbsp; Privacy &nbsp;·&nbsp; DPA &nbsp;·&nbsp; Refund Policy</span>
          </div>
        </div>
      </footer>
    </>
  );
}
