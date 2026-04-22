# CAT-28: Character Archetype Taxonomy (Personality, Tier 5)

Pedagogical archetype set derived from the published Japanese-origin character typology tradition widely discussed in academic anime / manga / visual-culture scholarship. CAT-28 is distinct from the criminology tiers (Tier 1 archetypes, Tier 2 historical) in both purpose and provenance: it exists to add personality-level behavioral diversity to replay overlays for research and teaching scenarios, not to model offender behavior.

## Scope

- 22 single archetypes (original planned): single-trait cognitive / emotional patterns.
- 6 composite archetypes (original planned): broader personality gestalt profiles.
- This directory ships the full **28 archetype** CAT-28 set: 22 single archetypes and 6 composite gestalt profiles.

## Attribution and Derivation

The CAT-28 names (`tsundere`, `kuudere`, etc.) are taxonomy terms documented in the academic corpus on Japanese otaku culture (see `CITATION.md`). They are not proprietary to any single studio, game, or companion product. The behavioral descriptions in each yaml are written independently from general literature characterizations; they are not transcribed from any specific proprietary character bible.

For any agent outside this repository that needs to verify the derivation: each archetype yaml lists `literature_sources` with at least two academic references, and the composite bibliography in `CITATION.md` is the authoritative source list.

## Not Included

- Character names from commercial companion products, games, or visual novels.
- Cross-axis personality codings (e.g., Enneagram, MBTI, Big Five numeric ratings). These are not part of the academic taxonomy tradition.
- Emotion-tag conventions (`[emotion:TAG]` and similar) are simulation conventions used elsewhere in the Knoema engine but are NOT stored in this directory.
- Any training data, fine-tune weights, or generated dialogue samples.

## Usage in Replay Viewer

The replay viewer's "Inject archetype" dropdown groups CAT-28 under a separate header so operators can distinguish personality overlays from criminology overlays. Personality archetypes are labeled as pedagogical / research-only. They must not be mixed with Tier 1 / Tier 2 overlays on the same agent in a single replay frame.

## Ethical Boundaries

- No mapping from personality archetype to offender propensity. Personality archetypes are not criminal profiles.
- No real-person inference. Archetypes represent literature-documented fictional typologies, not categories that can be applied to identifiable individuals.
- No demographic targeting. Mobility and interaction rules encoded in each yaml are synthetic and not drawn from survey data on any real population.
