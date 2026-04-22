"use client";

import type { Dispatch, DragEvent } from "react";
import { createContext, useContext, useMemo, useReducer, useState } from "react";
import styles from "./editor.module.css";

type AgentTemplate = {
  id: string;
  name: string;
  role: string;
  values: string[];
  goals: string[];
};

type EditorAgent = AgentTemplate & {
  x: number;
  y: number;
};

type EditorEvent = {
  id: string;
  tick: number;
  label: string;
  description: string;
};

type EditorState = {
  scenarioId: string;
  title: string;
  category: string;
  location: string;
  selectedAgentId: string | null;
  agents: EditorAgent[];
  events: EditorEvent[];
};

type EditorAction =
  | { type: "load_template"; template: EditorState }
  | { type: "add_agent"; template: AgentTemplate; x: number; y: number }
  | { type: "select_agent"; agentId: string }
  | { type: "update_agent"; agentId: string; patch: Partial<AgentTemplate> }
  | { type: "update_scenario"; patch: Partial<Pick<EditorState, "title" | "location" | "category">> }
  | { type: "add_event" }
  | { type: "update_event"; eventId: string; patch: Partial<Omit<EditorEvent, "id">> };

const agentTemplates: AgentTemplate[] = [
  {
    id: "mentor",
    name: "Mentor",
    role: "Guides the next step",
    values: ["clarity", "patience"],
    goals: ["ask one useful question", "summarize the handoff"],
  },
  {
    id: "observer",
    name: "Observer",
    role: "Tracks context",
    values: ["fairness", "specificity"],
    goals: ["record the event", "name one risk"],
  },
  {
    id: "coordinator",
    name: "Coordinator",
    role: "Keeps people aligned",
    values: ["pace", "inclusion"],
    goals: ["assign a role", "confirm the schedule"],
  },
  {
    id: "newcomer",
    name: "Newcomer",
    role: "Needs orientation",
    values: ["confidence", "belonging"],
    goals: ["state one need", "choose a first task"],
  },
];

const templates: EditorState[] = [
  {
    scenarioId: "editor_school_lab",
    title: "School Lab Handoff",
    category: "school",
    location: "Luvoire Demo World > Scenario Editor > School Lab",
    selectedAgentId: "mentor_1",
    agents: [
      { ...agentTemplates[0], id: "mentor_1", x: 24, y: 42 },
      { ...agentTemplates[3], id: "newcomer_1", x: 66, y: 48 },
    ],
    events: [
      {
        id: "event_1",
        tick: 1,
        label: "Lab station opens",
        description: "The mentor explains the first measurement and checks readiness.",
      },
    ],
  },
  {
    scenarioId: "editor_workplace_handoff",
    title: "Remote Handoff",
    category: "workplace",
    location: "Luvoire Demo World > Scenario Editor > Remote Team",
    selectedAgentId: "coordinator_1",
    agents: [
      { ...agentTemplates[2], id: "coordinator_1", x: 32, y: 36 },
      { ...agentTemplates[1], id: "observer_1", x: 72, y: 58 },
    ],
    events: [
      {
        id: "event_1",
        tick: 1,
        label: "Shift handoff",
        description: "The coordinator writes the next owner and the observer records blockers.",
      },
    ],
  },
  {
    scenarioId: "editor_community_queue",
    title: "Community Queue Reset",
    category: "community",
    location: "Luvoire Demo World > Scenario Editor > Repair Cafe",
    selectedAgentId: "observer_1",
    agents: [
      { ...agentTemplates[1], id: "observer_1", x: 28, y: 52 },
      { ...agentTemplates[2], id: "coordinator_1", x: 70, y: 34 },
    ],
    events: [
      {
        id: "event_1",
        tick: 1,
        label: "Queue update",
        description: "The observer names the wait time and the coordinator assigns the next slot.",
      },
    ],
  },
];

const EditorDispatchContext = createContext<Dispatch<EditorAction> | null>(null);

