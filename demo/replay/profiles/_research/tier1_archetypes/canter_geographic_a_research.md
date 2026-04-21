# Canter Geographic Archetype A Research

## Overview

Canter Geographic Archetype A is a no-person profile derived from investigative psychology and geographic profiling literature. It represents a simulated commuter-style actor whose event locations remain inside a meaningful activity space but do not collapse to a single home point. This is a pedagogical archetype for showing how anchor points, search range, buffer zones, and routine routes can be discussed without naming a living person. The profile draws on Canter's investigative psychology work, Rossmo's geographic profiling monograph, and routine activity theory. In the replay, the archetype should move through a bounded commercial grid, prefer edges and paths over random wandering, and react to changing guardianship. It should not claim to solve cases or infer identity.

## Primary sources

The archetype is literature-derived, so it has no police file or court transcript. The primary conceptual sources are Canter's published investigative psychology books and the methodological literature on geographic profiling [C1, C2]. They are primary for this archetype because they define the vocabulary used in the YAML: anchor point, mobility radius, path preference, edge preference, commuter/marauder distinction, and distance decay. The replay uses these concepts as interface-visible teaching variables. It does not use crime-scene detail, suspect lists, or real incident coordinates.

## Academic secondary sources

Rossmo's Geographic Profiling provides the strongest monograph basis for spatial parameters and cautions [C2]. The Cambridge Handbook chapter on offender profiling situates Canter's work inside investigative psychology and emphasizes empirical inference [C3]. Comerford's scoping review of serial homicide geographic mobility is used to show that multiple typologies exist and that mobility labels should not be treated as settled universal categories [C4]. Cohen and Felson provide the convergence logic for events [C5]. Gangnam urban-modernity and Seoul CPTED studies supply the contemporary built-environment translation [C6, C7]. This source mix makes the profile spatial and pedagogical rather than biographical.

## Behavioral analysis

### Victim profile

The archetype does not encode victim demographics. It selects situational exposure: predictable movement through a commercial edge, low current guardian density, and repeated route overlap. Routine activity theory supports modeling target suitability as situational rather than intrinsic [C5]. The profile therefore expresses the idea "path convergence matters" without implying that any group is inherently vulnerable.

### Modus operandi

The MO is a sequence of movement rules: maintain an anchor, scan along a route, avoid saturated guardian cells, move through edge cells, and abandon a route when the heatmap shows excessive convergence. These are abstract path-planning rules. They do not describe weapons, surveillance methods, evasion methods, or real-world tactics. The purpose is to let viewers see how geographic profiling language appears in a synthetic movement trace.

### Signature elements

No signature behavior is encoded. Geographic profiling concerns spatial distribution and search behavior; it does not require expressive crime details. The YAML should state that signature simulation is excluded. This prevents the viewer from drifting into sensational content and keeps the profile useful for academic demonstration.

### Geographic behavior

The profile should use two anchor points: a primary commercial anchor and a secondary transit-edge anchor. It should maintain a 3-5 cell mobility radius most of the time and occasionally take a longer path to represent a commuter pattern. Rossmo's framework supports anchor-point and distance-decay concepts, while Comerford's review reminds users that mobility typologies vary across studies [C2, C4]. In the 20 by 20 grid, this becomes route preference along main-road and commercial edges.

### Temporal patterns

The profile is active during the 30-minute replay's early and middle segments, when commute and retail flows change quickly. It should not encode real Seoul crime times. The 7 p.m. timestamp is a demo anchor that makes routine activity concepts easy to see. Temporal logic should be expressed as "if crowd density falls and guardian count is low, move to edge cell."

### Victim-offender interaction dynamics

The interaction model is indirect. The archetype does not need a direct approach to demonstrate spatial reasoning. It can produce observations, route shifts, and aborted convergence events. This makes it suitable for criminology faculty demos because the discussion can focus on distance, opportunity, and guardianship rather than harmful interaction detail.

## Geographic profiling data

This archetype is not attached to a measured case series in this repository. It uses geographic profiling concepts: anchor points, distance decay, buffer zones, and commuter/marauder contrast [C2]. The replay parameters are synthetic: two anchors, 3-5 cell routine radius, edge preference, and reduced movement inside guardian-rich cells. The output hash and msgpack frames make the behavior reproducible, but reproducibility is not empirical validation. A future measured profile would require an independent dataset and a separate ethics review.

## Contemporary Seoul translation

