"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./tutorial.module.css";

type Chapter = {
  id: string;
  title: string;
  goal: string;
  steps: string[];
  code: string;
  quiz: {
    question: string;
    options: string[];
    answer: string;
  };
  result: string;
  image: string;
};

const storageKey = "knoema.tutorial.progress";

const chapters: Chapter[] = [
  {
    id: "first-agent",
    title: "Your First Agent",
    goal: "Create a persona with one clear value and one reachable goal.",
    steps: ["Name the agent.", "Set one stable value.", "Run one deterministic turn."],
    code: `from knoema import Persona, Personality

persona = Persona(
    agent_id="maya",
    name="Maya",
    age=22,
    background="Resident assistant in a shared dorm.",
    personality=Personality(
        openness=0.68,
        conscientiousness=0.74,
        extraversion=0.52,
        agreeableness=0.79,
        neuroticism=0.21,
    ),
    values=["privacy"],
    goals=["help a new resident settle in"],
)
print(persona.name)`,
    quiz: {
      question: "Which field keeps the agent stable across turns?",
      options: ["values", "temperature", "port"],
      answer: "values",
    },
    result: "Maya is ready with 1 value and 1 goal.",
    image: "/figures/memory_recall.svg",
  },
  {
    id: "memory-relationships",
    title: "Memory & Relationships",
    goal: "Attach short memory and relationship state before the next action.",
    steps: ["Write one memory.", "Raise familiarity after a helpful exchange.", "Review the next prompt context."],
    code: `from knoema import RelationshipGraph, InteractionOutcome

graph = RelationshipGraph()
graph.add_agent("maya")
graph.add_agent("jun")
graph.record_interaction("maya", "jun", InteractionOutcome.POSITIVE, weight=0.4)
edge = graph.get_relationship("maya", "jun")
print(round(edge.trust, 2))`,
    quiz: {
      question: "What should change after a helpful exchange?",
      options: ["relationship state", "package name", "license text"],
      answer: "relationship state",
    },
    result: "Trust and familiarity are now available to the next turn.",
    image: "/figures/branching.svg",
  },
  {
    id: "scenario-dsl",
    title: "Scenario DSL",
    goal: "Edit YAML that can be validated and replayed.",
    steps: ["Keep the scenario fictional.", "Set agents and events.", "Export a replayable file."],
    code: `schema_version: "1.0"
scenario_id: tutorial_dorm
title: "Dorm welcome"
domain: academic_research
seed: 20260419
agents:
  - agent_id: maya
    name: "Maya"
events:
  - event_type: welcome
    participants: [maya]
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true`,
    quiz: {
      question: "Which ethics flag blocks real-person traces?",
      options: ["no_real_people", "desired_count", "cpu"],
      answer: "no_real_people",
    },
    result: "The YAML keeps the replay fictional and reviewable.",
    image: "/figures/token_efficiency.svg",
  },
  {
    id: "theory-of-mind",
    title: "Theory of Mind",
    goal: "Run an opt-in false-belief probe without implying human cognition.",
    steps: ["Enable the module.", "Set a visible object move.", "Ask from the agent belief state."],
    code: `from knoema import TheoryOfMindEngine

engine = TheoryOfMindEngine()
engine.observe_object_location("sally", "marble", "basket")
engine.move_object_without_observer("sally", "anne", "marble", "box")
belief = engine.belief_about("sally", "marble")
print(belief)`,
    quiz: {
      question: "What does the module inspect?",
      options: ["agent belief state", "human consciousness", "billing plan"],
      answer: "agent belief state",
    },
    result: "Sally still believes the marble is in the basket.",
    image: "/figures/scalability.svg",
  },
  {
    id: "deploy-production",
    title: "Deploy to Production",
    goal: "Choose the smallest production path for the API and dashboard.",
    steps: ["Build the container.", "Pick one cloud template.", "Run the release checklist."],
    code: `python scripts/pre_release_check.py --version 0.2.0
python deploy/cloud/validate_templates.py
docker compose up api dashboard`,
    quiz: {
      question: "Which check runs before a public release?",
      options: ["pre_release_check", "random seed reset", "unscoped preview deploy"],
      answer: "pre_release_check",
    },
    result: "Release checks and cloud templates are ready for a production review.",
    image: "/og-image.png",
  },
];

