"""Arabic NLP pipeline: normalization, tokenization, NER, and dialect detection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Dialect(str, Enum):
    """Supported Arabic dialect categories."""

    MSA = "msa"
    GULF = "gulf"
    EGYPTIAN = "egyptian"
    LEVANTINE = "levantine"
    MAGHREBI = "maghrebi"
    UNKNOWN = "unknown"


@dataclass
class Token:
    """A single Arabic token with linguistic metadata."""

    text: str
    lemma: str
    pos: str
    is_stop: bool = False
    start: int = 0
    end: int = 0


@dataclass
class NamedEntity:
    """A named entity extracted from Arabic text."""

    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class NLPResult:
    """Result container for the Arabic NLP pipeline."""

    original: str
    normalized: str
    tokens: List[Token] = field(default_factory=list)
    entities: List[NamedEntity] = field(default_factory=list)
    dialect: Dialect = Dialect.UNKNOWN
    dialect_scores: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# Arabic diacritics (tashkeel) to strip
_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]"
)

# Arabic-Indic digits to Western digits
_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_EASTERN_ARABIC_INDIC_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

# Alef variants -> bare alef
_ALEF_VARIANTS_RE = re.compile(r"[أإآٱ]")
# Teh marbuta -> heh
_TEH_MARBUTA_RE = re.compile(r"ة")
# Yeh variants -> yeh
_YEH_VARIANTS_RE = re.compile(r"[ىئ]")
# Tatweel (kashida) removal
_TATWEEL_RE = re.compile(r"\u0640")

# Common Arabic stop words
_STOP_WORDS: frozenset[str] = frozenset(
    """
    في من على إلى عن أن إن كان كانت التي الذي الذين هذا هذه ذلك تلك
    هو هي هم هن أنا نحن أنت أنتم أنتن ما لا لم لن أو و ثم قد بل لكن
    كل بعض غير بين حتى إذا كما حيث لدى دون حين عند مع أي أية ليس ليست
    له لها لهم لنا لكم به بها بهم بنا بكم فيه فيها فيهم فينا فيكم
    منه منها منهم مننا منكم عليه عليها عليهم علينا عليكم
    إليه إليها إليهم إلينا إليكم
    وهو وهي وهم ونحن فهو فهي
    وسوف فقد لقد إذ إذن لعل كأن ليت نعم لا بلى أجل
    يوم سنة شهر وقت حين الآن هنا هناك ثمة كيف ماذا لماذا متى أين
    أكثر أقل جدا فقط أيضا كذلك بعض غير بين خلال حول نحو لدى
    """.split()
)

# Simple lexicon for NER (production systems would use a trained model)
_ENTITY_LEXICON: Dict[str, List[str]] = {
    "PERSON": [
        "محمد", "أحمد", "علي", "فاطمة", "عائشة", "خالد", "سارة", "عمر",
        "يوسف", "مريم", "حسن", "حسين", "نورة", "عبدالله", "ريم",
        "محمد بن سلمان", "محمد بن راشد", "تميم بن حمد",
    ],
    "ORG": [
        "شركة", "مؤسسة", "بنك", "جامعة", "وزارة", "هيئة", "مستشفى",
    ],
    "LOC": [
        "الرياض", "جدة", "دبي", "أبوظبي", "الدوحة", "الكويت", "القاهرة",
        "عمان", "بيروت", "الدار البيضاء", "تونس", "الجزائر",
    ],
}

# Dialect markers
_DIALECT_MARKERS: Dict[str, List[str]] = {
    "gulf": ["شلون", "هال", "يبي", "ابغي", "ديرة", "هالحين", "والله"],
    "egyptian": ["ايه", "بقى", "كده", "دلوقتي", "عايز", "مش", "حاجة"],
    "levantine": ["شو", "كتير", "كتير", "كتير", "كتير", "كتير", "كتير"],
    "maghrebi": ["واش", "دابا", "هاد", "شي", "غادي", "بزاف"],
}


def normalize(text: str) -> str:
    """Normalize Arabic text."""
    text = _DIACRITICS_RE.sub("", text)
    text = _ALEF_VARIANTS_RE.sub("ا", text)
    text = _TEH_MARBUTA_RE.sub("ه", text)
    text = _YEH_VARIANTS_RE.sub("ي", text)
    text = _TATWEEL_RE.sub("", text)
    text = text.translate(_ARABIC_INDIC_DIGITS)
    text = text.translate(_EASTERN_ARABIC_INDIC_DIGITS)
    return text.strip()


def tokenize(text: str) -> List[Token]:
    """Tokenize Arabic text."""
    normalized = normalize(text)
    tokens: List[Token] = []
    for match in re.finditer(r"\S+", normalized):
        word = match.group()
        tokens.append(Token(
            text=word,
            lemma=word,
            pos="UNK",
            is_stop=word in _STOP_WORDS,
            start=match.start(),
            end=match.end(),
        ))
    return tokens


def detect_dialect(text: str) -> Tuple[Dialect, Dict[str, float]]:
    """Detect Arabic dialect from text."""
    normalized = normalize(text)
    scores: Dict[str, float] = {}
    for dialect, markers in _DIALECT_MARKERS.items():
        score = sum(1 for marker in markers if marker in normalized)
        scores[dialect] = score / max(len(markers), 1)
    best = max(scores, key=scores.get) if scores else "unknown"
    if best == "unknown" or scores.get(best, 0) == 0:
        return Dialect.UNKNOWN, scores
    return Dialect(best), scores


def extract_entities(text: str) -> List[NamedEntity]:
    """Extract named entities from Arabic text."""
    normalized = normalize(text)
    entities: List[NamedEntity] = []
    for label, lexicon in _ENTITY_LEXICON.items():
        for entity_text in lexicon:
            start = normalized.find(entity_text)
            if start >= 0:
                entities.append(NamedEntity(
                    text=entity_text,
                    label=label,
                    start=start,
                    end=start + len(entity_text),
                    confidence=0.8,
                ))
    return entities


def process(text: str) -> NLPResult:
    """Run the full NLP pipeline."""
    normalized = normalize(text)
    tokens = tokenize(text)
    entities = extract_entities(text)
    dialect, dialect_scores = detect_dialect(text)
    return NLPResult(
        original=text,
        normalized=normalized,
        tokens=tokens,
        entities=entities,
        dialect=dialect,
        dialect_scores=dialect_scores,
    )
