"""
Pure utility functions — no UI, no DB imports.
"""


def direction_from_angle(angle_mean) -> str:
    """Derive traversal direction from the sign of the angle mean."""
    try:
        v = float(str(angle_mean).replace(",", "."))
        if v > 0:
            return "up"
        elif v < 0:
            return "down"
        else:
            return "flat"
    except (TypeError, ValueError):
        return "flat"


def to_float_or_none(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int_or_none(s) -> int | None:
    v = to_float_or_none(s)
    return int(v) if v is not None else None