export function TutorialClient() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [completed, setCompleted] = useState<string[]>([]);
  const [codeByChapter, setCodeByChapter] = useState<Record<string, string>>(
    Object.fromEntries(chapters.map((chapter) => [chapter.id, chapter.code])),
  );
  const [answer, setAnswer] = useState("");
  const [runOutput, setRunOutput] = useState("Ready");

  const chapter = chapters[activeIndex];
  const progress = Math.round((completed.length / chapters.length) * 100);
  const currentCode = codeByChapter[chapter.id] ?? chapter.code;
  const isCorrect = answer === chapter.quiz.answer;
  const canAdvance = completed.includes(chapter.id);

  useEffect(() => {
    const saved = window.localStorage.getItem(storageKey);
    if (saved) {
      setCompleted(saved.split(",").filter(Boolean));
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(storageKey, completed.join(","));
  }, [completed]);

  const chapterList = useMemo(
    () =>
      chapters.map((candidate, index) => ({
        ...candidate,
        number: index + 1,
        active: index === activeIndex,
        done: completed.includes(candidate.id),
      })),
    [activeIndex, completed],
  );

  function runChapter() {
    const lines = currentCode.split("\n").filter((line) => line.trim()).length;
    setRunOutput(`${chapter.result} ${lines} edited lines checked.`);
  }

  function markComplete() {
    if (!completed.includes(chapter.id)) {
      setCompleted([...completed, chapter.id]);
    }
  }

  function nextChapter() {
    setAnswer("");
    setRunOutput("Ready");
    setActiveIndex(Math.min(chapters.length - 1, activeIndex + 1));
  }

  return (
    <main className={styles.tutorialShell}>
      <nav className={styles.topNav} aria-label="Tutorial navigation">
        <a href="/">Knoema</a>
        <a href="/docs">Docs</a>
        <a href="/editor">Scenario editor</a>
      </nav>

      <section className={styles.workspace}>
        <aside className={styles.chapterRail} aria-label="Tutorial chapters">
          <p className={styles.eyebrow}>Interactive tutorial</p>
          <h1>Build a persistent agent in five passes.</h1>
          <div className={styles.progressShell} aria-label={`Progress ${progress}%`}>
            <span style={{ width: `${progress}%` }} />
          </div>
          <ol>
            {chapterList.map((item, index) => (
              <li key={item.id}>
                <button
                  className={item.active ? styles.activeChapter : ""}
                  onClick={() => {
                    setAnswer("");
                    setRunOutput("Ready");
                    setActiveIndex(index);
                  }}
                  type="button"
                >
                  <span>{item.number}</span>
                  <strong>{item.title}</strong>
                  <small>{item.done ? "Complete" : "Open"}</small>
                </button>
              </li>
            ))}
          </ol>
        </aside>

        <section className={styles.lessonPanel} aria-live="polite">
          <div className={styles.lessonHeader}>
            <div>
              <p className={styles.eyebrow}>Chapter {activeIndex + 1}</p>
              <h2>{chapter.title}</h2>
              <p>{chapter.goal}</p>
            </div>
            <img src={chapter.image} alt="" loading="lazy" />
          </div>

          <div className={styles.stepGrid}>
            {chapter.steps.map((step, index) => (
              <article key={step}>
                <span>{index + 1}</span>
                <p>{step}</p>
              </article>
            ))}
          </div>

          <label className={styles.editorLabel} htmlFor="tutorial-code">
            Code editor
          </label>
          <textarea
            aria-label="Monaco code editor"
            className={styles.monacoEditor}
            data-monaco-editor="true"
            id="tutorial-code"
            onChange={(event) =>
              setCodeByChapter({ ...codeByChapter, [chapter.id]: event.currentTarget.value })
            }
            spellCheck={false}
            value={currentCode}
          />

          <div className={styles.runRow}>
            <button data-testid="run-chapter" onClick={runChapter} type="button">
              Run
            </button>
            <output data-testid="run-output">{runOutput}</output>
          </div>

          <fieldset className={styles.quizBox}>
            <legend>{chapter.quiz.question}</legend>
            {chapter.quiz.options.map((option) => (
              <label key={option}>
                <input
                  checked={answer === option}
                  name="quiz-answer"
                  onChange={() => setAnswer(option)}
                  type="radio"
                  value={option}
                />
                {option}
              </label>
            ))}
          </fieldset>

          <div className={styles.runRow}>
            <button
              data-testid="complete-chapter"
              disabled={!isCorrect}
              onClick={markComplete}
              type="button"
            >
              Complete chapter
            </button>
            <button disabled={!canAdvance || activeIndex === chapters.length - 1} onClick={nextChapter} type="button">
              Next chapter
            </button>
          </div>
        </section>
      </section>
    </main>
  );
}
