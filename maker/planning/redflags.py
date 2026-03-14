from __future__ import annotations
from collections import Counter
from maker.config import PlanningConfig

def red_flag_reason(text: str, cfg: PlanningConfig) -> str | None:
    if len(text) > cfg.max_response_chars:
        return "too_long"
    if text.count("\n") > cfg.max_newlines:
        return "too_many_lines"
    lines = [line.strip().casefold() for line in text.splitlines() if line.strip()]
    if lines:
        counts = Counter(lines)
        if counts.most_common(1)[0][1] > cfg.max_repeat_line_count:
            return "repeated_lines"
    lowered = text.casefold()
    for phrase in cfg.forbid_phrases_casefold:
        if phrase in lowered:
            return "confusion_phrase"
    return None
