def create_pattern(level=1):
    level = max(1, min(5, int(level)))
    sequence = ["blue", "gold", "rose", "teal"][:level + 1]
    return {"sequence": sequence, "next": sequence[0]}


def score_pattern(answer, expected):
    return 100 if answer == expected else 40