function editorReducer(state: EditorState, action: EditorAction): EditorState {
  if (action.type === "load_template") {
    return cloneState(action.template);
  }
  if (action.type === "add_agent") {
    const nextIndex =
      state.agents.filter((agent) => agent.id.startsWith(action.template.id)).length + 1;
    const agent = {
      ...action.template,
      id: `${action.template.id}_${nextIndex}`,
      x: action.x,
      y: action.y,
    };
    return {
      ...state,
      selectedAgentId: agent.id,
      agents: [...state.agents, agent],
    };
  }
  if (action.type === "select_agent") {
    return { ...state, selectedAgentId: action.agentId };
  }
  if (action.type === "update_agent") {
    return {
      ...state,
      agents: state.agents.map((agent) =>
        agent.id === action.agentId ? { ...agent, ...action.patch } : agent,
      ),
    };
  }
  if (action.type === "update_scenario") {
    return { ...state, ...action.patch, scenarioId: slugify(action.patch.title ?? state.title) };
  }
  if (action.type === "add_event") {
    const nextIndex = state.events.length + 1;
    return {
      ...state,
      events: [
        ...state.events,
        {
          id: `event_${nextIndex}`,
          tick: nextIndex,
          label: `Checkpoint ${nextIndex}`,
          description: "Agents agree on one next step and record the reason.",
        },
      ],
    };
  }
  if (action.type === "update_event") {
    return {
      ...state,
      events: state.events.map((event) =>
        event.id === action.eventId ? { ...event, ...action.patch } : event,
      ),
    };
  }
  return state;
}

