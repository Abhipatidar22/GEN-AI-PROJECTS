import datetime as dt
import random

def recommend(goals, last_mood=None, keywords=None):
    suggestions = []
    today = dt.date.today()

    # Base suggestions
    base = [
        "Take a 10-minute mindful walk today.",
        "Write three things you're grateful for.",
        "Plan one 25-minute deep work sprint.",
        "Drink water and take a short stretch break.",
        "Send a quick 'thank you' note to someone."
    ]
    suggestions.append(random.choice(base))

    # Goal-aware
    for g in goals[:3]:
        if g.get('status') != 'done':
            suggestions.append(f"Break goal '{g['title']}' into a 20-minute next step and schedule it today ({today}).")  

    # Mood-aware
    if last_mood is not None:
        if last_mood <= 2:
            suggestions.append("Low mood detected. Try a short breathing exercise: inhale 4s, hold 4s, exhale 6s, repeat x4.")
        elif last_mood >= 4:
            suggestions.append("You're on a roll! Use that energy to tackle a small but meaningful task now.")

    # Keyword-aware
    if keywords:
        suggestions.append(f"Since '{keywords[0]}' came up, read a 5-minute article or note about it and jot one takeaway.")

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for s in suggestions:
        if s not in seen:
            uniq.append(s); seen.add(s)
    return uniq
