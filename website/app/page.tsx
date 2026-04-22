import { headers } from "next/headers";
import LuvoireLanding from "../components/LuvoireLanding";

type Lang = "en" | "ko";

async function resolveInitialLang(): Promise<Lang> {
  const h = await headers();
  const country = (h.get("x-vercel-ip-country") || h.get("cf-ipcountry") || "").toUpperCase();
  if (country === "KR") return "ko";
  if (country && country !== "KR") return "en";
  const accept = (h.get("accept-language") || "").toLowerCase();
  if (/(^|[,;\s])ko\b/.test(accept)) return "ko";
  return "en";
}

export default async function Home() {
  const initialLang = await resolveInitialLang();
  return (
    <main>
      <LuvoireLanding initialLang={initialLang} />
    </main>
  );
}
