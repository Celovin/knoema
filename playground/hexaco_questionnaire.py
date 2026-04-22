"""Helpers for the IPIP-HEXACO-60 aligned questionnaire mode."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from statistics import mean
from typing import Literal

from knoema.types import PERSONALITY_NEUTRAL_DEFAULTS

HexacoDomain = Literal[
    "honesty_humility",
    "emotionality",
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "openness",
]

HEXACO_DOMAINS: tuple[HexacoDomain, ...] = (
    "honesty_humility",
    "emotionality",
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "openness",
)
QUESTIONNAIRE_RESPONSE_DEFAULT = 3
QUESTIONNAIRE_MODE_SLIDERS = "sliders"
QUESTIONNAIRE_MODE_HEXACO = "hexaco_questionnaire"

DOMAIN_LABELS = {
    "honesty_humility": {"ko": "Honesty-Humility 문항", "en": "Honesty-Humility items"},
    "emotionality": {"ko": "Emotionality 문항", "en": "Emotionality items"},
    "extraversion": {"ko": "Extraversion 문항", "en": "Extraversion items"},
    "agreeableness": {"ko": "Agreeableness 문항", "en": "Agreeableness items"},
    "conscientiousness": {
        "ko": "Conscientiousness 문항",
        "en": "Conscientiousness items",
    },
    "openness": {"ko": "Openness 문항", "en": "Openness items"},
}


@dataclass(frozen=True, slots=True)
class HexacoQuestionItem:
    item_id: str
    number: int
    domain: HexacoDomain
    prompt_en: str
    prompt_ko: str
    reverse_scored: bool

    @property
    def label(self) -> str:
        return f"Q{self.number:02d}"

    def prompt(self, language: str) -> str:
        return self.prompt_ko if language == "ko" else self.prompt_en


def questionnaire_mode_choices(language: str) -> list[tuple[str, str]]:
    if language == "ko":
        return [
            ("Trait 슬라이더", QUESTIONNAIRE_MODE_SLIDERS),
            ("IPIP-HEXACO-60 설문", QUESTIONNAIRE_MODE_HEXACO),
        ]
    return [
        ("Trait sliders", QUESTIONNAIRE_MODE_SLIDERS),
        ("IPIP-HEXACO-60 questionnaire", QUESTIONNAIRE_MODE_HEXACO),
    ]


def questionnaire_mode_label(language: str) -> str:
    return "성격 입력 모드" if language == "ko" else "Personality input mode"


def questionnaire_panel_label(language: str) -> str:
    return "IPIP-HEXACO-60 설문" if language == "ko" else "IPIP-HEXACO-60 questionnaire"


def questionnaire_intro_markdown(language: str) -> str:
    if language == "ko":
        return (
            "- 60문항, 1=전혀 아니다, 5=매우 그렇다.\n"
            "- 설문 모드가 켜져 있으면 응답이 현재 30개 trait 슬라이더에 자동 투영됩니다.\n"
            "- Apply 버튼은 투영 결과를 다시 계산할 때 사용할 수 있습니다.\n"
            "- 근거: Ashton, Lee, Goldberg (2007) public-domain IPIP-HEXACO scales."
        )
    return (
        "- 60 items, 1 = strongly disagree, 5 = strongly agree.\n"
        "- When questionnaire mode is active, responses automatically project into the current 30-trait slider profile.\n"
        "- Use Apply to refresh the projected trait profile on demand.\n"
        "- Basis: Ashton, Lee, Goldberg (2007) public-domain IPIP-HEXACO scales."
    )


def questionnaire_domain_label(domain: HexacoDomain, language: str) -> str:
    return str(DOMAIN_LABELS[domain][language])


def questionnaire_apply_label(language: str) -> str:
    return (
        "설문 trait 투영 새로고침"
        if language == "ko"
        else "Refresh questionnaire trait projection"
    )


def questionnaire_empty_summary(language: str) -> str:
    return (
        "아직 적용된 설문 프로필이 없습니다."
        if language == "ko"
        else "No questionnaire profile has been applied yet."
    )


def questionnaire_summary_markdown(scores: Mapping[str, float], language: str) -> str:
    lines = [
        "#### HEXACO 요약" if language == "ko" else "#### HEXACO summary",
        (
            "설문 응답을 6개 HEXACO 축으로 평균한 뒤 30개 trait slider로 투영했습니다."
            if language == "ko"
            else "Responses were averaged into the six HEXACO domains and projected into the 30-trait slider surface."
        ),
        "",
    ]
    for domain in HEXACO_DOMAINS:
        score = float(scores[domain])
        label = questionnaire_domain_label(domain, language)
        lines.append(f"- **{label}:** {score:.2f}")
    return "\n".join(lines)


def questionnaire_domain_items(domain: HexacoDomain) -> tuple[HexacoQuestionItem, ...]:
    return tuple(item for item in HEXACO_QUESTIONNAIRE_ITEMS if item.domain == domain)


def questionnaire_default_responses() -> dict[str, int]:
    return {item.item_id: QUESTIONNAIRE_RESPONSE_DEFAULT for item in HEXACO_QUESTIONNAIRE_ITEMS}


def score_hexaco_questionnaire(responses: Mapping[str, int | float]) -> dict[str, float]:
    per_domain: dict[str, list[float]] = {domain: [] for domain in HEXACO_DOMAINS}
    for item in HEXACO_QUESTIONNAIRE_ITEMS:
        raw_value = int(responses.get(item.item_id, QUESTIONNAIRE_RESPONSE_DEFAULT))
        if raw_value < 1 or raw_value > 5:
            raise ValueError(f"{item.item_id} must be between 1 and 5")
        normalized = (raw_value - 1) / 4
        if item.reverse_scored:
            normalized = 1.0 - normalized
        per_domain[item.domain].append(normalized)
    return {
        domain: round(mean(values), 3)
        for domain, values in per_domain.items()
    }


def derive_personality_from_questionnaire(
    responses: Mapping[str, int | float],
) -> dict[str, float]:
    scores = score_hexaco_questionnaire(responses)
    honesty = float(scores["honesty_humility"])
    emotionality = float(scores["emotionality"])
    extraversion = float(scores["extraversion"])
    agreeableness = float(scores["agreeableness"])
    conscientiousness = float(scores["conscientiousness"])
    openness = float(scores["openness"])

    derived = dict(PERSONALITY_NEUTRAL_DEFAULTS)
    derived.update(
        {
            "openness": openness,
            "conscientiousness": conscientiousness,
            "extraversion": extraversion,
            "agreeableness": agreeableness,
            "neuroticism": emotionality,
            "honesty_humility": honesty,
            "machiavellianism": _clamp(1.0 - honesty),
            "narcissism": _clamp((0.6 * (1.0 - honesty)) + (0.4 * extraversion)),
            "psychopathy": _clamp(
                (0.55 * (1.0 - honesty))
                + (0.25 * (1.0 - emotionality))
                + (0.20 * (1.0 - agreeableness))
            ),
            "sadism": _clamp(
                (0.45 * (1.0 - agreeableness))
                + (0.35 * (1.0 - honesty))
                + (0.20 * (1.0 - emotionality))
            ),
            "kantianism": _clamp((0.65 * honesty) + (0.35 * agreeableness)),
            "humanism": _clamp(
                (0.45 * honesty) + (0.35 * agreeableness) + (0.20 * emotionality)
            ),
            "faith_in_humanity": _clamp(
                (0.35 * agreeableness) + (0.35 * honesty) + (0.30 * emotionality)
            ),
            "risk_tolerance": _clamp(
                (0.45 * extraversion) + (0.30 * openness) + (0.25 * (1.0 - emotionality))
            ),
            "locus_of_control": _clamp(
                (0.45 * conscientiousness)
                + (0.35 * extraversion)
                + (0.20 * (1.0 - emotionality))
            ),
            "need_for_cognition": _clamp((0.65 * openness) + (0.35 * conscientiousness)),
            "trait_empathy": _clamp(
                (0.50 * emotionality) + (0.25 * agreeableness) + (0.25 * honesty)
            ),
            "care_harm": _clamp(
                (0.45 * emotionality) + (0.30 * agreeableness) + (0.25 * honesty)
            ),
            "fairness": _clamp((0.70 * honesty) + (0.30 * agreeableness)),
            "binding_morals": _clamp(
                (0.45 * conscientiousness) + (0.30 * honesty) + (0.25 * agreeableness)
            ),
            "self_direction": _clamp((0.60 * openness) + (0.40 * extraversion)),
            "stimulation": _clamp((0.60 * openness) + (0.40 * extraversion)),
            "hedonism": _clamp(
                (0.50 * extraversion) + (0.30 * openness) + (0.20 * (1.0 - conscientiousness))
            ),
            "achievement": _clamp((0.60 * conscientiousness) + (0.40 * extraversion)),
            "power": _clamp((0.55 * extraversion) + (0.45 * (1.0 - honesty))),
            "security": _clamp((0.60 * emotionality) + (0.40 * conscientiousness)),
            "conformity": _clamp((0.55 * conscientiousness) + (0.45 * agreeableness)),
            "tradition": _clamp(
                (0.50 * conscientiousness) + (0.30 * honesty) + (0.20 * emotionality)
            ),
            "benevolence": _clamp(
                (0.50 * agreeableness) + (0.30 * honesty) + (0.20 * emotionality)
            ),
            "universalism": _clamp((0.40 * openness) + (0.35 * honesty) + (0.25 * agreeableness)),
        }
    )
    return {field_name: round(float(value), 3) for field_name, value in derived.items()}


def questionnaire_domain_counts() -> dict[str, int]:
    return dict(Counter(item.domain for item in HEXACO_QUESTIONNAIRE_ITEMS))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _domain_items(
    domain: HexacoDomain,
    start_number: int,
    prompts: list[tuple[str, str, bool]],
) -> tuple[HexacoQuestionItem, ...]:
    return tuple(
        HexacoQuestionItem(
            item_id=f"q{start_number + offset:02d}",
            number=start_number + offset,
            domain=domain,
            prompt_en=prompt_en,
            prompt_ko=prompt_ko,
            reverse_scored=reverse_scored,
        )
        for offset, (prompt_en, prompt_ko, reverse_scored) in enumerate(prompts)
    )


HEXACO_QUESTIONNAIRE_ITEMS = (
    _domain_items(
        "honesty_humility",
        1,
        [
            ("I avoid flattering people just to get favors.", "이득을 얻으려고 아첨하지 않는다.", False),
            ("I would bend rules if I could benefit without being caught.", "들키지 않는다면 규칙을 굽혀도 된다고 본다.", True),
            ("I speak plainly about my motives.", "내 의도를 솔직하게 말하는 편이다.", False),
            ("I like showing status with expensive symbols.", "비싼 상징물로 지위를 드러내고 싶다.", True),
            ("I return extra change when a cashier makes a mistake.", "거스름돈을 더 받으면 돌려준다.", False),
            ("I exaggerate achievements to impress people.", "사람들을 놀라게 하려고 성과를 부풀린다.", True),
            ("I feel uncomfortable taking more credit than I earned.", "내가 한 일보다 더 큰 공을 받으면 불편하다.", False),
            ("I enjoy using charm to control outcomes.", "결과를 통제하려고 매력을 전략적으로 사용한다.", True),
            ("I see myself as no better than most people.", "나는 대부분의 사람들보다 특별히 낫지 않다고 본다.", False),
            ("Power and luxury matter a lot to me.", "권력과 사치가 매우 중요하다.", True),
        ],
    )
    + _domain_items(
        "emotionality",
        11,
        [
            ("I worry about loved ones when they are late.", "가까운 사람이 늦으면 쉽게 걱정한다.", False),
            ("Risky situations rarely bother me.", "위험한 상황도 거의 신경 쓰이지 않는다.", True),
            ("I get anxious before uncertain outcomes.", "불확실한 결과를 앞두면 불안해진다.", False),
            ("I can sleep easily even when serious problems are unresolved.", "큰 문제가 남아 있어도 쉽게 잠든다.", True),
            ("I feel strong sympathy when others are hurting.", "다른 사람이 힘들어하면 깊이 공감한다.", False),
            ("I stay detached when people around me are distressed.", "주변 사람이 괴로워도 거리를 둔다.", True),
            ("I seek reassurance when circumstances feel unstable.", "상황이 불안정하면 안심시켜 줄 사람을 찾는다.", False),
            ("I recover from shocks without much emotional residue.", "충격적인 일을 겪어도 감정이 오래 남지 않는다.", True),
            ("Sudden threats make me cautious quickly.", "갑작스러운 위협에 빠르게 조심스러워진다.", False),
            ("I remain unshaken in situations that frighten most people.", "대부분의 사람이 무서워하는 상황에서도 흔들리지 않는다.", True),
        ],
    )
    + _domain_items(
        "extraversion",
        21,
        [
            ("I start conversations with new people easily.", "처음 보는 사람과도 쉽게 대화를 시작한다.", False),
            ("I keep to myself at social gatherings.", "사교 모임에서는 혼자 있으려는 편이다.", True),
            ("I enjoy being the center of a lively discussion.", "활발한 대화의 중심이 되는 것을 즐긴다.", False),
            ("I avoid taking visible leadership roles.", "눈에 띄는 리더 역할을 피한다.", True),
            ("My energy rises when many people are around.", "사람이 많아지면 에너지가 올라간다.", False),
            ("I speak softly even when I have something important to say.", "중요한 말이 있어도 작게 말하는 편이다.", True),
            ("I find it easy to act confidently in a new room.", "낯선 자리에서도 자신감 있게 행동한다.", False),
            ("I prefer letting others carry the conversation.", "대화는 다른 사람이 이끌게 두는 편이다.", True),
            ("I laugh and show enthusiasm openly.", "웃음과 열정을 겉으로 잘 드러낸다.", False),
            ("Social attention drains me quickly.", "사람들의 관심을 받으면 금방 지친다.", True),
        ],
    )
    + _domain_items(
        "agreeableness",
        31,
        [
            ("I forgive small mistakes without much trouble.", "작은 실수는 쉽게 용서한다.", False),
            ("I hold grudges for a long time.", "서운한 일을 오래 붙잡고 있는 편이다.", True),
            ("I try to soften conflict before it grows.", "갈등이 커지기 전에 누그러뜨리려 한다.", False),
            ("I enjoy proving people wrong in arguments.", "논쟁에서 상대가 틀렸음을 드러내는 일이 즐겁다.", True),
            ("I stay patient when others are slow or clumsy.", "상대가 느리거나 서툴러도 참는 편이다.", False),
            ("I snap back when someone annoys me.", "누가 거슬리면 바로 날카롭게 받아친다.", True),
            ("I look for compromise in tense situations.", "긴장된 상황에서는 타협점을 찾는다.", False),
            ("I feel justified retaliating when offended.", "기분이 상하면 되갚아도 된다고 느낀다.", True),
            ("I try to assume good intent before judging others.", "남을 판단하기 전에 좋은 의도를 먼저 가정한다.", False),
            ("I can be harsh when correcting someone.", "누군가를 바로잡을 때 매몰차게 말할 수 있다.", True),
        ],
    )
    + _domain_items(
        "conscientiousness",
        41,
        [
            ("I finish tasks before relaxing.", "쉬기 전에 해야 할 일을 끝내는 편이다.", False),
            ("I leave important work until the last minute.", "중요한 일을 마지막까지 미룬다.", True),
            ("I keep my materials organized.", "자료와 물건을 정리해 두는 편이다.", False),
            ("My plans are usually loose and unfinished.", "계획이 대체로 느슨하고 미완으로 남는다.", True),
            ("I check details carefully before submitting work.", "결과물을 내기 전에 세부를 꼼꼼히 확인한다.", False),
            ("I get distracted and abandon routines easily.", "쉽게 산만해져서 루틴을 포기한다.", True),
            ("I follow through even when a task becomes boring.", "일이 지루해져도 끝까지 해낸다.", False),
            ("I skip preparation and rely on improvising.", "준비를 건너뛰고 즉흥적으로 처리한다.", True),
            ("I prefer a clear schedule for important goals.", "중요한 목표에는 분명한 일정이 필요하다.", False),
            ("I make careless errors when rushing.", "급하면 부주의한 실수를 한다.", True),
        ],
    )
    + _domain_items(
        "openness",
        51,
        [
            ("I enjoy exploring unusual ideas.", "낯선 아이디어를 탐색하는 일이 즐겁다.", False),
            ("Abstract discussions feel pointless to me.", "추상적인 대화는 별 의미가 없다고 느낀다.", True),
            ("Art, music, or literature often pull my attention.", "예술, 음악, 문학에 자주 끌린다.", False),
            ("I prefer familiar answers over imaginative ones.", "상상력 있는 답보다 익숙한 답이 좋다.", True),
            ("I like learning about cultures unlike my own.", "나와 다른 문화에 대해 배우는 것을 좋아한다.", False),
            ("I resist changing my views when I meet new evidence.", "새로운 근거를 봐도 관점을 잘 바꾸지 않는다.", True),
            ("I enjoy experimenting with new ways of doing things.", "새로운 방식으로 시도해 보는 일을 좋아한다.", False),
            ("I am not very interested in creative hobbies.", "창의적인 취미에는 큰 관심이 없다.", True),
            ("I look for patterns and meanings others miss.", "다른 사람이 놓친 패턴과 의미를 찾으려 한다.", False),
            ("Novel perspectives rarely feel appealing to me.", "새로운 관점은 별로 끌리지 않는다.", True),
        ],
    )
)


__all__ = [
    "DOMAIN_LABELS",
    "HEXACO_DOMAINS",
    "HEXACO_QUESTIONNAIRE_ITEMS",
    "QUESTIONNAIRE_MODE_HEXACO",
    "QUESTIONNAIRE_MODE_SLIDERS",
    "QUESTIONNAIRE_RESPONSE_DEFAULT",
    "HexacoDomain",
    "HexacoQuestionItem",
    "derive_personality_from_questionnaire",
    "questionnaire_apply_label",
    "questionnaire_default_responses",
    "questionnaire_domain_counts",
    "questionnaire_domain_items",
    "questionnaire_domain_label",
    "questionnaire_empty_summary",
    "questionnaire_intro_markdown",
    "questionnaire_mode_choices",
    "questionnaire_mode_label",
    "questionnaire_panel_label",
    "questionnaire_summary_markdown",
    "score_hexaco_questionnaire",
]
