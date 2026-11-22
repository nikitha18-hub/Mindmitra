def recommend_difficulty(recent_scores):
    """Return a gentle 1-5 difficulty based on caregiver/patient sessions."""
    if not recent_scores:
        return 1
    average = sum(recent_scores) / len(recent_scores)
    if average >= 85:
        return 4
    if average >= 65:
        return 3
    if average >= 40:
        return 2
    return 1