# FBI Organized Archetype Research

## Overview

The FBI organized archetype is a pedagogical profile derived from behavioral-science typologies developed for sexual homicide and later used in broader crime-scene classification. It is not a diagnosis and it is not a rule for identifying a person. In Knoema replay terms, the archetype represents a simulated agent whose behavior is deliberate, socially managed, and spatially planned. The relevant literature describes organization as a cluster of crime-scene and pre-offense features: planning, victim selection, controlled interaction, evidence management, and post-event movement. Later empirical work strongly qualifies the dichotomy, showing that organized features may be common while a clean organized/disorganized split is not well supported. The replay should therefore treat the archetype as a teaching label with explicit uncertainty rather than as a validated classifier.

## Primary sources

The Tier 1 organized archetype has no named-person primary file. Its closest primary-source foundation is the FBI Behavioral Science Unit interview and case-file program summarized in the 1986 and 1988 sexual homicide publications [C1, C2]. Those publications report how offender interviews, police records, autopsy records, and investigative files were synthesized into crime-scene categories. The Crime Classification Manual later standardized classification language for violent-crime investigation [C3]. For this repository, those sources are primary in the narrow sense that they are the originating operational texts for the typology, but they are not field measurements of a Korean urban environment. Any replay behavior derived from them is therefore encoded as a historical-literature archetype, not as a validated model of current public risk.

## Academic secondary sources

Five secondary sources are used to bound the archetype. Canter, Alison, Alison, and Wentink tested the organized/disorganized distinction with multidimensional scaling and found no distinct natural split across the variables they analyzed [C4]. Kocsis and colleagues tested related organized/disorganized concepts in arson and treated the typology as a hypothesis requiring validation rather than a settled fact [C5]. The Cambridge Handbook chapter on offender profiling frames profiling as an inference problem in forensic psychology, where action-to-characteristic claims require empirical support [C6]. Rossmo's geographic profiling monograph supplies the anchor-point and journey-to-crime language used in the replay grid, without implying that an organized agent can be located from a small synthetic trace [C7]. Cohen and Felson's routine activity paper supplies the convergence model used for replay events: motivated actor, suitable target, and absence of capable guardianship [C8].

## Behavioral analysis

### Victim profile

The organized archetype selects targets in a way that appears purposeful inside the simulation: isolated movement, predictable path, and limited nearby guardianship. That is a replay translation of crime-opportunity literature rather than a claim about real-world victim categories [C8]. The older FBI literature linked organized scenes to prior selection and controlled contact, but subsequent reviews caution that such features often overlap with other categories [C1, C4]. In the YAML profile, target criteria should be declarative and situational: low crowd density, repeated path exposure, and no guardian within one grid cell. Demographic claims are intentionally excluded because the replay is a pedagogical urban-flow demonstration, not a victimology prediction tool.

### Modus operandi

MO rules should encode pre-event scanning, approach-delay, withdrawal when a guardian is visible, and movement along edges of commercial zones. The FBI-derived source material associated organized behavior with planning and transport, but the empirical challenge is that "organized" behaviors may be widespread across cases rather than distinctive [C1, C4]. The replay therefore avoids weapon, injury, or forensic details. It models only abstract social movement: wait, scan, approach, abort, relocate. This keeps the profile within safe, non-operational simulation logic.

### Signature elements

The profile should not encode signature conduct. In offender-profiling literature, signature is often treated as expressive or psychologically meaningful, whereas MO is practical and adaptive. A demo replay does not need expressive details, and adding them would increase sensationalism without improving the stakeholder lesson. The YAML should instead include a negative rule: no graphic signature behavior, no real-world procedural advice, and no claims that the profile identifies a person.

### Geographic behavior

Organized archetype movement can be represented as multi-anchor mobility: home-like anchor, commercial observation anchor, and exit-route anchor. Rossmo's journey-to-crime work supports the vocabulary of anchor points, distance decay, and buffer zones [C7]. The replay grid translates this into edge preference and controlled loops around commercial cells. The agent may cross the full grid but should prefer cells that preserve exit options. That behavior is for visualization only and should not be described as a validated predictor.

### Temporal patterns

The agent should be most active during high-flow transition periods, because routine activity theory emphasizes convergence in time and space [C8]. In the demo, 7 p.m. represents evening commute and commercial activity. The profile may delay action while traffic is dense, then move when guardianship thins. No day-of-week or real Seoul incident inference should be encoded.

### Victim-offender interaction dynamics

The organized archetype should use controlled, low-salience interaction states: observe, shadow-at-distance, disengage, and relocate. The interaction model should never provide tactical instruction. It should be framed as a simulation of perceived opportunity and guardianship, using a pedagogical abstraction that criminology faculty can critique.

## Geographic profiling data