Gangnam is used because the literature describes its planned modernity, superblocks, arterial roadways, commercial centers, and unequal urban form [C6]. Seoul CPTED research supports modeling lighting, CCTV, maintenance, and walking behavior as relevant environmental conditions [C7]. In the grid, main roads are blue-tinted corridors, commercial cells are teal-tinted blocks, and alleys are coral-tinted connectors. The archetype prefers path and edge cells to show how a spatial profile can be inspected visually. It should also become less active when a guardian marker enters the same cell cluster, reinforcing the capable-guardian lesson from routine activity theory [C5].

## Ethical considerations

Geographic profiling can be misunderstood as a person-finding machine. The profile must explicitly say that it is a classroom overlay, not an investigative tool. It must avoid real addresses, real incidents, and contemporary named people. Canter and Rossmo's methods are useful for discussing spatial reasoning, but the replay contains synthetic coordinates and synthetic agents. The viewer should show the ethics modal before injection because even abstract profiles can invite overinterpretation. The safest use is comparative: users can toggle the archetype and ask how changes in road layout, guardianship, or footfall alter path choices.

Implementation should expose the assumptions behind the path. The YAML can include mobility radius, anchor-point count, path preference, edge preference, and guardian sensitivity as readable fields. The viewer should render these as labels, not as hidden model coefficients. Instructors can then ask whether a two-anchor commuter model is plausible, whether an edge preference is too strong, or whether the commercial zone should be weighted differently. That transparency is more valuable than a sophisticated but opaque scoring formula.

The profile should also avoid a common geographic-profiling error: treating a small number of event points as a solved location problem. The replay's frames are deterministic and numerous, but they are generated by code, not observed from the world. A heatmap of synthetic cells can be useful for explaining how distance decay and guardianship interact; it cannot validate a real anchor point. The output hash proves only that the trace is reproducible. The report should keep that distinction visible.

Cultural translation requires additional restraint. Whitechapel, North American geographic profiling literature, and Seoul commercial districts differ in land use, transit density, policing, surveillance, and street culture. The profile maps concepts, not facts: "anchor" becomes a commercial cell, "path" becomes a main-road corridor, and "guardian" becomes patrol, peer presence, lighting, or verification support. This analogy is acceptable for pedagogy only if every profile panel states that no contemporary case is being modeled.

Finally, the archetype should be a good citizen inside the replay. It should never displace existing agents or change the committed msgpack base trace. It should be an additive overlay with a distinct triangle marker, so observers can separate base simulation from profile injection. That visual separation reinforces that the profile is a teaching layer rather than hidden ground truth.

The YAML should also preserve the difference between route explanation and route prediction. A classroom viewer can say "this is why the synthetic route moved through edge cells"; it should not say "this is where a real offender would be." That phrasing keeps the profile compatible with the ethics modal and with the no-fabricated-numbers policy used elsewhere in the repository. The profile is acceptable only because it is transparent, deterministic, and non-operational.

Any future measured extension belongs in a separate dataset-backed profile.

## Citation appendix

[C1] Canter, D. V. (1994). Criminal Shadows: Inside the Mind of the Serial Killer. HarperCollins. ISBN: 9780002552158.

[C2] Rossmo, D. K. (2000). Geographic Profiling. CRC Press. ISBN: 9780849381294.

[C3] Canter, D. (2010). Offender profiling. In J. M. Brown & E. A. Campbell (Eds.), The Cambridge Handbook of Forensic Psychology. Cambridge University Press. ISBN: 9780521701815.

[C4] Comerford, C. V. (2022). A Scoping Review of Serial Homicide Geographic Mobility Literature and Four Typologies. Homicide Studies, 26(4), 379-407. DOI: 10.1177/1088767921993506.

[C5] Cohen, L. E., & Felson, M. (1979). Social Change and Crime Rate Trends: A Routine Activity Approach. American Sociological Review, 44(4), 588-608. DOI: 10.2307/2094589.

[C6] Kim, J. I. (2015). The birth of urban modernity in Gangnam, Seoul. arq: Architectural Research Quarterly, 19(4), 369-379. DOI: 10.1017/S1359135515000615.

[C7] Lee, J. S., Park, S., & Jung, S. (2016). Effect of crime prevention through environmental design measures on active living and fear of crime. Sustainability, 8(9), 872. DOI: 10.3390/su8090872.

[C8] Reynald, D. M. (2011). Guarding Against Crime: Measuring Guardianship within Routine Activity Theory. Ashgate. ISBN: 9781409411765.
