import re
from collections import Counter

# Simple rule-based sentiment and intent
POS_WORDS = set("""happy great awesome good love progress proud win positive confident calm energized motivated peaceful hopeful inspired grateful""".split())
NEG_WORDS = set("""sad bad terrible angry hate stuck anxious stressed worried tired frustrated lost hopeless overwhelmed bored guilty regret""".split())

INTENT_RULES = [
    (r"\b(goal|target|plan|milestone)\b", "goal_update"),
    (r"\b(feel|mood|emotion)\b", "mood_checkin"),
    (r"\b(help|advice|suggest|recommend)\b", "advice_request"),
    (r"\bjournal|reflect|reflection\b", "journal_entry"),
]

def simple_sentiment(text: str) -> float:
    words = re.findall(r"[a-zA-Z']+", (text or '').lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    score = (pos - neg) / max(1, (pos + neg))
    return round(score, 3)

def simple_intent(text: str) -> str:
    t = (text or '').lower()
    for pattern, label in INTENT_RULES:
        if re.search(pattern, t):
            return label
    return "general"

def extract_keywords(text: str, top_k=5):
    words = re.findall(r"[a-zA-Z']+", (text or '').lower())
    stop = set("""i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it
        its itself they them their theirs themselves what which who whom this that these those am is are was were be been being have
        has had having do does did doing a an the and but if or because as until while of at by for with about against between into
        through during before after above below to from up down in out on off over under again further then once here there when
        where why how all any both each few more most other some such no nor not only own same so than too very s t can will just
        don should now""".split())
    words = [w for w in words if w not in stop and len(w) > 2]
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_k)]
