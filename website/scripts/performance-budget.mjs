import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../app/tutorial/TutorialClient.tsx", import.meta.url), "utf8");
const css = await readFile(new URL("../app/tutorial/tutorial.module.css", import.meta.url), "utf8");

const checks = {
  noThirdPartyScripts: !source.includes("<script"),
  imageCountBounded: (source.match(/image: "/g) || []).length <= 5,
  localStorageScoped: source.includes("knoema.tutorial.progress"),
  responsiveRules: css.includes("@media (max-width: 900px)") && css.includes("@media (max-width: 540px)"),
};

const passed = Object.values(checks).filter(Boolean).length;
const score = Math.round((passed / Object.keys(checks).length) * 100);

console.log(JSON.stringify({ score, checks }, null, 2));

if (score < 90) {
  throw new Error(`performance budget score below 90: ${score}`);
}
