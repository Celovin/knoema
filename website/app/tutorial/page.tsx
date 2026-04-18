import type { Metadata } from "next";
import { TutorialClient } from "./TutorialClient";

export const metadata: Metadata = {
  title: "Interactive Tutorial | Knoema Engine",
  description: "Five hands-on Knoema lessons for agents, memory, scenarios, Theory of Mind, and deployment.",
  alternates: {
    canonical: "/tutorial",
  },
};

export default function TutorialPage() {
  return <TutorialClient />;
}
