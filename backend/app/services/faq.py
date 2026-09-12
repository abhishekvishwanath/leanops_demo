"""
Naive keyword-overlap FAQ matching — a mock for the real retrieval a Phase 6
LLM integration would do. Good enough to route the E0 "routine" cases in the
spec's escalation classification (section 5) to an approved answer.
"""
import re
from typing import List, Optional

from app.domain import FaqMatch, FaqRecord

MATCH_THRESHOLD = 0.2

_STOPWORDS = {
    "a", "an", "the", "is", "are", "can", "i", "we", "you", "to", "for",
    "of", "on", "in", "do", "does", "will", "and", "or", "my", "our",
}


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOPWORDS}


def find_best_match(message: str, faqs: List[FaqRecord]) -> Optional[FaqMatch]:
    message_words = _words(message)
    if not message_words:
        return None

    best: Optional[FaqMatch] = None
    for faq in faqs:
        faq_words = _words(faq.question)
        if not faq_words:
            continue
        overlap = len(message_words & faq_words)
        if overlap == 0:
            continue
        score = overlap / len(faq_words)
        if best is None or score > best.score:
            best = FaqMatch(faq_id=faq.faq_id, question=faq.question, answer=faq.approved_answer, score=score)

    if best and best.score >= MATCH_THRESHOLD:
        return best
    return None
