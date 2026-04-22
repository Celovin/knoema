import { EditorClient } from "./EditorClient";

export const metadata = {
  title: "Scenario Editor | Luvoire",
  description: "Drag agents, edit events, and export Luvoire Scenario DSL YAML.",
};

export default function EditorPage() {
  return <EditorClient />;
}
