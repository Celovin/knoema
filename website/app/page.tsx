import { Architecture } from "../components/Architecture";
import { CTA } from "../components/CTA";
import { CodeDemo } from "../components/CodeDemo";
import { Hero } from "../components/Hero";
import { ThreeApplications } from "../components/ThreeApplications";

export default function Home() {
  return (
    <main>
      <Hero />
      <ThreeApplications />
      <CodeDemo />
      <Architecture />
      <CTA />
    </main>
  );
}