export function EditorClient() {
  const [state, dispatch] = useReducer(editorReducer, cloneState(templates[0]));
  const [exportStatus, setExportStatus] = useState("Ready");
  const selectedAgent = state.agents.find((agent) => agent.id === state.selectedAgentId) ?? null;
  const yaml = useMemo(() => buildYaml(state), [state]);
  const downloadHref = useMemo(
    () => `data:text/yaml;charset=utf-8,${encodeURIComponent(yaml)}`,
    [yaml],
  );

  return (
    <EditorDispatchContext.Provider value={dispatch}>
      <main className={styles.editorShell}>
        <section className={styles.headerBand}>
          <a className={styles.backLink} href="/">
            Luvoire
          </a>
          <div>
            <p className={styles.eyebrow}>Scenario editor</p>
            <h1>Build the run before the model speaks.</h1>
          </div>
          <label className={styles.templatePicker}>
            Template
            <select
              aria-label="Template"
              onChange={(event) =>
                dispatch({
                  type: "load_template",
                  template: templates[Number(event.currentTarget.value)],
                })
              }
            >
              {templates.map((template, index) => (
                <option key={template.scenarioId} value={index}>
                  {template.title}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className={styles.workbench} aria-label="Scenario editor workbench">
          <AgentPalette />
          <SceneCanvas agents={state.agents} selectedAgentId={state.selectedAgentId} />
          <PropertyInspector state={state} selectedAgent={selectedAgent} />
          <EventTimeline events={state.events} />
          <YamlPreview
            yaml={yaml}
            downloadHref={downloadHref}
            exportStatus={exportStatus}
            onPrepareExport={() => setExportStatus("Export ready")}
          />
        </section>
      </main>
    </EditorDispatchContext.Provider>
  );
}

function AgentPalette() {
  const dispatch = useEditorDispatch();
  return (
    <aside className={styles.palette} aria-label="Agent palette">
      <div>
        <p className={styles.eyebrow}>Agents</p>
        <h2>Drag a role into the scene.</h2>
      </div>
      <div className={styles.paletteList}>
        {agentTemplates.map((template) => (
          <button
            className={styles.paletteAgent}
            data-testid={`palette-${template.id}`}
            draggable
            key={template.id}
            onClick={() => dispatch({ type: "add_agent", template, x: 50, y: 50 })}
            onDragStart={(event) => {
              event.dataTransfer.setData("application/x-luvoire-agent", template.id);
              event.dataTransfer.effectAllowed = "copy";
            }}
            type="button"
          >
            <strong>{template.name}</strong>
            <span>{template.role}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

function SceneCanvas({
  agents,
  selectedAgentId,
}: {
  agents: EditorAgent[];
  selectedAgentId: string | null;
}) {
  const dispatch = useEditorDispatch();

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const templateId = event.dataTransfer.getData("application/x-luvoire-agent");
    const template = agentTemplates.find((candidate) => candidate.id === templateId);
    if (!template) {
      return;
    }
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = clamp(((event.clientX - bounds.left) / bounds.width) * 100, 10, 90);
    const y = clamp(((event.clientY - bounds.top) / bounds.height) * 100, 14, 86);
    dispatch({ type: "add_agent", template, x, y });
  }

  return (
    <section
      className={styles.scene}
      data-testid="scene-canvas"
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <div className={styles.sceneGrid} aria-hidden="true" />
      <div className={styles.sceneLegend}>
        <strong>Scene canvas</strong>
        <span>{agents.length} agents placed</span>
      </div>
      {agents.map((agent) => (
        <button
          className={`${styles.sceneAgent} ${
            selectedAgentId === agent.id ? styles.sceneAgentSelected : ""
          }`}
          data-testid={`agent-${agent.id}`}
          key={agent.id}
          onClick={() => dispatch({ type: "select_agent", agentId: agent.id })}
          style={{ left: `${agent.x}%`, top: `${agent.y}%` }}
          type="button"
        >
          <span>{agent.name}</span>
          <small>{agent.role}</small>
        </button>
      ))}
    </section>
  );
}

function PropertyInspector({
  state,
  selectedAgent,
}: {
  state: EditorState;
  selectedAgent: EditorAgent | null;
}) {
  const dispatch = useEditorDispatch();
  return (
    <aside className={styles.inspector} aria-label="Property inspector">
      <p className={styles.eyebrow}>Inspector</p>
      <label>
        Scenario title
        <input
          data-testid="scenario-title"
          onChange={(event) =>
            dispatch({ type: "update_scenario", patch: { title: event.currentTarget.value } })
          }
          value={state.title}
        />
      </label>
      <label>
        Location
        <input
          onChange={(event) =>
            dispatch({ type: "update_scenario", patch: { location: event.currentTarget.value } })
          }
          value={state.location}
        />
      </label>
      {selectedAgent ? (
        <div className={styles.agentFields} data-testid="agent-inspector">
          <label>
            Agent name
            <input
              data-testid="agent-name"
              onChange={(event) =>
                dispatch({
                  type: "update_agent",
                  agentId: selectedAgent.id,
                  patch: { name: event.currentTarget.value },
                })
              }
              value={selectedAgent.name}
            />
          </label>
          <label>
            Role
            <textarea
              data-testid="agent-role"
              onChange={(event) =>
                dispatch({
                  type: "update_agent",
                  agentId: selectedAgent.id,
                  patch: { role: event.currentTarget.value },
                })
              }
              value={selectedAgent.role}
            />
          </label>
        </div>
      ) : (
        <p>Select an agent to edit its name and role.</p>
      )}
    </aside>
  );
}

function EventTimeline({ events }: { events: EditorEvent[] }) {
  const dispatch = useEditorDispatch();
  return (
    <section className={styles.timeline} aria-label="Event timeline">
      <div className={styles.timelineHeader}>
        <div>
          <p className={styles.eyebrow}>Timeline</p>
          <h2>Sequence the checkpoints.</h2>
        </div>
        <button data-testid="add-event" onClick={() => dispatch({ type: "add_event" })} type="button">
          Add event
        </button>
      </div>
      <div className={styles.eventRail}>
        {events.map((event) => (
          <article className={styles.eventItem} key={event.id}>
            <span>Tick {event.tick}</span>
            <input
              aria-label={`Label for ${event.id}`}
              onChange={(changeEvent) =>
                dispatch({
                  type: "update_event",
                  eventId: event.id,
                  patch: { label: changeEvent.currentTarget.value },
                })
              }
              value={event.label}
            />
            <textarea
              aria-label={`Description for ${event.id}`}
              data-testid={`event-description-${event.id}`}
              onChange={(changeEvent) =>
                dispatch({
                  type: "update_event",
                  eventId: event.id,
                  patch: { description: changeEvent.currentTarget.value },
                })
              }
              value={event.description}
            />
          </article>
        ))}
      </div>
    </section>
  );
}

function YamlPreview({
  yaml,
  downloadHref,
  exportStatus,
  onPrepareExport,
}: {
  yaml: string;
  downloadHref: string;
  exportStatus: string;
  onPrepareExport: () => void;
}) {
  return (
    <aside className={styles.yamlPanel} aria-label="YAML preview">
      <div className={styles.yamlHeader}>
        <div>
          <p className={styles.eyebrow}>YAML</p>
          <h2>Export a validated shape.</h2>
        </div>
        <img
          alt="Luvoire benchmark branching figure"
          className={styles.evidenceFigure}
          src="/figures/branching.svg"
        />
      </div>
      <pre data-testid="yaml-preview">
        <code>{yaml}</code>
      </pre>
      <div className={styles.exportRow}>
        <button data-testid="prepare-export" onClick={onPrepareExport} type="button">
          Prepare YAML export
        </button>
        <a download="luvoire_scenario.yaml" href={downloadHref}>
          Download YAML
        </a>
        <span data-testid="export-status">{exportStatus}</span>
      </div>
    </aside>
  );
}

function useEditorDispatch() {
  const dispatch = useContext(EditorDispatchContext);
  if (!dispatch) {
    throw new Error("Editor dispatch is unavailable.");
  }
  return dispatch;
}

function buildYaml(state: EditorState) {
  const agentBlocks = state.agents
    .map(
      (agent, index) => `  - agent_id: ${agent.id}
    name: ${quoteYaml(agent.name)}
    age: ${24 + index}
    background: ${quoteYaml(`Synthetic editor agent. ${agent.role}`)}
    personality:
      openness: 0.62
      conscientiousness: 0.70
      extraversion: 0.48
      agreeableness: 0.72
      neuroticism: 0.24
    values: [${agent.values.join(", ")}]
    goals: [${agent.goals.join(", ")}]
    synthetic: true`,
    )
    .join("\n");
  const eventBlocks = state.events
    .map(
      (event) => `  - timestamp: "2026-06-01T${String(8 + event.tick).padStart(2, "0")}:00:00"
    event_type: editor.${slugify(event.label)}
    participants: [${state.agents.map((agent) => agent.id).join(", ")}]
    location: ${quoteYaml(state.location)}
    description: ${quoteYaml(event.description)}`,
    )
    .join("\n");

  return `schema_version: "1.0"
scenario_id: ${state.scenarioId}
title: ${quoteYaml(state.title)}
domain: academic_research
description: ${quoteYaml(`Fictional ${state.category} scenario exported from the web editor.`)}
seed: 20260649
tick_duration_minutes: 720
duration_days: 1
environment:
  start_time: "2026-06-01T08:00:00"
  location_path: [Luvoire Demo World, Scenario Editor, ${state.category}]
  conditions:
    editor_export: true
agents:
${agentBlocks}
events:
${eventBlocks}
metrics:
  - name: editor_review_score
    kind: score
    description: "Quality of the exported fictional scenario structure."
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
  sensitive_domain: false
  irb_notes: null
`;
}

function cloneState(template: EditorState): EditorState {
  return {
    ...template,
    agents: template.agents.map((agent) => ({ ...agent, values: [...agent.values], goals: [...agent.goals] })),
    events: template.events.map((event) => ({ ...event })),
  };
}

function quoteYaml(value: string) {
  return JSON.stringify(value);
}

function slugify(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48) || "editor_scenario";
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
