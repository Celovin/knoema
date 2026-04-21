"""Pre-registration template library for the Playground."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PreregTemplate:
    template_id: str
    label_en: str
    label_ko: str
    title: str
    hypotheses: str
    design: str
    data_generation: str
    factor_design: str
    outcomes: str
    performance_metrics: str
    aggregation: str
    analysis: str
    planned_n: int
    power_test: str
    power_effect: float
    power_alpha: float
    power_target: float
    deviations: str = "No deviations recorded."


PREREG_TEMPLATES: tuple[PreregTemplate, ...] = (
    PreregTemplate(
        template_id="theory_of_mind_development",
        label_en="Theory of Mind development",
        label_ko="마음이론 발달",
        title="Theory of Mind development in deterministic social simulations",
        hypotheses=(
            "H1. Agents with higher perspective-taking and humanism scores will resolve false-belief conflicts more accurately.\n"
            "H2. Higher planning depth will increase belief-state consistency across repeated seeds."
        ),
        design=(
            "Run false-belief and coordination scenarios under fixed seeds, varying perspective-taking trait profiles and HTN planning depth."
        ),
        data_generation=(
            "Freeze scenario YAML, seed schedule, agent roster, and false-belief event injections before running all batches."
        ),
        factor_design="2 x 2 design: perspective-taking profile (low/high) by planning depth (off/on).",
        outcomes=(
            "Primary outcome: false-belief-consistent action rate.\n"
            "Secondary outcomes: belief repair latency, trust delta, and explanation consistency."
        ),
        performance_metrics="False-belief accuracy, plan completion rate, action diversity, and relationship coherence.",
        aggregation="Aggregate seed-level outcomes first, then compare scenario-level means with confidence intervals.",
        analysis=(
            "Use paired seed comparisons for planning depth and independent comparisons for trait profile. Report effect sizes and Holm-corrected p-values."
        ),
        planned_n=128,
        power_test="two_proportions",
        power_effect=0.35,
        power_alpha=0.05,
        power_target=0.8,
    ),
    PreregTemplate(
        template_id="trait_stability_over_time",
        label_en="Trait stability over time",
        label_ko="시간에 따른 trait 안정성",
        title="Trait stability and behavioral drift across repeated social runs",
        hypotheses=(
            "H1. Deterministic replay will preserve trait-action rank ordering across seed batches.\n"
            "H2. High-neuroticism agents will show larger late-phase behavioral drift under stressors."
        ),
        design="Repeated batch replay across fixed scenarios, comparing early and late tick windows.",
        data_generation="Use the same scenario YAML with fixed seed ranges and predeclared stressor injections.",
        factor_design="Within-run time window: early ticks versus late ticks; between-agent trait bands: low/mid/high.",
        outcomes="Primary outcome: trait-action rank stability.\nSecondary outcomes: late-phase drift, action entropy, and emotion variance.",
        performance_metrics="Spearman rank stability, action entropy, mean action rate, and PAD emotion dispersion.",
        aggregation="Compute per-seed stability first, then summarize across seeds and scenarios.",
        analysis="Estimate rank correlations and Mann-Whitney tests over drift scores with BH correction.",
        planned_n=150,
        power_test="paired_t",
        power_effect=0.4,
        power_alpha=0.05,
        power_target=0.8,
    ),
    PreregTemplate(
        template_id="group_polarization_dynamics",
        label_en="Group polarization dynamics",
        label_ko="집단 양극화 동역학",
        title="Group polarization dynamics under repeated agent interaction",
        hypotheses=(
            "H1. Homogeneous value clusters will polarize faster than mixed-value clusters.\n"
            "H2. Higher binding-morals profiles will increase within-group alignment and between-group distance."
        ),
        design="Compare homogeneous and mixed value-group scenarios with identical event timing and agent counts.",
        data_generation="Generate fixed rosters from value profile bands and replay each condition over the same seed schedule.",
        factor_design="2 x 2 design: value composition (homogeneous/mixed) by stressor intensity (low/high).",
        outcomes="Primary outcome: between-group relationship distance.\nSecondary outcomes: language alignment and action-type divergence.",
        performance_metrics="Trust modularity, action distribution divergence, conversation-thread alignment, and conflict action rate.",
        aggregation="Aggregate by seed and group pair before estimating condition-level effects.",
        analysis="Use chi-square tests for action distribution shifts and t-tests for relationship distance effects.",
        planned_n=160,
        power_test="independent_t",
        power_effect=0.45,
        power_alpha=0.05,
        power_target=0.85,
    ),
    PreregTemplate(
        template_id="moral_foundation_action_coupling",
        label_en="Moral foundation x action coupling",
        label_ko="도덕 기반과 행동 결합",
        title="Moral foundation and action coupling in social simulation logs",
        hypotheses=(
            "H1. Higher care/harm scores will increase support and de-escalation actions.\n"
            "H2. Higher fairness scores will increase norm-enforcement actions when resources are contested."
        ),
        design="Run contested-resource scenarios while varying moral-foundation trait vectors across agents.",
        data_generation="Freeze resource-conflict events, agent moral profiles, seed ranges, and action vocabulary before analysis.",
        factor_design="Trait bands for care/harm and fairness crossed with resource pressure level.",
        outcomes="Primary outcome: moral-consistent action probability.\nSecondary outcomes: target selection and relationship repair.",
        performance_metrics="Conditional action probability, Cohen's w, BH-adjusted q-values, and relationship delta.",
        aggregation="Pool event-level counts by seed and trait band before modeling.",
        analysis="Apply trait-action chi-square tests with Benjamini-Hochberg correction and report top bias signals.",
        planned_n=180,
        power_test="two_proportions",
        power_effect=0.3,
        power_alpha=0.05,
        power_target=0.85,
    ),
    PreregTemplate(
        template_id="schwartz_value_priority_emergence",
        label_en="Schwartz value priority emergence",
        label_ko="Schwartz 가치 우선순위 발현",
        title="Emergence of Schwartz value priorities through repeated interaction",
        hypotheses=(
            "H1. Self-direction and universalism will predict exploration and bridge-building actions.\n"
            "H2. Security and conformity will predict rule-following and risk-avoidant actions."
        ),
        design="Run multi-agent scenarios with predeclared Schwartz value profiles and fixed event schedules.",
        data_generation="Freeze agent values, location graph, social events, and seed ranges before generating logs.",
        factor_design="Between-agent value priority bands across self-direction, universalism, security, and conformity.",
        outcomes="Primary outcome: value-consistent action rate.\nSecondary outcomes: network centrality and trust accumulation.",
        performance_metrics="Action affinity score, relationship centrality, trust delta, and action entropy.",
        aggregation="Compute agent-level scores per seed, then compare value bands.",
        analysis="Use regression over predeclared value bands and report standardized coefficients with confidence intervals.",
        planned_n=144,
        power_test="independent_t",
        power_effect=0.45,
        power_alpha=0.05,
        power_target=0.8,
    ),
    PreregTemplate(
        template_id="cultural_variation_honesty_humility",
        label_en="Cultural variation in Honesty-Humility",
        label_ko="문화권별 Honesty-Humility 변이",
        title="Cultural variation in Honesty-Humility and cooperation outcomes",
        hypotheses=(
            "H1. Cultural-prior shifts in Honesty-Humility will change cooperation and deception-related action rates.\n"
            "H2. Effects will remain directionally stable after controlling for agent count and scenario type."
        ),
        design="Compare culturally shifted trait priors across matched scenarios and seed schedules.",
        data_generation="Freeze cultural-prior IDs, agent rosters, scenarios, and seeds before running all conditions.",
        factor_design="Cultural prior condition by scenario family, with matched seeds across all cells.",
        outcomes="Primary outcome: cooperation rate.\nSecondary outcomes: deception-like actions, trust delta, and conflict repair.",
        performance_metrics="Conditional action rates, trust change, relationship coherence, and reproducibility coefficient.",
        aggregation="Aggregate by seed, culture condition, and scenario before cross-condition comparison.",
        analysis="Use matched-seed comparisons and report effect sizes with caveats about synthetic cultural priors.",
        planned_n=160,
        power_test="paired_t",
        power_effect=0.4,
        power_alpha=0.05,
        power_target=0.8,
    ),
    PreregTemplate(
        template_id="memory_decay_retrieval_accuracy",
        label_en="Memory decay and retrieval accuracy",
        label_ko="기억 감쇠와 검색 정확도",
        title="Memory decay and retrieval accuracy in persistent agent memory",
        hypotheses=(
            "H1. Longer simulated delay will reduce retrieval accuracy for low-salience events.\n"
            "H2. Reflection and long-term retrieval will preserve decision-relevant events better than neutral observations."
        ),
        design="Replay memory-heavy scenarios with predeclared retrieval probes at multiple delay windows.",
        data_generation="Freeze memory probes, event salience labels, delay windows, and seed ranges before simulation.",
        factor_design="Delay window (short/medium/long) by event salience (low/high).",
        outcomes="Primary outcome: retrieval accuracy.\nSecondary outcomes: retrieval latency, hallucinated recall rate, and decision relevance.",
        performance_metrics="Recall@k, precision@k, hallucination rate, and memory-to-action citation rate.",
        aggregation="Aggregate probe-level scores by seed and delay window before comparison.",
        analysis="Use paired delay-window tests and report retrieval curves with confidence intervals.",
        planned_n=200,
        power_test="paired_t",
        power_effect=0.35,
        power_alpha=0.05,
        power_target=0.85,
    ),
    PreregTemplate(
        template_id="dark_tetrad_cooperation_rate",
        label_en="Dark Tetrad x cooperation rate",
        label_ko="Dark Tetrad와 협력률",
        title="Dark Tetrad trait profiles and cooperation rates in fictional simulations",
        hypotheses=(
            "H1. Higher Machiavellianism and psychopathy profiles will reduce cooperation under resource stress.\n"
            "H2. IRB-gated fictional scenarios will show stronger effects than neutral classroom scenarios."
        ),
        design="Use fictional, safety-gated scenarios with predeclared Dark Tetrad trait profiles and neutral controls.",
        data_generation="Freeze safety gate acknowledgement, fictional scenario IDs, trait profiles, seeds, and exclusion rules.",
        factor_design="Trait profile band by scenario sensitivity class, with matched seed schedules.",
        outcomes="Primary outcome: cooperation rate.\nSecondary outcomes: threat/refusal actions, target concentration, and trust loss.",
        performance_metrics="Cooperation probability, conflict action rate, target Gini index, and relationship delta.",
        aggregation="Aggregate by seed and trait band before interpreting any sensitive scenario result.",
        analysis="Use two-proportion tests with BH correction and report safety caveats before substantive interpretation.",
        planned_n=180,
        power_test="two_proportions",
        power_effect=0.3,
        power_alpha=0.05,
        power_target=0.85,
    ),
    PreregTemplate(
        template_id="agent_imitation_influence",
        label_en="Agent imitation and influence",
        label_ko="에이전트 모방과 영향력",
        title="Agent imitation and influence under social-learning enabled simulation",
        hypotheses=(
            "H1. High-status or high-centrality agents will be imitated more often after visible actions.\n"
            "H2. Social-learning enabled runs will converge faster than social-learning disabled controls."
        ),
        design="Compare matched scenarios with and without social-learning influence pathways.",
        data_generation="Freeze visible action events, agent centrality priors, seed ranges, and imitation detection rules.",
        factor_design="Social learning enabled/disabled by initial centrality band.",
        outcomes="Primary outcome: imitation event rate.\nSecondary outcomes: convergence speed, action diversity, and centrality change.",
        performance_metrics="Imitation count, time-to-convergence, entropy change, and network centrality shift.",
        aggregation="Aggregate imitation events by seed and source-agent centrality band.",
        analysis="Use paired-seed comparisons and event-count models with robust confidence intervals.",
        planned_n=144,
        power_test="paired_t",
        power_effect=0.45,
        power_alpha=0.05,
        power_target=0.8,
    ),
    PreregTemplate(
        template_id="conversation_coordination_patterns",
        label_en="Conversation coordination patterns",
        label_ko="대화 조율 패턴",
        title="Conversation coordination patterns in multi-agent social scenarios",
        hypotheses=(
            "H1. Higher agreeableness and conscientiousness will increase turn-taking regularity.\n"
            "H2. Stressor events will reduce coordination unless a high-trust bridge agent is present."
        ),
        design="Run conversation-heavy scenarios with matched seeds, varying trait profiles and bridge-agent presence.",
        data_generation="Freeze conversation scenarios, event injections, bridge-agent assignment, and seed ranges.",
        factor_design="Bridge agent present/absent by stressor condition and trait profile band.",
        outcomes="Primary outcome: turn-taking regularity.\nSecondary outcomes: response latency proxy, topic repair, and trust delta.",
        performance_metrics="Thread continuity, target alternation, topic repair rate, and conversation entropy.",
        aggregation="Aggregate thread metrics by seed and conversation dyad before condition-level analysis.",
        analysis="Use mixed seed-level summaries and report both quantitative metrics and representative anonymized traces.",
        planned_n=150,
        power_test="independent_t",
        power_effect=0.4,
        power_alpha=0.05,
        power_target=0.8,
    ),
)


def prereg_template_choices(language: str = "en") -> list[tuple[str, str]]:
    label_attr = "label_ko" if language == "ko" else "label_en"
    return [
        (getattr(template, label_attr), template.template_id)
        for template in PREREG_TEMPLATES
    ]


def prereg_template_by_id(template_id: str) -> PreregTemplate:
    for template in PREREG_TEMPLATES:
        if template.template_id == template_id:
            return template
    return PREREG_TEMPLATES[0]


__all__ = ["PREREG_TEMPLATES", "PreregTemplate", "prereg_template_by_id", "prereg_template_choices"]
