"""Normalize punctuation in user-facing dashboard content."""

import re

EM_DASH = re.compile(r"[ \t]*(?:\u2014|\\u2014|&mdash;|&#0*8212;|&#x0*2014;)[ \t]*", re.I)


def display_text(value):
    """Replace em dashes with a spaced hyphen, including in nested records."""
    if isinstance(value, str):
        return EM_DASH.sub(" - ", value)
    if isinstance(value, dict):
        return {display_text(key): display_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [display_text(item) for item in value]
    return value
