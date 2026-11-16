"""Suggests which lost and found reports might be about the same object.

Plain word matching, no AI: a lost report and a found report are a possible match when they share
words in the title or description, and score higher when the category, place and date also agree.
Only public fields are used. The private verification detail is never read here.
"""

import re

from app.models.item import Item

MIN_SCORE = 5
MAX_MATCHES = 5
MAX_CANDIDATES = 200
DATE_WINDOW_DAYS = 14

STOPWORDS = {
    "the", "and", "for", "with", "was", "were", "has", "have", "had", "near", "found", "lost", "from",
    "that", "this", "its", "are", "not", "but", "you", "your", "our", "any", "all", "can", "who", "one",
    "very", "some", "left", "inside", "outside", "area", "around", "there", "their", "them", "then",
    "item", "items", "please", "seen", "saw", "got", "get", "she", "him", "her", "his", "off", "out",
}


def words(text: str) -> set[str]:
    """Lower-case words of three or more letters or digits, without everyday filler words."""
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in STOPWORDS}


def _same_place(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    return bool(a and b) and (a in b or b in a or bool(words(a) & words(b)))


def score(source: Item, other: Item) -> int:
    """How alike two reports are. Zero when they share no word at all."""
    source_title, other_title = words(source.title), words(other.title)
    source_all = source_title | words(source.description)
    other_all = other_title | words(other.description)

    shared = source_all & other_all
    if not shared:
        return 0
    title_hits = len(source_title & other_title)
    result = min(title_hits, 2) * 4
    result += min(len(shared) - title_hits, 3)  # words shared outside the two titles
    if source.category == other.category:
        result += 2
    if _same_place(source.location, other.location):
        result += 2
    if abs((source.event_date - other.event_date).days) <= DATE_WINDOW_DAYS:
        result += 1
    return result


def best_matches(source: Item, candidates: list[Item]) -> list[Item]:
    """The most alike reports first; ties go to the newest. Candidates must already be filtered."""
    scored = [(score(source, other), other) for other in candidates]
    scored = [(value, other) for value, other in scored if value >= MIN_SCORE]
    scored.sort(key=lambda pair: (pair[0], pair[1].created_at), reverse=True)
    return [other for _, other in scored[:MAX_MATCHES]]
