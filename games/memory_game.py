def create_round(familiar_words=None):
    words = familiar_words or ["Garden", "Family", "Music", "Home"]
    target = words[0]
    return {"prompt": "Which picture matches the familiar word?", "target": target, "choices": list(words)}


def score_answer(selected, target):
    return 100 if selected == target else 50