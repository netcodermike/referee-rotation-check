from collections import defaultdict
from re import fullmatch


def minute(value):
    if not isinstance(value, str) or not fullmatch(r"[0-9]{2}:[0-9]{2}", value):
        raise ValueError("times must use 24-hour HH:MM")
    hours, minutes = map(int, value.split(":"))
    if not (hours < 24 and minutes < 60) and value != "24:00":
        raise ValueError("time is outside the event day")
    return hours * 60 + minutes


def label(data, key):
    value = data[key]
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 80:
        raise ValueError(f"{key} must be a nonempty label of at most 80 characters")
    return value.strip()


def analyze(data):
    minimum = data["minimum_rest_minutes"]
    if type(minimum) is not int or not 0 <= minimum <= 720:
        raise ValueError("minimum_rest_minutes must be an integer from 0 through 720")
    raw = data["assignments"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 500:
        raise ValueError("enter 1 through 500 assignments")

    by_official = defaultdict(list)
    seen = set()
    for assignment in raw:
        official = label(assignment, "official")
        fixture = label(assignment, "fixture")
        start, end = minute(assignment["start"]), minute(assignment["end"])
        if end <= start:
            raise ValueError("end must be after start within the same event day")
        if (official, fixture) in seen:
            raise ValueError("each fixture can appear only once per official")
        seen.add((official, fixture))
        by_official[official].append((start, end, fixture))

    overlaps, short_breaks = [], []
    for official, assignments in sorted(by_official.items()):
        active = []
        last_end, last_fixture = None, None
        for start, end, fixture in sorted(assignments):
            active = [entry for entry in active if entry[0] > start]
            for active_end, active_fixture in active:
                overlaps.append({"official": official, "fixtures": [active_fixture, fixture],
                                 "overlap_minutes": min(active_end, end) - start})
            if not active and last_end is not None and start - last_end < minimum:
                short_breaks.append({"official": official, "after": last_fixture,
                                     "before": fixture, "rest_minutes": start - last_end})
            if last_end is None or end > last_end:
                last_end, last_fixture = end, fixture
            active.append((end, fixture))

    return {"official_count": len(by_official), "overlap_count": len(overlaps),
            "short_break_count": len(short_breaks), "minimum_rest_minutes": minimum,
            "overlaps": overlaps, "short_breaks": short_breaks}

if __name__ == "__main__":
    import json
    from pathlib import Path
    import sys
    try:
        path, = sys.argv[1:]
        result = analyze(json.loads(Path(path).read_text(encoding="utf-8")))
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        sys.exit(2)
