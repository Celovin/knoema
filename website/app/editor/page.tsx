import { EditorClient } from "./EditorClient";

export const metadata = {
  title: "Scenario Editor | Knoema Engine",
  description: "Drag agents, edit events, and export Knoema Scenario DSL YAML.",
};

export default function EditorPage() {
  return <EditorClient />;
}
