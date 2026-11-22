def create_round(level=1):
    level = max(1, min(5, int(level)))
    stars = level + 3
    return {
        "instruction": "Notice the one glowing star.",
        "stars": stars,
        "target": 1,
    }


def score_answer(selected, target):
    return 100 if int(selected) == int(target) else 40