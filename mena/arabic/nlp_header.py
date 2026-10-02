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