There is no direct quantitative geographic profile for this no-person archetype. The relevant data concept is methodological: geographic profiling assumes that repeated event locations can contain information about anchor points, search behavior, and distance decay [C7]. For the replay, the archetype's mobility radius is a bounded 3-6 cells from a commercial anchor, with occasional edge movement to represent route planning. This number is a visualization parameter. It is not imported from a measured offender population. The report should state that no external benchmark was run and no external location accuracy is claimed.

## Contemporary Seoul translation

The Seoul translation uses published work on Gangnam's modernist superblock and commercial formation [C9] plus Seoul CPTED research showing the relevance of lighting, CCTV, maintenance, and walking behavior to fear-of-crime outcomes [C10]. Whitechapel-style alleys are not used here; this archetype maps to modern commercial blocks, arterial roads, and interior side streets. The "commercial-zone" flag represents retail density and transit-adjacent footfall. The "guardian" role represents visible patrol, store workers, groups of pedestrians, and camera-lit spaces. The grid should show that an organized archetype is constrained by guardianship rather than empowered by it.

## Ethical considerations

The organized label has a contested scientific status. Canter and coauthors found that the dichotomy did not emerge as two clean clusters in their sample [C4]. That limitation must be visible in the profile notes and viewer ethics modal. The profile must not imply that social competence, planning, or calmness are suspicious traits. It must not be applied to a living person, a local Korean incident, or any contemporary named case. The safe educational use is to let instructors discuss how typologies can be useful as teaching scaffolds while still failing as hard classifiers.

Implementation should also keep the simulation reversible and inspectable. Every rule in the YAML should be a small declarative condition that can be read by a non-programmer: "if guardian within one cell, abort approach"; "if commercial cell is crowded, wait"; "if route is exposed, relocate to edge." These rules make the profile discussable in a classroom because the instructor can challenge each assumption. The profile should not include hidden weights, latent personality diagnoses, or probabilistic labels that make the output look more scientific than it is. The viewer should show the literature sources beside the profile and should state that no field trial, police validation, or external framework benchmark is implied.

The organized archetype should be used to teach false confidence as much as it teaches planning. Students and evaluators should be able to see that a coherent path can emerge from simple deterministic rules, and that coherence alone does not prove that a real person would behave that way. The replay's strongest proof is reproducibility: the same seed produces the same movement trace and the same hash. That is an engineering property, not a criminological truth. For public demos, the presenter should describe the profile as "a historically derived teaching overlay" and should avoid language such as "detects," "predicts," or "profiles real offenders."

The profile also needs cultural caution. Mapping a typology born in U.S. investigative practice onto a Seoul-inspired grid is an analogy across time, institutions, and urban form. Seoul's guardianship practices, CCTV saturation, pedestrian density, and commercial rhythms differ from the settings behind the older FBI publications. The YAML should therefore contain a Seoul translation note and not simply import U.S. behavioral labels. The model should make guardianship and environment visible, not individual suspicion.

## Citation appendix

[C1] Ressler, R. K., Burgess, A. W., Douglas, J. E., Hartman, C. R., & D'Agostino, R. B. (1986). Sexual Killers and Their Victims. Journal of Interpersonal Violence, 1(3), 288-308. DOI: 10.1177/088626086001003003.

[C2] Douglas, J. E., Burgess, A. W., Burgess, A. G., & Ressler, R. K. (1992). Crime Classification Manual. Lexington Books. ISBN: 9780787985011.

[C3] Douglas, J. E., Burgess, A. W., Ressler, R. K., & Hartman, C. R. (1988). Sexual Homicide: Patterns and Motives. Free Press. ISBN: 9780028740638.

[C4] Canter, D. V., Alison, L. J., Alison, E., & Wentink, N. (2004). The Organized/Disorganized Typology of Serial Murder: Myth or Model? Psychology, Public Policy, and Law, 10(3), 293-320. DOI: 10.1037/1076-8971.10.3.293.

[C5] Kocsis, R. N., Cooksey, R. W., & Irwin, H. J. (1998). Organised and disorganised criminal behaviour syndromes in arsonists. Psychiatry, Psychology and Law, 5(1), 117-130. DOI: 10.1080/13218719809524925.

[C6] Canter, D. (2010). Offender profiling. In J. M. Brown & E. A. Campbell (Eds.), The Cambridge Handbook of Forensic Psychology. Cambridge University Press. ISBN: 9780521701815.

[C7] Rossmo, D. K. (2000). Geographic Profiling. CRC Press. ISBN: 9780849381294.

[C8] Cohen, L. E., & Felson, M. (1979). Social Change and Crime Rate Trends: A Routine Activity Approach. American Sociological Review, 44(4), 588-608. DOI: 10.2307/2094589.

[C9] Kim, J. I. (2015). The birth of urban modernity in Gangnam, Seoul. arq: Architectural Research Quarterly, 19(4), 369-379. DOI: 10.1017/S1359135515000615.

[C10] Lee, J. S., Park, S., & Jung, S. (2016). Effect of crime prevention through environmental design measures on active living and fear of crime. Sustainability, 8(9), 872. DOI: 10.3390/su8090872.
