# Web Scenario Editor

The Phase 49 editor is a browser authoring surface for Scenario DSL drafts. Open `/editor` on the Next.js website to place agents on a scene canvas, edit their names and roles, sequence timeline checkpoints, preview generated YAML, and prepare a downloadable scenario file.

The editor starts with three templates: school lab handoff, remote workplace handoff, and community queue reset. Each template exports the same safety defaults used by the Scenario DSL validator: fictional agents, no real people, no forecasting, and no suspect scoring. Use `knoema validate <file>` after downloading a scenario to run the Python-side validator.

The state model uses React Context with a reducer so the palette, canvas, inspector, timeline, and YAML preview share one source of truth. The canvas supports drag-and-drop agent placement and click-to-add fallback behavior. The YAML preview updates immediately after title, agent, or event edits.

Local verification:

```powershell
cd C:\Users\admin\Projects\knoema\website
npm run build
npm run e2e
```
