#!/usr/bin/env python3
"""Token shielding and validation module for Stella Sora Phase 2A."""

import re

TOKEN_REGEX = re.compile(
    r'('
    r'\x0b'
    r'|\n'
    r'|<color=[^>]+>'
    r'|</color>'
    r'|<sprite=[^>]+>'
    r'|<sprite\s+name=[^>]+>'
    r'|</?[a-zA-Z]+(?:=[^>]+)?>'
    r'|&Param\d+&'
    r'|\{[0-9a-zA-Z_]+\}'
    r'|##[^#\n\x0b<>]+(?:#[0-9]+)?#'
    r'|#[0-9]+#'
    r')'
)

def extract_tokens(text: str):
    """Extract all tokens in order."""
    if not text:
        return []
    return TOKEN_REGEX.findall(text)

def shield_tokens(text: str):
    """Replace tokens with placeholder [[TOK#]] and return shielded text and token list."""
    if not text:
        return "", []
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    shielded = TOKEN_REGEX.sub(repl, text)
    shielded = re.sub(r'[ \t]+', ' ', shielded).strip()
    return shielded, tokens

def unshield_tokens(shielded_text: str, tokens: list):
    """Restore tokens into shielded text cleanly without stripping newlines or punctuation."""
    def repl(m):
        idx = int(m.group(1))
        if idx < len(tokens):
            tok = tokens[idx]
            if tok in ('\x0b', '\n'):
                return tok
            return f" {tok} "
        return ""

    res = re.sub(r'[ \t]*\[\[\s*TOK(\d+)\s*\]\][ \t]*', repl, shielded_text)
    
    # Clean whitespace around formatting tags (horizontal whitespace only!)
    res = re.sub(r'(<color=[^>]+>)[ \t]+', r'\1', res)
    res = re.sub(r'[ \t]+(</color>)', r'\1', res)
    res = re.sub(r'(<color=[^>]+>)[ \t]*(\{.*?\}|&Param\d+&)[ \t]*(</color>)', r'\1\2\3', res)
    res = re.sub(r'[ \t]+(&Param\d+&)[ \t]+', r' \1 ', res)
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    res = re.sub(r'[ \t]+([,.:;?!])', r'\1', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})[ \t]+s\b', r'\1s', res)
    res = re.sub(r'(&Param\d+&)[ \t]+s\b', r'\1s', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})[ \t]*%', r'\1%', res)
    res = re.sub(r'(&Param\d+&)[ \t]*%', r'\1%', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res

def validate_token_preservation(orig_text: str, vi_text: str):
    """Validate that vi_text preserves 100% of tokens from orig_text (multiset equality)."""
    orig_toks = extract_tokens(orig_text)
    vi_toks = extract_tokens(vi_text)
    return sorted(orig_toks) == sorted(vi_toks), orig_toks, vi_toks
