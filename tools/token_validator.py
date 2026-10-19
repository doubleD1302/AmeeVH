#!/usr/bin/env python3
"""Token validator for Stella Sora localization."""

import re

TOKEN_REGEX = re.compile(
    r'(<[^>]+>|'               # HTML/RichText tags: <color=...>, </color>, <size=...>, <sprite=...>, etc.
    r'\{[0-9a-zA-Z_]+\}|'      # Placeholders: {0}, {1}, {name}, etc.
    r'&[0-9a-zA-Z_]+&|'        # Parameters: &Param1&, &Param2&, etc.
    r'#[0-9a-zA-Z_]+#|'        # Parameters: #1#, #2#, etc.
    r'##[0-9a-zA-Z_#]+##|'     # Potential tags
    r'\\[ntrfv])'              # Escape characters: \n, \t, etc.
)

def extract_tokens(text):
    if not text:
        return []
    # Find all tokens
    tokens = TOKEN_REGEX.findall(text)
    # Normalize tag names/attributes for comparison if needed, or exact match
    return sorted(tokens)

def test():
    sample = "Test <color=#ec6d21>{0}</color>？\n<size=36><color=#bd3059>(Give up &Param1&)</color></size>"
    tokens = extract_tokens(sample)
    print("Sample tokens:", tokens)

if __name__ == '__main__':
    test()
