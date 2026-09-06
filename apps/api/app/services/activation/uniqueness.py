"""The guard that stops day 3 from being day 1 with different punctuation.

The prompt is told every earlier message and told not to repeat itself, but a
prompt is a request, not a constraint. Five near-identical nudges is the exact
failure that makes someone mute the bot, so repetition is checked in code after
the model answers: same opener, or a suggestion made of the same words, is a
rejected draft. The caller retries once and skips the day rather than sending a
message the user has already read.
"""

#: Words compared when deciding two messages open the same way. Short enough
#: that a rephrased opener still collides, long enough that two different
#: sentences about the same tool do not.
OPENER_WORDS = 6
#: Jaccard overlap above which two suggestions are "the same suggestion".
MAX_SUGGESTION_OVERLAP = 0.6
#: Words carrying no topic signal, dropped before the overlap is computed so
#: two unrelated suggestions are not called duplicates for sharing "the".
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "get",
        "got",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "so",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "up",
        "want",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "will",
        "with",
        "would",
        "you",
        "your",
    ]
)


def _words(text: str) -> list[str]:
    """Lowercased alphanumeric words; punctuation and case never hide a repeat."""
    return ["".join(c for c in w if c.isalnum()) for w in text.lower().split()]


def opener(text: str) -> str:
    """The first :data:`OPENER_WORDS` meaningful words, normalised for comparison."""
    return " ".join([w for w in _words(text) if w][:OPENER_WORDS])


def suggestion_overlap(left: str, right: str) -> float:
    """Jaccard overlap of the content words of two suggestions, 0.0 to 1.0.

    Two empty suggestions overlap fully: an empty draft is not a new idea.
    """
    a = {w for w in _words(left) if w and w not in _STOPWORDS}
    b = {w for w in _words(right) if w and w not in _STOPWORDS}
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def repeats_earlier(
    first_bubble: str, suggestion: str, earlier: list[tuple[str, str]]
) -> str | None:
    """Why this draft repeats an earlier day, or ``None`` when it is new.

    ``earlier`` is ``(first_bubble, suggestion)`` for every message the sequence
    already sent, oldest first. Returns a short machine-readable reason so the
    retry prompt and the skip log can both name what went wrong.
    """
    this_opener = opener(first_bubble)
    for past_bubble, past_suggestion in earlier:
        if this_opener and this_opener == opener(past_bubble):
            return "same_opener"
        if suggestion_overlap(suggestion, past_suggestion) > MAX_SUGGESTION_OVERLAP:
            return "same_suggestion"
    return None
