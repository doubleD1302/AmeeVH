"""Copyable, PII-redacted error reports for Stella Sora Launcher v2.0.

``build_report`` turns an exception (or a known situation code) plus the launcher's
current state into one ``ErrorReport``: a plain-language explanation with concrete
steps for the dialog, a 7-cell structured context grid for ``SmartErrorDialog``, a
complete plain-text report for ``copy_text_native``, and JSON-serializable export.

Privacy: Windows profile paths (``%USERPROFILE%``), standalone usernames, inline URL
credentials (``user:pass@``), and URL query/fragment strings are stripped before any
text or JSON leaves this module.

100% pure Python (zero Qt / PySide6 imports).
"""
from __future__ import annotations

import ctypes
import getpass
import json
import logging
import math
import os
import platform
import re
import shutil
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import error_catalog, tls
from .config import LAUNCHER_VERSION
from .diagnostics import get_os_build_info, is_process_admin
from .game_detection import is_game_process_running
from .net_probe import format_probe
from .safety import atomic_json

log = logging.getLogger('launcher_v2.error_report')

_KNOWN_SCHEMES = ('https', 'http', 'file', 'ftps', 'ftp', 'wss', 'ws', 'ssh', 'git')
_MAILTO_SCHEMES = ('mailto', 'tel', 'urn', 'data', 'cid', 'sms', 'ssh', 'git')
_NEXT_PATH_OR_SCHEME = (
    r'(?:(?:https?|ftps?|wss?|ws|ssh|git|file)://|[A-Za-z][A-Za-z0-9+.-]{0,24}://|(?:mailto|tel|urn|data|cid|sms|ssh|git):[^\s:]'
    r'|[^A-Za-z\s\\/:*?"\'<>|\r\n,;(){\[\]}#]*://|[A-Za-z]:[\\/]|\\{2}|\\+Users(?=[\\/]|$)|/+Users(?=[\\/]|$)|%USERPROFILE%)'
)
_NEXT_PATH_OR_SCHEME_RE = re.compile(_NEXT_PATH_OR_SCHEME, re.IGNORECASE)

_FC_NOAT = r'[^\s\'"<>;,(){\[\]}\\\?#@:]'
_FC_PATH = r'[^\s\'"<>;,(){\[\]}\\\?#:@]'
_FC_PATH_APOS = r'[^\s"<>#,;(){\[\]}\\\?:@%]'
_F_NET_SCH = r'((?:https?|ftps?|wss?|ws|ssh|git)://)'
_F_AUTH_SIMPLE = r'[^\s\'"<>;,(){\[\]}\\\?#@/]+@'
_F_AUTH_APOS = (
    r'(?![\'"]?(?:mailto|tel|urn|data|cid|sms|ssh|git):)'
    r'[^\s"<>#,;(){\[\]}\\\?#@/]+@'
)
_F_BOUND_END = (
    r'[,;](?=' + _NEXT_PATH_OR_SCHEME + r'|$|[\s<>")\]}>])'
    r'|$|[\s<>")\]}>]|\'(?=$|[\s<>")\]}>,;])'
)
_F_BOUND = r'(?=' + _F_BOUND_END + r')'
_F_HP_SIMPLE = _FC_NOAT + r'+(?::\d+)?(?:/' + _FC_PATH + r'*)?'
_F_HP_APOS = _FC_NOAT + r'+(?::\d+)?(?:/(?:' + _FC_PATH_APOS + r'+(?<!\'))?)?'
_F_HP_Q_SIMPLE = _FC_NOAT + r'+(?=[/:?#])(?::\d+(?=[/?#]))?(?:/' + _FC_PATH + r'*(?=[?#]))?'
_F_HP_Q_APOS = _FC_NOAT + r'+(?=[/:?#])(?::\d+(?=[/?#]))?(?:/(?:' + _FC_PATH_APOS + r'+(?<!\'))?(?=[?#]))?'
_F_Q_SIMPLE = r'[?#][^\s\'"<>;,(){\[\]}\\]*'
_F_Q_APOS = r'[?#](?:[^\s"<>#,;(){\[\]}\\\':%]+(?<!\'))?'

_URL_FAST_AUTH_SIMPLE = re.compile(
    _F_NET_SCH + _F_AUTH_SIMPLE + r'(' + _F_HP_SIMPLE + r')(?:' + _F_Q_SIMPLE + r')?' + _F_BOUND,
    re.IGNORECASE,
)
_URL_FAST_QUERY_SIMPLE = re.compile(
    r'(' + _F_NET_SCH + _F_HP_Q_SIMPLE + r')' + _F_Q_SIMPLE + _F_BOUND,
    re.IGNORECASE,
)
_URL_FAST_AUTH_APOS = re.compile(
    _F_NET_SCH + _F_AUTH_APOS + r'(' + _F_HP_APOS + r')(?:' + _F_Q_APOS + r')?' + _F_BOUND,
    re.IGNORECASE,
)
_URL_FAST_QUERY_APOS = re.compile(
    r'(' + _F_NET_SCH + _F_HP_Q_APOS + r')' + _F_Q_APOS + _F_BOUND,
    re.IGNORECASE,
)
_URL_FAST_CHUNK = re.compile(r'[^\s\'"<>;,(){\[\]}\\\?#]+')
_FILE_FAST_CHUNK = re.compile(r'[^?\r\n\f\v"<>;,(){\[\]}#\\:\/]+')
_DASH_SPACE_RE = re.compile(r'[ \t]-+[ \t]')

_WIN_STOP_CHARS = r'\s\\/:*?"\'<>|\r\n\f\v,;(){\[\]}'
_POSIX_STOP_CHARS = r'\s/\\:*?"\'<>|\r\n\f\v,;(){\[\]}'

_STOP_LOOKAHEAD = (
    r'(?=[\\/*?"<>|\r\n\f\v,;(){\[\]}]|\'(?!\w)|\'(?=' + _NEXT_PATH_OR_SCHEME + r')|:(?!//)'
    r'|[ \t]+(?:[\\/*?"\'<>|\r\n\f\v,;(){\[\]}]|:(?!//)|' + _NEXT_PATH_OR_SCHEME + r'|$)'
    r'|$)'
)
_SPACE_STOP_LOOKAHEAD = _STOP_LOOKAHEAD
_SPACE_NEG_LOOKAHEAD = (
    r'(?=[A-Za-z0-9_]+(?=[ \t\\/,;\r\n]|$)|'
    r'(?!%USERPROFILE%|[^A-Za-z\s\\/:*?"\'<>|\r\n,;(){\[\]}#]+://|[A-Za-z]:[\\/]'
    r'|[A-Za-z][A-Za-z0-9+.-]{0,24}://|(?:mailto|tel|urn|data|cid|sms|ssh|git):[^\s:]'
    r'|\'(?:' + _NEXT_PATH_OR_SCHEME + r')))'
)

_UNREDACTED_GUARD = r'(?!%USERNAME%(?:[\\/\s:*?"\'<>|\r\n,;(){\[\]}]|[A-Za-z]:[\\/]|$))'
_APOS_JOIN = r'\'(?=[A-Za-z0-9_]+(?=[ \t\\/,;\r\n]|$)|(?=\w)(?!' + _NEXT_PATH_OR_SCHEME + r'))'

_WIN_WORD = r'[^' + _WIN_STOP_CHARS + r']+'
_POSIX_WORD = r'[^' + _POSIX_STOP_CHARS + r']+'
_WIN_WORD_APOS = r'(?:' + _APOS_JOIN + r')?' + _WIN_WORD + r'(?:' + _APOS_JOIN + _WIN_WORD + r')*'
_POSIX_WORD_APOS = r'(?:' + _APOS_JOIN + r')?' + _POSIX_WORD + r'(?:' + _APOS_JOIN + _POSIX_WORD + r')*'

_SEG_CC_STOP = r'\r\n\f\v\\/:*?"<>|,;(){\[\]}'
_SEG_SINGLE_CC = r'((?:\'(?=\w)|[^' + _SEG_CC_STOP + r' \t\'])[^' + _SEG_CC_STOP + r']*)'
_POSIX_SEG_SINGLE_CC = (
    r'((?:\'(?=\w)|\\\'(?=\w)|[^' + _SEG_CC_STOP + r' \t\'])'
    r'[^' + _SEG_CC_STOP + r']*(?:\\\'(?=\w)[^' + _SEG_CC_STOP + r']*)*)'
)
_FAST_WIN_CC = re.compile(
    r'((?:[A-Za-z]:(?:\\+|/(?!/))|%USERPROFILE%[\\/]+)Users[\\/]+)' + _UNREDACTED_GUARD + _SEG_SINGLE_CC,
    re.IGNORECASE,
)
_FAST_WIN_NESTED_CC = re.compile(
    r'((?:(?<!\\)\\\\|(?<![\\/])\\)Users[\\/]+)' + _UNREDACTED_GUARD + _SEG_SINGLE_CC,
    re.IGNORECASE,
)
_FAST_UNC_CC = re.compile(
    r'((?<!\\)\\{2,}[^\\/:*?"\'<>|\s\r\n,;(){\[\]}]+[\\/]+(?:[^\\/:*?"\'<>|\s\r\n,;(){\[\]}]+[\\/]+)?Users[\\/]+)'
    + _UNREDACTED_GUARD + _SEG_SINGLE_CC,
    re.IGNORECASE,
)
_FAST_POSIX_CC = re.compile(
    r'((?<![\\/])/+Users[\\/]+)' + _UNREDACTED_GUARD + _POSIX_SEG_SINGLE_CC,
    re.IGNORECASE,
)

_HAS_UNREDACTED_USERS = re.compile(
    r'Users[\\/]+' + _UNREDACTED_GUARD + r'(?:\'(?=\w)|\\\'(?=\w)|[^' + _WIN_STOP_CHARS + r'])',
    re.IGNORECASE,
)
_DRIVE_ROOT_SPLIT = re.compile(r'([A-Za-z]:(?:\\+|/(?!/))|%USERPROFILE%[\\/]+)', re.IGNORECASE)
_ADJACENT_PATH_SPLIT = re.compile(r'(?<![ \t])([ \t]+)(?=' + _NEXT_PATH_OR_SCHEME + r')', re.IGNORECASE)
_DELIM_RE = re.compile(r'[:*?"<>|\r\n,;(){\[\]}]')
_USERS_WIN_TAIL = re.compile(
    r'((?:(?<!\\)\\\\|(?<![\\/])[\\/]+)Users[\\/]+)'
    + _UNREDACTED_GUARD
    + r'(' + _WIN_WORD_APOS + r'(?:[ \t]+' + _WIN_WORD_APOS + r')*)',
    re.IGNORECASE,
)
_UNC_SPAN = re.compile(r'(?<!\\)\\{2,}(?:\?\\+UNC[\\/]+)?[^:*?"<>|\r\n,;(){\[\]}]+', re.IGNORECASE)
_USERS_UNC_TAIL = _USERS_WIN_TAIL
_USERS_ROOTED_SPAN = re.compile(r'(?<![\\/])\\Users[\\/]+[^:*?"<>|\r\n,;(){\[\]}]+', re.IGNORECASE)
_ROOTED_HEAD = re.compile(r'^(\\Users[\\/]+)(.*)$', re.IGNORECASE | re.DOTALL)
_USERS_POSIX_SPAN = re.compile(r'(?<![\\/])/+Users[\\/]+[^:*?"<>|\r\n,;(){\[\]}]+', re.IGNORECASE)
_POSIX_HEAD = re.compile(r'^(/+Users[\\/]+)(.*)$', re.IGNORECASE | re.DOTALL)
_POSIX_USER_SEG = re.compile(_POSIX_WORD_APOS)


def _match_scheme_before_sep(text: str, sep: int, min_pos: int) -> tuple[int, str]:
    i = sep
    limit = max(min_pos, sep - 25)
    while i > limit and (text[i - 1].isalnum() or text[i - 1] in '+.-'):
        i -= 1
    cand = text[i:sep]
    if not cand:
        return -1, ''
    lc = cand.lower()
    if cand[0].isalpha() and (i == 0 or not text[i - 1].isalnum()) and lc in _KNOWN_SCHEMES:
        return i, lc
    for sch in _KNOWN_SCHEMES:
        if lc.endswith(sch):
            return sep - len(sch), sch
    return -1, ''


def _has_auth_at_ahead(text: str, j: int, n: int) -> bool:
    k = j + 1
    limit = min(n, k + 256)
    while k < limit:
        c = text[k]
        if c == '@':
            return True
        if c.isspace() or c in '/?#}]),;"<>':
            return False
        k += 1
    return False


def _scan_net_or_query_end(
    text: str,
    start: int,
    n: int,
    paren: int = 0,
    bracket: int = 0,
    brace: int = 0,
    in_query: bool = False,
    saw_slash: bool = False,
) -> int:
    j = start
    chunk_match = _URL_FAST_CHUNK.match
    next_re = _NEXT_PATH_OR_SCHEME_RE.match
    while j < n:
        m = chunk_match(text, j)
        if m is not None:
            seg_end = m.end()
            if not saw_slash and '/' in text[j:seg_end]:
                saw_slash = True
            j = seg_end
            if j >= n:
                break
        ch = text[j]
        if ch.isspace() or ch in '<>':
            break
        if ch in '?#':
            in_query = True
            j += 1
            continue
        if ch in '([{':
            if next_re(text, j + 1) is not None:
                break
            if ch == '(':
                paren += 1
            elif ch == '[':
                bracket += 1
            else:
                brace += 1
            j += 1
            continue
        if ch == ')':
            if paren > 0:
                paren -= 1
                j += 1
                continue
            break
        if ch == ']':
            if bracket > 0:
                bracket -= 1
                j += 1
                continue
            break
        if ch == '}':
            if brace > 0:
                brace -= 1
                j += 1
                continue
            break
        if ch == '"':
            break
        if ch == "'":
            if j + 1 < n and next_re(text, j + 1) is not None:
                break
            nxt = text[j + 1] if j + 1 < n else ''
            if not nxt or nxt.isspace() or nxt in ',;)]}>"':
                break
            if nxt == ':':
                if not in_query and not saw_slash and _has_auth_at_ahead(text, j, n):
                    j += 1
                    continue
                break
            if nxt.isalnum() or nxt in '_~+-/@':
                j += 1
                continue
            if nxt == '%' and j + 3 < n and text[j + 2] in '0123456789abcdefABCDEF' and text[j + 3] in '0123456789abcdefABCDEF':
                j += 1
                continue
            if nxt == '&' and j + 2 < n and (text[j + 2].isalnum() or text[j + 2] in '_~%+-'):
                j += 1
                continue
            break
        if ch == '\\':
            if j + 1 < n and text[j + 1] == "'" and j + 2 < n:
                nxt2 = text[j + 2]
                if (
                    nxt2.isalnum()
                    or nxt2 in '_~+-/@'
                    or (nxt2 == ':' and not in_query and not saw_slash and _has_auth_at_ahead(text, j + 1, n))
                    or (nxt2 == '&' and j + 3 < n and (text[j + 3].isalnum() or text[j + 3] in '_~%+-'))
                ):
                    j += 2
                    continue
            break
        if ch in ';,':
            if j + 1 >= n:
                break
            nxt = text[j + 1]
            if nxt.isspace() or nxt in ')]}>"':
                break
            if nxt in '\'"([{' and next_re(text, j + 2) is not None:
                break
            if next_re(text, j + 1) is not None:
                break
            j += 1
            continue
        break
    return j


def _scan_file_url_end(text: str, body_start: int, n: int) -> tuple[int, int]:
    j = body_start
    paren = 0
    bracket = 0
    brace = 0
    saw_dash_space = False
    chunk_match = _FILE_FAST_CHUNK.match
    dash_search = _DASH_SPACE_RE.search
    next_re = _NEXT_PATH_OR_SCHEME_RE.match
    while j < n:
        ws_start = j
        m = chunk_match(text, j)
        if m is not None:
            seg = m.group(0)
            seg_end = m.end()
            if '%' in seg:
                up_idx = seg.lower().find('%userprofile%')
                if up_idx != -1:
                    stop = j + up_idx
                    if stop > j and text[stop - 1] in "'([{":
                        stop -= 1
                    while stop > j and text[stop - 1] in ' \t':
                        stop -= 1
                    return stop, j + up_idx
            if "'" in seg:
                slen = len(seg)
                apos_pos = seg.find("'")
                while apos_pos != -1:
                    abs_pos = j + apos_pos
                    if abs_pos + 1 < n and next_re(text, abs_pos + 1) is not None:
                        stop = abs_pos
                        while stop > j and text[stop - 1] in ' \t':
                            stop -= 1
                        return stop, abs_pos
                    nxt = text[abs_pos + 1] if abs_pos + 1 < n else ''
                    if not nxt or nxt.isspace() or nxt in ';)]}>"':
                        stop = abs_pos
                        while stop > j and text[stop - 1] in ' \t':
                            stop -= 1
                        return stop, abs_pos
                    apos_pos = seg.find("'", apos_pos + 1)
            if '-' in seg and dash_search(seg) is not None:
                saw_dash_space = True
            j = seg_end
            ws_start = j
            while ws_start > body_start and text[ws_start - 1] in ' \t':
                ws_start -= 1
            if j >= n:
                return ws_start, j
        ch = text[j]
        if ch in '\r\n\f\v<>|*"':
            return ws_start, j
        if ch == ':':
            if text[j:j + 3] == '://':
                sch_pos, _ = _match_scheme_before_sep(text, j, body_start)
                stop = sch_pos if sch_pos != -1 else j
                if stop > body_start and text[stop - 1] in "'([{":
                    stop -= 1
                while stop > body_start and text[stop - 1] in ' \t':
                    stop -= 1
                return stop, stop
            if j + 1 < n and text[j + 1] in ('\\', '/'):
                if j <= body_start + 3 and j > body_start and text[j - 1].isalpha() and (j - 1 == body_start or text[j - 2] == '/'):
                    j += 1
                    continue
                stop = j - 1 if (j > body_start and text[j - 1].isalpha()) else j
                if stop > body_start and text[stop - 1] in "'([{":
                    stop -= 1
                while stop > body_start and text[stop - 1] in ' \t':
                    stop -= 1
                return stop, stop
            if j + 1 >= n or text[j + 1].isspace():
                return ws_start, j
            j += 1
            continue
        if ch in '/\\':
            saw_dash_space = False
            j += 1
            continue
        if ch in '([{':
            if next_re(text, j + 1) is not None:
                return ws_start, j
            if ch == '(':
                paren += 1
            elif ch == '[':
                bracket += 1
            else:
                brace += 1
            j += 1
            continue
        if ch == ')':
            if paren > 0:
                paren -= 1
                j += 1
                continue
            return ws_start, j
        if ch == ']':
            if bracket > 0:
                bracket -= 1
                j += 1
                continue
            return ws_start, j
        if ch == '}':
            if brace > 0:
                brace -= 1
                j += 1
                continue
            return ws_start, j
        if ch == ';':
            return ws_start, j
        if ch == ',':
            if j + 1 >= n or text[j + 1].isspace() or text[j + 1] in ')]}>"':
                return ws_start, j
            if text[j + 1] in '\'"([{' and next_re(text, j + 2) is not None:
                return ws_start, j
            if next_re(text, j + 1) is not None:
                return ws_start, j
            j += 1
            continue
        if ch in '?#':
            if saw_dash_space or ws_start < j or j + 1 >= n or text[j + 1].isspace():
                return ws_start, j
            url_end = _scan_net_or_query_end(text, j + 1, n, paren=paren, bracket=bracket, brace=brace, in_query=True, saw_slash=True)
            return url_end, url_end
        return ws_start, j
    return j, j


def _redact_url_token(token: str) -> str:
    sep = token.find('://')
    if sep == -1:
        return token
    scheme = token[:sep + 3]
    rest = token[sep + 3:]
    q = rest.find('?')
    h = rest.find('#')
    if q != -1 or h != -1:
        cut = len(rest)
        if q != -1:
            cut = min(cut, q)
        if h != -1:
            cut = min(cut, h)
        rest = rest[:cut]
    slash = rest.find('/')
    auth = rest if slash == -1 else rest[:slash]
    path = '' if slash == -1 else rest[slash:]
    if '@' in auth:
        auth = auth.rsplit('@', 1)[1]
    return scheme + auth + path


def _redact_urls_linear(text: str) -> str:
    if '@' not in text and '?' not in text and '#' not in text:
        return text
    if '://' in text:
        first_trig = min(p for p in (text.find('@'), text.find('?'), text.find('#')) if p != -1)
        fpos = -1
        if 'file://' in text or (('f' in text or 'F' in text) and 'file://' in text.lower()):
            fpos = text.lower().find('file://')
        if fpos == -1 or fpos >= first_trig:
            start_scan = max(
                text.rfind(' ', 0, first_trig),
                text.rfind('\t', 0, first_trig),
                text.rfind('\n', 0, first_trig),
                text.rfind('\r', 0, first_trig),
            ) + 1
        else:
            start_scan = max(
                text.rfind('\n', 0, first_trig),
                text.rfind('\r', 0, first_trig),
            ) + 1
        prefix = text[:start_scan] if start_scan else ''
        work = text[start_scan:] if start_scan else text
        if '://' in work:
            has_apos = "'" in work
            if '@' in work:
                work = (_URL_FAST_AUTH_APOS if has_apos else _URL_FAST_AUTH_SIMPLE).sub(r'\1\2', work)
            if '?' in work or '#' in work:
                work = (_URL_FAST_QUERY_APOS if has_apos else _URL_FAST_QUERY_SIMPLE).sub(r'\1', work)
            if '@' in work or '?' in work or '#' in work:
                last_trig = max(work.rfind('@'), work.rfind('?'), work.rfind('#'))
                n = len(work)
                out: list[str] = []
                pos = 0
                while pos < n:
                    sep = work.find('://', pos)
                    if sep == -1 or sep > last_trig:
                        out.append(work[pos:])
                        break
                    scheme_start, scheme = _match_scheme_before_sep(work, sep, pos)
                    if scheme_start == -1:
                        out.append(work[pos:sep + 3])
                        pos = sep + 3
                        continue
                    if scheme_start > pos:
                        out.append(work[pos:scheme_start])
                    body_start = sep + 3
                    if scheme == 'file':
                        url_end, next_pos = _scan_file_url_end(work, body_start, n)
                        if url_end > body_start:
                            out.append(_redact_url_token(work[scheme_start:url_end]))
                            pos = url_end
                        else:
                            out.append(work[scheme_start:body_start])
                            pos = max(body_start, next_pos)
                    else:
                        url_end = _scan_net_or_query_end(work, body_start, n)
                        out.append(_redact_url_token(work[scheme_start:url_end]))
                        pos = max(url_end, body_start)
                work = ''.join(out)
        text = prefix + work if prefix else work
    if ('?' in text or '#' in text) and ('mailto:' in text or (('m' in text or 'M' in text) and 'mailto:' in text.lower())):
        low = text.lower()
        n = len(text)
        out_m: list[str] = []
        pos = 0
        while pos < n:
            idx = low.find('mailto:', pos)
            if idx == -1:
                out_m.append(text[pos:])
                break
            if idx > 0 and text[idx - 1].isalnum():
                out_m.append(text[pos:idx + 7])
                pos = idx + 7
                continue
            out_m.append(text[pos:idx])
            end = _scan_net_or_query_end(text, idx + 7, n)
            tok = text[idx:end]
            q = tok.find('?')
            h = tok.find('#')
            if q != -1 or h != -1:
                cut = len(tok)
                if q != -1:
                    cut = min(cut, q)
                if h != -1:
                    cut = min(cut, h)
                tok = tok[:cut]
            out_m.append(tok)
            pos = max(end, idx + 7)
        text = ''.join(out_m)
    return text


def _split_scheme_tail(span: str, full_text: str, end_idx: int) -> tuple[str, str]:
    is_double_slash = full_text[end_idx:end_idx + 3] == '://'
    is_scheme_colon = (
        not is_double_slash
        and full_text[end_idx:end_idx + 1] == ':'
        and end_idx + 1 < len(full_text)
        and full_text[end_idx + 1] not in ('\\', '/', ' ', '\t', '\r', '\n')
    )
    if not is_double_slash and not is_scheme_colon:
        return span, ''
    i = len(span)
    while i > 0 and (span[i - 1].isalnum() or span[i - 1] in '+.-'):
        i -= 1
    cand = span[i:]
    slen = 0
    if cand and cand[0].isalpha():
        if i == 0 or span[i - 1] in (' ', '\t', '(', '[', '{', '=', '"', "'"):
            if is_double_slash or cand.lower() in _MAILTO_SCHEMES:
                slen = len(cand)
        elif is_double_slash:
            lc = cand.lower()
            for sch in _KNOWN_SCHEMES:
                if lc.endswith(sch):
                    slen = len(sch)
                    break
    if not slen:
        return span, ''
    cut = len(span) - slen
    if cut > 0 and span[cut - 1] in (' ', '\t'):
        while cut > 0 and span[cut - 1] in (' ', '\t'):
            cut -= 1
    return span[:cut], span[cut:]


def _trim_before_adjacent_drive(span: str, full_text: str, end_idx: int) -> tuple[str, str]:
    if end_idx + 1 < len(full_text) and full_text[end_idx] == ':' and full_text[end_idx + 1] in ('\\', '/'):
        if span and span[-1].isascii() and span[-1].isalpha():
            cut = len(span) - 1
            while cut > 0 and span[cut - 1] in (' ', '\t'):
                cut -= 1
            return span[:cut], span[cut:]
    return span, ''


def _trim_cc_span(span: str, full_text: str, end_idx: int, allow_esc_apos_posix: bool = False) -> str:
    if '%' in span:
        up_idx = span.lower().find('%userprofile%')
        if up_idx != -1:
            span = span[:up_idx]
    if end_idx < len(full_text) and full_text[end_idx] == ':':
        span, sch_tail = _split_scheme_tail(span, full_text, end_idx)
        if not sch_tail:
            span, _ = _trim_before_adjacent_drive(span, full_text, end_idx)
    if "'" in span:
        slen = len(span)
        apos_pos = span.find("'")
        while apos_pos != -1:
            nxt = span[apos_pos + 1] if apos_pos + 1 < slen else ''
            if not nxt or not (nxt.isalnum() or nxt == '_'):
                cut = apos_pos - 1 if (allow_esc_apos_posix and apos_pos > 0 and span[apos_pos - 1] == '\\') else apos_pos
                span = span[:cut]
                break
            apos_pos = span.find("'", apos_pos + 1)
    return span.rstrip(' \t')


def _apply_users_cc(text: str, pat: re.Pattern[str], allow_esc_apos_posix: bool = False) -> tuple[str, bool]:
    m = pat.search(text)
    if m is None:
        return text, False
    out: list[str] = []
    append = out.append
    cursor = 0
    changed = False
    search = pat.search
    while m is not None:
        g2_start = m.start(2)
        trimmed = _trim_cc_span(m.group(2), text, m.end(2), allow_esc_apos_posix=allow_esc_apos_posix)
        if trimmed:
            append(text[cursor:g2_start])
            append('%USERNAME%')
            cursor = g2_start + len(trimmed)
            changed = True
        else:
            append(text[cursor:g2_start])
            cursor = g2_start
        m = search(text, cursor)
    if not changed:
        return text, False
    append(text[cursor:])
    return ''.join(out), True


def _redact_win_drive_paths(text: str) -> tuple[str, bool]:
    out_fast, _ = _apply_users_cc(text, _FAST_WIN_CC)
    still_has = _HAS_UNREDACTED_USERS.search(out_fast) is not None
    if still_has:
        out_fast, n_sub = _apply_users_cc(out_fast, _FAST_WIN_NESTED_CC)
        if n_sub:
            still_has = _HAS_UNREDACTED_USERS.search(out_fast) is not None
    if not still_has:
        return out_fast, False
    parts = _DRIVE_ROOT_SPLIT.split(out_fast)
    if len(parts) == 1:
        return out_fast, True
    out = [parts[0]]
    append = out.append
    delim_search = _DELIM_RE.search
    adj_search = _ADJACENT_PATH_SPLIT.search
    tail_sub = _USERS_WIN_TAIL.sub
    has_unredacted = _HAS_UNREDACTED_USERS.search
    n = len(parts)
    for idx in range(1, n, 2):
        root = parts[idx]
        chunk = parts[idx + 1]
        if has_unredacted(chunk) is None:
            append(root)
            append(chunk)
            continue
        m_del = delim_search(chunk)
        if m_del is not None:
            dpos = m_del.start()
            span = chunk[:dpos]
            tail = chunk[dpos:]
            if chunk[dpos:dpos + 3] == '://' or (dpos + 1 < len(chunk) and chunk[dpos] == ':'):
                span, sch_tail = _split_scheme_tail(span, chunk, dpos)
                tail = sch_tail + tail
        else:
            span = chunk
            tail = ''
            if idx + 2 < n and span and span[-1] in (' ', '\t'):
                stripped = span.rstrip(' \t')
                tail = span[len(stripped):]
                span = stripped
        m_adj = adj_search(span)
        if m_adj is not None:
            apos = m_adj.start()
            tail = span[apos:] + tail
            span = span[:apos]
        if has_unredacted(span) is None:
            append(root)
            append(span)
            append(tail)
            continue
        rprefix = root[:13] if root[0] == '%' else root[:2]
        append(rprefix)
        append(tail_sub(r'\1%USERNAME%', root[len(rprefix):] + span))
        if tail:
            append(tail)
    res = ''.join(out)
    return res, (_HAS_UNREDACTED_USERS.search(res) is not None)


def _redact_unc_span(m: re.Match[str]) -> str:
    span = m.group(0)
    if _HAS_UNREDACTED_USERS.search(span) is None:
        return span
    suffix = ''
    end_idx = m.end()
    if end_idx < len(m.string) and m.string[end_idx] == ':':
        span, suffix = _split_scheme_tail(span, m.string, end_idx)
        if not suffix:
            span, suffix = _trim_before_adjacent_drive(span, m.string, end_idx)
    if _HAS_UNREDACTED_USERS.search(span) is None:
        return span + suffix
    if _ADJACENT_PATH_SPLIT.search(span) is not None:
        parts = _ADJACENT_PATH_SPLIT.split(span)
        rebuilt: list[str] = []
        for idx, part in enumerate(parts):
            if idx % 2 == 1:
                rebuilt.append(part)
            elif part.startswith('\\\\') and _HAS_UNREDACTED_USERS.search(part) is not None:
                rebuilt.append(_USERS_UNC_TAIL.sub(r'\1%USERNAME%', part))
            else:
                rebuilt.append(part)
        return ''.join(rebuilt) + suffix
    return _USERS_UNC_TAIL.sub(r'\1%USERNAME%', span) + suffix


def _redact_tail_span(m: re.Match[str], head_re: re.Pattern[str], required_prefix: str) -> str:
    span = m.group(0)
    suffix = ''
    end_idx = m.end()
    if end_idx < len(m.string) and m.string[end_idx] == ':':
        span, suffix = _split_scheme_tail(span, m.string, end_idx)
        if not suffix:
            span, suffix = _trim_before_adjacent_drive(span, m.string, end_idx)
    up_idx = span.lower().find('%userprofile%')
    if up_idx != -1:
        cut = up_idx
        while cut > 0 and span[cut - 1] in (' ', '\t'):
            cut -= 1
        suffix = span[cut:] + suffix
        span = span[:cut]
    parts = _ADJACENT_PATH_SPLIT.split(span) if _ADJACENT_PATH_SPLIT.search(span) is not None else [span]
    rebuilt: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            rebuilt.append(part)
            continue
        if not part.startswith(required_prefix) or (required_prefix == '\\' and part.startswith('\\\\')):
            rebuilt.append(part)
            continue
        if _HAS_UNREDACTED_USERS.search(part) is None:
            rebuilt.append(part)
            continue
        if part.lower().count('users') <= 1:
            m_head = head_re.match(part)
            if not m_head:
                rebuilt.append(part)
                continue
            prefix, body = m_head.group(1), m_head.group(2)
            sep_idx = -1
            for ch_idx, ch in enumerate(body):
                if ch in ('/', '\\'):
                    sep_idx = ch_idx
                    break
            if sep_idx != -1:
                first_seg = body[:sep_idx]
                rest = body[sep_idx:]
                m_seg = _POSIX_USER_SEG.match(first_seg)
                if m_seg:
                    rebuilt.append(f'{prefix}%USERNAME%{first_seg[m_seg.end():]}{rest}')
                else:
                    rebuilt.append(part)
                continue
            stripped = body.rstrip(' \t')
            trailing_ws = body[len(stripped):]
            m_seg = _POSIX_USER_SEG.match(stripped)
            if m_seg:
                end_seg = m_seg.end()
                while end_seg > 0 and stripped[end_seg - 1] in (' ', '\t'):
                    end_seg -= 1
                if end_seg > 0:
                    rebuilt.append(f'{prefix}%USERNAME%{stripped[end_seg:]}{trailing_ws}')
                    continue
            rebuilt.append(part)
        else:
            rebuilt.append(_USERS_WIN_TAIL.sub(r'\1%USERNAME%', part))
    return ''.join(rebuilt) + suffix


def _redact_rooted_win_span(m: re.Match[str]) -> str:
    return _redact_tail_span(m, _ROOTED_HEAD, '\\')


def _redact_posix_span(m: re.Match[str]) -> str:
    return _redact_tail_span(m, _POSIX_HEAD, '/')
_WINERR_RE = re.compile(r'(?:WinError|winerror)\s*[:=]?\s*(\d+)')
_HTTP_STATUS_RE = re.compile(r'(?:HTTP Error|HTTP|mã)\s+(\d{3})\b', re.IGNORECASE)

_SAFE_USER_TOKENS = frozenset({
    'user', 'admin', 'administrator', 'guest', 'default', 'public',
    'system', 'windows', 'stellasora', 'launcher', 'github', 'yostar', 'steam',
})


def _home_variants() -> list[str]:
    out = []
    home_raw: Optional[str] = None
    try:
        home_raw = str(Path.home())
    except Exception:  # noqa: BLE001
        home_raw = None
    for raw in (os.environ.get('USERPROFILE'), home_raw):
        if raw:
            norm = str(raw).rstrip('\\/')
            if len(norm) >= 4:
                out.append(norm)
    return sorted(set(out), key=lambda v: (-len(v), v))


def _username_variants() -> list[str]:
    out: list[str] = []
    candidates = [os.environ.get('USERNAME')]
    try:
        candidates.append(getpass.getuser())
    except Exception:  # noqa: BLE001
        pass
    for raw in candidates:
        name = str(raw or '').strip()
        if len(name) >= 3 and name.casefold() not in _SAFE_USER_TOKENS:
            out.append(name)
    return sorted(set(out), key=lambda v: (-len(v), v))


def redact(text: Any) -> str:
    """Remove account-identifying paths, standalone usernames, URL credentials, and queries."""
    out = _sstr(text)
    if not out:
        return ''
    out = _redact_urls_linear(out)
    low = out.lower()
    if ':' in out or '/' in out or '\\' in out:
        variants: list[str] = []
        for home in _home_variants():
            variants.extend((home, home.replace('\\', '\\\\'), home.replace('\\', '/')))
        for variant in sorted(set(variants), key=lambda v: (-len(v), v)):
            if variant.lower() in low:
                out = re.sub(
                    re.escape(variant) + r'(?=$|[\\/",:;(){\[\]}>|\r\n]|\'(?!\w))',
                    '%USERPROFILE%',
                    out,
                    flags=re.IGNORECASE,
                )
                low = out.lower()
    if 'users' in low:
        still_has = True
        prev_out = out
        if ':' in out or '%userprofile%' in low:
            out, still_has = _redact_win_drive_paths(out)
        if still_has:
            if '\\\\' in out:
                out, n_sub = _apply_users_cc(out, _FAST_UNC_CC)
                if n_sub:
                    still_has = _HAS_UNREDACTED_USERS.search(out) is not None
                if still_has:
                    out, n_sub = _apply_users_cc(out, _FAST_WIN_NESTED_CC)
                    if n_sub:
                        still_has = _HAS_UNREDACTED_USERS.search(out) is not None
                if still_has:
                    out, n_sub = _UNC_SPAN.subn(_redact_unc_span, out)
                    if n_sub:
                        still_has = _HAS_UNREDACTED_USERS.search(out) is not None
            if still_has and '\\' in out:
                out, n_sub = _apply_users_cc(out, _FAST_WIN_NESTED_CC)
                if n_sub:
                    still_has = _HAS_UNREDACTED_USERS.search(out) is not None
                if still_has:
                    out, n_sub = _USERS_ROOTED_SPAN.subn(_redact_rooted_win_span, out)
                    if n_sub:
                        still_has = _HAS_UNREDACTED_USERS.search(out) is not None
            if still_has and '/' in out:
                out, n_sub = _apply_users_cc(out, _FAST_POSIX_CC, allow_esc_apos_posix=True)
                if n_sub:
                    still_has = _HAS_UNREDACTED_USERS.search(out) is not None
                if still_has:
                    out = _USERS_POSIX_SPAN.sub(_redact_posix_span, out)
        if out != prev_out:
            low = out.lower()
    for uname in _username_variants():
        if uname.lower() in low:
            out = re.sub(rf'\b{re.escape(uname)}\b', '%USERNAME%', out, flags=re.IGNORECASE)
            low = out.lower()
    out = _redact_urls_linear(out)
    return _sanitize_surrogates(out)


def _sanitize_surrogates(text: Any) -> str:
    """Replace lone UTF-16 surrogates (e.g. from Win32 OS error messages) so UTF-8 encoding never raises."""
    if type(text) is not str:
        text = _sstr(text)
    if text.isascii():
        return text
    return text.encode('utf-8', 'replace').decode('utf-8')


def _redact_obj(obj: Any, seen: Optional[set[int]] = None) -> Any:
    if type(obj) is str:
        return _sanitize_surrogates(redact(obj))
    if isinstance(obj, str):
        return _sanitize_surrogates(redact(_sstr(obj)))
    if isinstance(obj, Path):
        return _sanitize_surrogates(redact(_sstr(obj)))
    if isinstance(obj, dict):
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return '[CyclicRef]'
        seen.add(obj_id)
        try:
            items = list(obj.items())
            return {_sanitize_surrogates(redact(_sstr(k, '?'))): _redact_obj(v, seen=seen) for k, v in items}
        except Exception:  # noqa: BLE001
            return {}
        finally:
            seen.discard(obj_id)
    if isinstance(obj, (list, tuple)):
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return '[CyclicRef]'
        seen.add(obj_id)
        try:
            seq = list(obj)
            return [_redact_obj(v, seen=seen) for v in seq]
        except Exception:  # noqa: BLE001
            return []
        finally:
            seen.discard(obj_id)
    if obj is None or type(obj) in (bool, int):
        return obj
    if type(obj) is float:
        return obj if math.isfinite(obj) else None
    if isinstance(obj, bool):
        return _sbool(obj)
    if isinstance(obj, int):
        return _coerce_opt_int(obj)
    if isinstance(obj, float):
        try:
            v = float(obj)
            return v if (type(v) is float and math.isfinite(v)) else None
        except Exception:  # noqa: BLE001
            return None
    s = _sstr(obj, '')
    return _sanitize_surrogates(redact(s)) if s else None


def safe_url(url: Any) -> str:
    """scheme://host[:port]/path only (no credentials, query or fragment), plus PII redaction."""
    if url is None:
        return '(không có)'
    try:
        raw = _sstr(url)
        if not raw:
            return '(không có)'
        norm_raw = raw.replace('\\', '/') if raw.lstrip().lower().startswith('file:') else raw
        u = urllib.parse.urlparse(norm_raw)
        scheme = u.scheme.lower()
        if scheme == 'file':
            if not u.hostname and not u.path.strip('/'):
                return '(địa chỉ không hợp lệ)'
            host = (f'[{u.hostname}]' if ':' in u.hostname else u.hostname) if u.hostname else ''
            u_port = u.port
            port = f':{u_port}' if u_port else ''
            clean_path = re.sub(r'/+', '/', u.path)
            return _sanitize_surrogates(redact(f'{u.scheme}://{host}{port}{clean_path}'))
        if scheme not in ('http', 'https') or not u.hostname:
            return '(địa chỉ không hợp lệ)'
        host = f'[{u.hostname}]' if ':' in u.hostname else u.hostname
        u_port = u.port
        port = f':{u_port}' if u_port else ''
        clean_path = re.sub(r'/+', '/', u.path)
        return _sanitize_surrogates(redact(f'{u.scheme}://{host}{port}{clean_path}'))
    except Exception:  # noqa: BLE001
        return '(địa chỉ không hợp lệ)'


def new_report_id() -> str:
    n, digits, out = int(time.time() * 1000), '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', ''
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return out or '0'


@dataclass
class ErrorContext:
    """Snapshot of launcher state at failure time. Every field is optional."""
    action: str = ''                 # what the user was doing, e.g. "Cài Việt hoá"
    operation: str = ''              # internal operation kind
    progress: str = ''               # last progress line
    path_manager: Any = None
    game: Any = None                 # core.types.GameInfo
    sync: Optional[dict] = None      # github sync state
    channel: Optional[dict] = None   # github channel config
    probe: Optional[dict] = None     # net_probe.run_probe() result
    extra: dict = field(default_factory=dict)
    # v2.0 contextual diagnostics fields
    error_code: str = ''
    win32_error: Optional[int] = None
    http_status: Optional[int] = None
    target_file: str = ''
    target_url: str = ''
    system_report: Optional[Any] = None
    config: Optional[dict] = None
    writability: Optional[Any] = None
    log_lines: int = 30


@dataclass
class ErrorReport:
    code: str
    report_id: str
    title: str
    summary: str
    steps: tuple
    level: str
    message: str
    text: str
    wrapper: str = ''
    probe_text: str = ''
    # v2.0 enriched fields
    win32_error: Optional[int] = None
    http_status: Optional[int] = None
    target_file: str = ''
    target_url: str = ''
    context_rows: tuple[dict[str, str], ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        return self.level == 'error'

    @property
    def code_line(self) -> str:
        return f'Mã lỗi: {_sanitize_surrogates(_sstr(self.code))} · #{_sanitize_surrogates(_sstr(self.report_id))}'

    def dialog_details(self) -> str:
        """Text for the scrollable area of the dialog (steps + short technical block)."""
        parts = []
        steps_iter: tuple[Any, ...] = ()
        try:
            if _sbool(self.steps):
                steps_iter = tuple(self.steps)
        except Exception:  # noqa: BLE001
            steps_iter = ()
        if steps_iter:
            parts.append('CÁCH XỬ LÝ')
            parts.extend(f'{i}. {_sstr(s)}' for i, s in enumerate(steps_iter, 1))
            parts.append('')
        parts.append(_sstr(self.code_line))
        parts.append('Bấm "Sao chép mã lỗi" để chép toàn bộ thông tin chẩn đoán gửi cho người hỗ trợ.')
        msg_str = _sstr(self.message)
        sum_str = _sstr(self.summary)
        if msg_str and msg_str.strip() and msg_str.strip() != sum_str.strip():
            parts.extend(['', 'CHI TIẾT KỸ THUẬT', redact(msg_str)])
        return _sanitize_surrogates(redact('\n'.join(parts)))

    def to_dict(self) -> dict[str, Any]:
        """Returns a PII-redacted, JSON-serializable representation of this report."""
        try:
            steps_list = [_sanitize_surrogates(redact(s)) for s in (self.steps or ())]
        except Exception:  # noqa: BLE001
            steps_list = []
        base = {
            'code': _sanitize_surrogates(_sstr(self.code)),
            'report_id': _sanitize_surrogates(_sstr(self.report_id)),
            'title': _sanitize_surrogates(redact(self.title)),
            'summary': _sanitize_surrogates(redact(self.summary)),
            'steps': steps_list,
            'level': _sanitize_surrogates(_sstr(self.level)),
            'message': _sanitize_surrogates(redact(self.message)),
            'wrapper': _sanitize_surrogates(_sstr(self.wrapper)),
            'probe_text': _sanitize_surrogates(redact(self.probe_text)),
            'win32_error': _safe_json_scalar(self.win32_error),
            'http_status': _safe_json_scalar(self.http_status),
            'target_file': _sanitize_surrogates(redact(self.target_file)) if _sstr(self.target_file) else '',
            'target_url': _sanitize_surrogates(safe_url(self.target_url)) if _sstr(self.target_url) else '',
            'context_rows': _redact_context_rows(self.context_rows),
            'text': _sanitize_surrogates(redact(self.text)),
        }
        has_payload = False
        try:
            has_payload = bool(self.payload)
        except Exception:  # noqa: BLE001
            has_payload = self.payload is not None
        if has_payload:
            base['payload'] = _redact_obj(self.payload)
        return base

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, allow_nan=False)


# --------------------------------------------------------------------------- safe attribute / exception inspection
def _sget(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    except Exception:  # noqa: BLE001
        return default


def _sbool(value: Any, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def _sstr(value: Any, default: str = '') -> str:
    if value is None:
        return default
    if type(value) is str:
        return value
    try:
        s = str(value)
        return s if type(s) is str else (str.__str__(s) if isinstance(s, str) else default)
    except Exception:  # noqa: BLE001
        return default


def _coerce_opt_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if type(value) is int:
        return value
    if isinstance(value, int):
        try:
            v = int(value)
            return v if type(v) is int else None
        except Exception:  # noqa: BLE001
            return None
    try:
        v = int(_sstr(value).strip())
        return v if type(v) is int else None
    except Exception:  # noqa: BLE001
        return None


_CONTEXT_ROW_SCHEMA_KEYS = frozenset({'label', 'value', 'tone'})


def _redact_context_rows(rows: Any) -> Any:
    if not isinstance(rows, (list, tuple)):
        return _redact_obj(rows)
    seen: set[int] = set()
    out: list[Any] = []
    try:
        seq = list(rows)
    except Exception:  # noqa: BLE001
        return []
    for row in seq:
        if isinstance(row, dict):
            rid = id(row)
            if rid in seen:
                out.append('[CyclicRef]')
                continue
            seen.add(rid)
            try:
                cleaned = {}
                for k, v in list(row.items()):
                    ks = _sanitize_surrogates(_sstr(k, '?'))
                    safe_k = ks if ks in _CONTEXT_ROW_SCHEMA_KEYS else _sanitize_surrogates(redact(ks))
                    cleaned[safe_k] = _redact_obj(v, seen=seen)
                out.append(cleaned)
            except Exception:  # noqa: BLE001
                out.append({})
            finally:
                seen.discard(rid)
        else:
            out.append(_redact_obj(row, seen=seen))
    return out


def _safe_json_scalar(value: Any) -> Any:
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else None
    if type(value) is str:
        return _sanitize_surrogates(redact(value))
    if isinstance(value, bool):
        return _sbool(value)
    if isinstance(value, int):
        return _coerce_opt_int(value)
    if isinstance(value, float):
        try:
            v = float(value)
            return v if (type(v) is float and math.isfinite(v)) else None
        except Exception:  # noqa: BLE001
            return None
    if isinstance(value, str):
        return _sanitize_surrogates(redact(_sstr(value)))
    c = _coerce_opt_int(value)
    if c is not None:
        return c
    s = _sstr(value, '')
    return _sanitize_surrogates(redact(s)) if s else None


def _yn(value: Any) -> str:
    return 'Có' if _sbool(value) else 'Không'


def _free_gb_num(path: Any) -> Optional[float]:
    try:
        return shutil.disk_usage(path).free / (1024 ** 3)
    except Exception:  # noqa: BLE001
        return None


def _free_gb(path: Any) -> str:
    val = _free_gb_num(path)
    return f'{val:.1f} GB' if val is not None else 'không đọc được'


def _is_admin() -> bool:
    return is_process_admin()


def _proxy_summary() -> str:
    try:
        proxies = urllib.request.getproxies()
    except Exception:  # noqa: BLE001
        return 'không đọc được'
    if not proxies:
        return 'không dùng proxy'
    out = []
    for scheme, value in sorted(proxies.items()):
        try:
            val_str = _sstr(value)
            u = urllib.parse.urlparse(val_str if '//' in val_str else '//' + val_str)
            u_port = u.port
            out.append(f'{_sstr(scheme, "?")}={u.hostname}{":" + str(u_port) if u_port else ""}')
        except Exception:  # noqa: BLE001
            out.append(f'{_sstr(scheme, "?")}=?')
    return ', '.join(out)


def _extract_exc_metadata(exc: Any, ctx: ErrorContext) -> tuple[Optional[int], Optional[int], str, str]:
    win32_err: Optional[int] = _coerce_opt_int(_sget(ctx, 'win32_error', None))
    http_status: Optional[int] = _coerce_opt_int(_sget(ctx, 'http_status', None))
    target_file: str = _sstr(_sget(ctx, 'target_file', ''))
    target_url: str = _sstr(_sget(ctx, 'target_url', ''))

    if isinstance(exc, BaseException):
        for item in error_catalog.exception_chain(exc):
            if win32_err is None:
                w = _coerce_opt_int(_sget(item, 'winerror', None))
                if w is not None:
                    win32_err = w
                else:
                    m = _WINERR_RE.search(_sstr(item))
                    if m:
                        win32_err = _coerce_opt_int(m.group(1))
            if http_status is None:
                if isinstance(item, urllib.error.HTTPError):
                    http_status = _coerce_opt_int(_sget(item, 'code', None))
                if http_status is None:
                    m = _HTTP_STATUS_RE.search(_sstr(item))
                    if m:
                        http_status = _coerce_opt_int(m.group(1))
            if not target_file:
                fn = _sget(item, 'filename', None)
                if fn is not None:
                    fn_str = _sstr(fn)
                    if fn_str:
                        target_file = fn_str
            if not target_url:
                u_str = _sstr(_sget(item, 'url', None))
                if not u_str:
                    geturl = _sget(item, 'geturl', None)
                    if callable(geturl):
                        try:
                            u_str = _sstr(geturl())
                        except Exception:  # noqa: BLE001
                            u_str = ''
                if u_str:
                    target_url = u_str

    if target_url:
        target_url = safe_url(target_url)
    if target_file:
        target_file = redact(target_file)
    return win32_err, http_status, target_file, target_url


def _writability_summary(ctx: ErrorContext) -> tuple[Optional[bool], str, bool, str]:
    """Returns (writable_bool, status_str, cfa_suspected, human_label)."""
    w = _sget(ctx, 'writability', None)
    if w is not None:
        raw_writable = _sget(w, 'writable', None)
        writable = None if raw_writable is None else _sbool(raw_writable, False)
        status = _sstr(_sget(w, 'status', 'unknown'), 'unknown') or 'unknown'
        cfa = _sbool(_sget(w, 'cfa_suspected', False), False) or status == 'cfa_blocked'
        detail = _sstr(_sget(w, 'detail', ''), '')
        return writable, status, cfa, detail or status

    sr = _sget(ctx, 'system_report', None)
    if sr is not None:
        raw_writable = _sget(sr, 'folder_writable', None)
        writable = None if raw_writable is None else _sbool(raw_writable, False)
        status = _sstr(_sget(sr, 'writability_status', 'unknown'), 'unknown') or 'unknown'
        cfa = _sbool(_sget(sr, 'cfa_suspected', False), False) or status == 'cfa_blocked'
        detail = _sstr(_sget(sr, 'writability_detail', ''), '')
        return writable, status, cfa, detail or status

    return None, 'unknown', False, 'Chưa kiểm tra'


# --------------------------------------------------------------------------- section builders
def _system_lines(ctx: ErrorContext) -> list[str]:
    pm = _sget(ctx, 'path_manager', None)
    os_info = get_os_build_info()
    os_summary = _sstr(_sget(os_info, 'summary', '')) or platform.platform()
    lines = [
        f'Launcher: v{LAUNCHER_VERSION} ({"đã đóng gói .exe" if getattr(sys, "frozen", False) else "chạy từ mã nguồn"})',
        f'Windows: {os_summary} · {platform.machine()}',
        f'Quyền Quản trị: {_yn(_is_admin())}',
        f'Múi giờ: UTC{time.strftime("%z")} · Python {platform.python_version()}',
        f'Proxy hệ thống: {_proxy_summary()}',
    ]
    try:
        tinfo = tls.info()
        sys_r = _sstr(_sget(tinfo, 'system_roots', '?'), '?')
        tru_r = _sstr(_sget(tinfo, 'trusted_roots', '?'), '?')
        ext_r = _sstr(_sget(tinfo, 'extra_roots', 0), '0')
        lines.append(f'TLS Root Store: hệ thống {sys_r} · tổng {tru_r} (+{ext_r} certifi)')
    except Exception:  # noqa: BLE001
        pass
    if pm is not None:
        try:
            app = _sstr(_sget(pm, 'app_data_dir', ''))
            if app:
                lines.append(f'Thư mục dữ liệu launcher: {app} (trống {_free_gb(app)})')
            else:
                lines.append('Thư mục dữ liệu launcher: không truy cập được')
        except Exception:  # noqa: BLE001
            lines.append('Thư mục dữ liệu launcher: không truy cập được')
    sr = _sget(ctx, 'system_report', None)
    if sr is not None:
        gm = _sstr(_sget(sr, 'graphics_mode', ''))
        dpi = _sstr(_sget(sr, 'screen_dpi_info', ''))
        mig = _sstr(_sget(sr, 'migration_status', ''))
        if dpi:
            lines.append(f'DPI hệ thống: {dpi}')
        if gm:
            lines.append(f'Chế độ đồ họa: {gm}')
        if mig:
            lines.append(f'Di trú r02: {mig}')
    writable, wstatus, cfa, wdetail = _writability_summary(ctx)
    if wstatus != 'unknown' or writable is not None:
        lines.append(f'Quyền ghi thư mục: {wdetail} (status={wstatus}, cfa={_yn(cfa)})')
    return lines


def _game_lines(ctx: ErrorContext) -> list[str]:
    g = _sget(ctx, 'game', None)
    if g is None:
        return ['Chưa có thông tin game.']
    path = _sstr(_sget(g, 'game_path', ''))
    det_src = _sstr(_sget(g, 'detection_source', '?'), '?') or '?'
    plat = _sstr(_sget(g, 'platform', '?'), '?') or '?'
    ver = _sstr(_sget(g, 'version', '?'), '?') or '?'
    rver = _sstr(_sget(g, 'resource_version', '?'), '?') or '?'
    lines = [
        f'Nhận diện thư mục game: {_yn(_sget(g, "installed", False))} (nguồn: {det_src})',
        f'Đường dẫn: {path if path else "chưa chọn"}',
        f'Nền tảng: {plat} · game {ver} / tài nguyên {rver}',
        f'Game đang chạy: {_yn(_sget(g, "is_running", False))}',
    ]
    if path:
        try:
            p = Path(path)
            lines.append(f'StellaSora.exe: {"có" if (p / "StellaSora.exe").is_file() else "KHÔNG THẤY"} · thư mục tồn tại: {_yn(p.is_dir())} · trống {_free_gb(p if p.exists() else p.anchor)}')
        except Exception:  # noqa: BLE001
            pass
    receipt = _sget(g, 'installed_receipt', None)
    if isinstance(receipt, dict) and _sbool(receipt):
        files_obj = _sget(receipt, 'files', None)
        try:
            files_cnt = len(files_obj) if isinstance(files_obj, (dict, list, tuple, set)) else 0
        except Exception:  # noqa: BLE001
            files_cnt = 0
        rec_ver = _sstr(_sget(receipt, 'version', '?'), '?') or '?'
        inst_at = _sstr(_sget(receipt, 'installed_at', '?'), '?') or '?'
        lines.append(
            f'Biên bản cài: có · bản dịch {rec_ver} · {files_cnt} tệp · cài lúc {inst_at}'
        )
    else:
        lines.append('Biên bản cài: KHÔNG CÓ (chưa cài Việt hoá bằng launcher này, hoặc biên bản không khớp thư mục)')
    bak_raw = _sget(g, 'backup_count', 0)
    bak_int = _coerce_opt_int(bak_raw)
    bak_str = str(bak_int) if bak_int is not None else (_sstr(bak_raw, '0') or '0')
    lines.append(f'Biên bản lỗi thời: {_yn(_sget(g, "receipt_stale", False))} · có bản dịch: {_yn(_sget(g, "has_vietnamese", False))} · số bản sao lưu: {bak_str}')
    official = _sget(g, 'official_restore', None)
    if isinstance(official, dict) and _sbool(official):
        rest_at = _sstr(_sget(official, 'restored_at', '?'), '?') or '?'
        off_rver = _sstr(_sget(official, 'official_resource_version', '?'), '?') or '?'
        lines.append(f'Đã khôi phục dữ liệu gốc: {rest_at} (tài nguyên {off_rver})')
    return lines


def _sync_lines(ctx: ErrorContext) -> list[str]:
    s = ctx.sync or {}
    lines = []
    ch = ctx.channel or {}
    if ch:
        lines.append(f'Kho/nhánh: {ch.get("repo", "?")} @ {ch.get("branch", "?")}')
        lines.append(f'Địa chỉ phát hành: {safe_url(ch.get("release_url"))}')
        lines.append(f'Địa chỉ thông báo: {safe_url(ch.get("notifications_url"))}')
        if ch.get('manifest_url'):
            lines.append(f'Địa chỉ bảng kê tuỳ chọn: {safe_url(ch.get("manifest_url"))}')
        if ch.get('configuration_error'):
            lines.append(f'Lỗi cấu hình: {ch["configuration_error"]}')
    if not s:
        lines.append('Chưa đồng bộ GitHub lần nào.')
        return lines
    lines.append(f'Trạng thái chung: {s.get("message", "?")} (đã tươi: {_yn(s.get("fresh"))})')
    if 'release_status' in s:
        lines.append(f'Bản phát hành: {s.get("release_status")} · {s.get("release_version") or "chưa đọc được"}')
        if s.get('release_error'):
            lines.append(f'  Lỗi bản phát hành [{s.get("release_error_code", "?")}]: {s["release_error"]}')
    if 'manifest_status' in s:
        lines.append(
            f'Bảng kê bản dịch: {s.get("manifest_status")} · {s.get("translation_version") or "chưa xác minh"}'
            f' · game {s.get("translation_game") or "?"} / tài nguyên {s.get("translation_resource") or "?"} · {s.get("translation_file_count") if s.get("translation_file_count") is not None else "?"} tệp'
        )
        if s.get('manifest_error'):
            lines.append(f'  Lỗi bảng kê [{s.get("manifest_error_code", "?")}]: {s["manifest_error"]}')
    if 'notification_status' in s:
        lines.append(f'Thông báo: {s.get("notification_status")} · {s.get("notification_message", "")}')
    upd = s.get('update')
    if isinstance(upd, dict):
        lines.append(f'Cập nhật launcher: {upd.get("status")} · {upd.get("message", "")}')
    if s.get('cache_warning'):
        lines.append(f'Cảnh báo bộ nhớ đệm: {s["cache_warning"]}')
    if s.get('fetched_at'):
        lines.append(f'Đồng bộ lúc: {s["fetched_at"]}')
    return lines


def _log_tail(ctx: ErrorContext, count: Optional[int] = None) -> list[str]:
    pm = ctx.path_manager
    if pm is None:
        return []
    line_limit = max(1, int(getattr(ctx, 'log_lines', 30) or 30)) if count is None else count
    try:
        path = Path(pm.logs_dir) / 'launcher.log'
        if not path.is_file():
            return ['(chưa có tệp nhật ký)']
        with path.open('rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 24 * 1024))
            raw = f.read().decode('utf8', errors='replace')
        tail = raw.splitlines()[-line_limit:]
        return [(line if len(line) <= 260 else line[:260] + '…') for line in tail]
    except Exception:  # noqa: BLE001
        return ['(không đọc được nhật ký)']


def _trace_lines(exc: Any, limit: int = 24) -> list[str]:
    if not isinstance(exc, BaseException):
        return []
    try:
        lines = [ln for block in traceback.format_exception(type(exc), exc, exc.__traceback__) for ln in block.rstrip().splitlines()]
    except Exception:  # noqa: BLE001
        return []
    return lines[-limit:]


def _safe(section, ctx: ErrorContext) -> list[str]:
    """One broken section must never cost the user the whole report."""
    try:
        return section(ctx)
    except Exception as exc:  # noqa: BLE001
        return [f'(không đọc được mục này: {type(exc).__name__})']


def _build_context_rows(
    ctx: ErrorContext,
    win32_err: Optional[int],
    http_status: Optional[int],
    target_file: str,
    target_url: str,
) -> tuple[dict[str, str], ...]:
    action_val = _sanitize_surrogates(redact(_sstr(_sget(ctx, 'action', '')) or _sstr(_sget(ctx, 'operation', '')) or 'Không rõ'))

    sys_parts = []
    if win32_err is not None:
        sys_parts.append(f'WinError {_sstr(win32_err)}')
    if http_status is not None:
        sys_parts.append(f'HTTP {_sstr(http_status)}')
    if sys_parts:
        sys_val, sys_tone = ' · '.join(sys_parts), 'danger'
    else:
        sys_val, sys_tone = 'Không có mã lỗi hệ thống', 'neutral'

    dns_val, dns_tone = 'Chưa đo (bấm Kiểm tra kết nối)', 'neutral'
    try:
        probe = _sget(ctx, 'probe', None)
        v_raw = _sget(probe, 'verdict', None) if isinstance(probe, dict) else None
        v = _sstr(v_raw)
        if v:
            known_verdict = {
                'ok': 'GitHub: Kết nối tốt',
                'offline': 'Mất Internet hoàn toàn',
                'dns_blocked': 'Lỗi DNS GitHub · 1.1.1.1 OK',
                'dns_broken': 'DNS hỏng · IP trực tiếp OK',
                'blocked': 'Kết nối tới GitHub bị chặn',
                'captive_portal': 'Captive Portal (cần đăng nhập Wi-Fi)',
            }.get(v)
            dns_val = known_verdict if known_verdict is not None else _sanitize_surrogates(redact(v))
            dns_tone = 'ok' if v == 'ok' else ('warn' if v in ('dns_blocked', 'dns_broken') else 'danger')
    except Exception:  # noqa: BLE001
        dns_val, dns_tone = 'Chưa đo (bấm Kiểm tra kết nối)', 'neutral'

    disk_parts = []
    disk_low = False
    pm = _sget(ctx, 'path_manager', None)
    if pm is not None:
        try:
            app_gb = _free_gb_num(pm.app_data_dir)
            if app_gb is not None:
                disk_parts.append(f'AppData: {app_gb:.1f} GB')
                if app_gb < 1.0:
                    disk_low = True
        except Exception:  # noqa: BLE001
            pass
    g = _sget(ctx, 'game', None)
    gpath = _sstr(_sget(g, 'game_path', None))
    if gpath:
        try:
            gp = Path(gpath)
            ggb = _free_gb_num(gp if gp.exists() else gp.anchor)
            if ggb is not None:
                disk_parts.append(f'Game: {ggb:.1f} GB')
                if ggb < 1.0:
                    disk_low = True
        except Exception:  # noqa: BLE001
            pass
    disk_val = ' · '.join(disk_parts) if disk_parts else 'Không đọc được'
    disk_tone = 'warn' if disk_low else ('ok' if disk_parts else 'neutral')

    running_flag = _sbool(_sget(g, 'is_running', False), False)
    try:
        if not running_flag and g is not None:
            running_flag = is_game_process_running()
    except Exception:  # noqa: BLE001
        pass
    game_val = 'Đang chạy (StellaSora.exe)' if running_flag else 'Đã đóng'
    game_tone = 'danger' if running_flag else 'ok'

    writable, wstatus, cfa, _wdetail = _writability_summary(ctx)
    if writable is True or wstatus == 'writable':
        perm_val, perm_tone = 'Hợp lệ', 'ok'
    elif cfa or wstatus == 'cfa_blocked':
        perm_val, perm_tone = 'Bị chặn (CFA / AV)', 'danger'
    elif wstatus == 'access_denied':
        perm_val, perm_tone = 'Bị chặn (Cần quyền Quản trị)', 'danger'
    elif wstatus in ('locked', 'read_only'):
        perm_val, perm_tone = ('Đang bị khóa' if wstatus == 'locked' else 'Chỉ đọc'), 'warn'
    else:
        perm_val, perm_tone = 'Chưa kiểm tra', 'neutral'

    if target_file:
        target_label, target_val = 'Tệp mục tiêu', redact(target_file)
    elif target_url:
        target_label, target_val = 'Địa chỉ truy cập', safe_url(target_url)
    elif gpath:
        target_label, target_val = 'Thư mục game', redact(str(gpath))
    else:
        target_label, target_val = 'Tệp mục tiêu', '(không có)'

    return (
        {'label': 'Thao tác', 'value': action_val, 'tone': 'neutral'},
        {'label': 'Mã hệ thống', 'value': sys_val, 'tone': sys_tone},
        {'label': 'DNS / Kết nối', 'value': dns_val, 'tone': dns_tone},
        {'label': 'Ổ đĩa trống', 'value': disk_val, 'tone': disk_tone},
        {'label': 'Tiến trình game', 'value': game_val, 'tone': game_tone},
        {'label': 'Quyền ghi thư mục', 'value': perm_val, 'tone': perm_tone},
        {'label': target_label, 'value': target_val, 'tone': 'mono'},
    )


def _probe_lines(ctx: ErrorContext) -> list[str]:
    probe = _sget(ctx, 'probe', None)
    if not probe:
        return []
    return format_probe(probe)


def _extra_lines(ctx: ErrorContext) -> list[str]:
    extra = _sget(ctx, 'extra', None)
    if not extra:
        return []
    lines: list[str] = []
    for k, v in extra.items():
        try:
            lines.append(f'{k}: {v}')
        except Exception as exc:  # noqa: BLE001
            try:
                key_str = str(k)
            except Exception:  # noqa: BLE001
                key_str = '?'
            lines.append(f'{key_str}: (không đọc được: {type(exc).__name__})')
    return lines


def _compose_text(
    r: ErrorReport,
    ctx: ErrorContext,
    diag: Optional[error_catalog.Diagnosis],
    trace: list[str],
) -> str:
    stamp = time.strftime('%Y-%m-%d %H:%M:%S') + f' (UTC{time.strftime("%z")})'
    raw_action = _sstr(_sget(ctx, 'action', ''))
    op_str = _sstr(_sget(ctx, 'operation', ''))
    action_str = raw_action or op_str or '(không rõ)'
    progress_str = _sstr(_sget(ctx, 'progress', '')) or '(không có)'
    out = [
        f'STELLA SORA VIỆT HOÁ — MÃ LỖI {r.code} (#{r.report_id})',
        f'Nền tảng: Windows PC · Launcher v{LAUNCHER_VERSION}',
        f'Thời gian: {stamp}',
        f'Đang làm: {action_str}' + (f' [{op_str}]' if raw_action and op_str else ''),
        f'Bước cuối: {progress_str}',
        '',
        f'Tiêu đề: {r.title}',
        f'Giải thích: {r.summary}',
        'Cách xử lý đã gợi ý: ' + ' | '.join(r.steps) if r.steps else 'Cách xử lý đã gợi ý: (không)',
        f'Thông báo gốc: {r.message or "(không có)"}',
    ]
    if r.win32_error is not None or r.http_status is not None:
        w_str = _sstr(r.win32_error, '-') or '-'
        h_str = _sstr(r.http_status, '-') or '-'
        out.append(f'Mã hệ thống: WinError={w_str} · HTTP={h_str}')
    if r.target_file:
        out.append(f'Tệp mục tiêu: {r.target_file}')
    if r.target_url:
        out.append(f'Địa chỉ truy cập: {r.target_url}')
    if diag is not None and diag.wrapper:
        out.append(f'Bao ngoài: {diag.wrapper} (launcher đã hoàn tác thay đổi nếu có)')
    probe_section = _safe(_probe_lines, ctx)
    if probe_section:
        out.extend(['', '--- Đo kết nối mạng lúc lỗi ---'] + probe_section)
    out.extend(['', '--- Hệ thống ---'] + _safe(_system_lines, ctx))
    out.extend(['', '--- Game ---'] + _safe(_game_lines, ctx))
    out.extend(['', '--- GitHub / kênh cập nhật ---'] + _safe(_sync_lines, ctx))
    extra_section = _safe(_extra_lines, ctx)
    if extra_section:
        out.extend(['', '--- Thông tin thêm ---'] + extra_section)
    if diag is not None and diag.chain:
        out.extend(['', '--- Chuỗi lỗi (ngoài → trong) ---'] + [f'{i + 1}. {line}' for i, line in enumerate(diag.chain)])
    if trace:
        out.extend(['', '--- Vết lỗi (rút gọn) ---'] + trace)
    out.extend(['', '--- Nhật ký launcher (30 dòng cuối) ---'] + _safe(_log_tail, ctx))
    return redact('\n'.join(out))


def build_report(
    code: Optional[str] = None,
    *,
    exc: Optional[BaseException] = None,
    message: str = '',
    action: str = '',
    title: str = '',
    ctx: Optional[ErrorContext] = None,
    subject: Optional[str] = None,
    extra_summary: str = '',
) -> ErrorReport:
    """Create an :class:`ErrorReport`. Never raises.

    ``exc`` wins over ``code``: the exception chain is classified (see ``error_catalog.diagnose``) and ``code`` is only
    a fallback. With no exception, ``code`` names a known situation from the catalog.
    """
    safe_code = _sanitize_surrogates(_sstr(code))
    safe_title = _sanitize_surrogates(_sstr(title))
    safe_message = _sanitize_surrogates(_sstr(message))
    safe_subject = _sanitize_surrogates(_sstr(subject))
    safe_action = _sanitize_surrogates(_sstr(action))
    safe_extra_summary = _sanitize_surrogates(_sstr(extra_summary))
    if ctx is None:
        ctx = ErrorContext()
    if safe_action and not _sstr(_sget(ctx, 'action', '')):
        try:
            ctx.action = safe_action
        except Exception:  # noqa: BLE001
            pass
    try:
        diag = error_catalog.diagnose(exc, fallback=safe_code or None, subject=safe_subject or None) if exc is not None else None
        if diag is not None:
            info, final_code = diag.info, _sanitize_surrogates(_sstr(diag.code))
        else:
            final_code = safe_code or _sanitize_surrogates(_sstr(_sget(ctx, 'error_code', ''))) or 'E-UNKNOWN'
            info = error_catalog.lookup(final_code, safe_subject or 'github')

        _writable, _wstatus, cfa_flag, _wdetail = _writability_summary(ctx)
        if final_code == 'E-FILE-DENIED' and cfa_flag:
            final_code = 'E-CFA-BLOCKED'
            info = error_catalog.lookup(final_code, (diag.subject if diag else None) or safe_subject or 'github')

        raw = _sanitize_surrogates(safe_message or (diag.message if diag is not None else ''))
        win32_err, http_status, target_file, target_url = _extract_exc_metadata(exc, ctx)
        probe_text = ''
        try:
            probe_obj = _sget(ctx, 'probe', None)
            if probe_obj is not None and _sbool(probe_obj) and info.network:
                raw_vt = _sget(probe_obj, 'verdict_text', '')
                probe_text = _sanitize_surrogates(_sstr(raw_vt))
        except Exception:  # noqa: BLE001
            probe_text = ''
        summary = info.summary
        if safe_extra_summary:
            summary += '\n\n' + safe_extra_summary
        if probe_text:
            summary += '\n\nKiểm tra tự động: ' + probe_text
        summary = _sanitize_surrogates(summary)

        context_rows = _build_context_rows(ctx, win32_err, http_status, target_file, target_url)
        report = ErrorReport(
            code=final_code,
            report_id=new_report_id(),
            title=_sanitize_surrogates(safe_title or info.title),
            summary=summary,
            steps=info.steps,
            level=info.level,
            message=raw,
            text='',
            wrapper=_sanitize_surrogates(diag.wrapper if diag else ''),
            probe_text=probe_text,
            win32_error=win32_err,
            http_status=http_status,
            target_file=target_file,
            target_url=target_url,
            context_rows=context_rows,
        )
        report.text = _compose_text(report, ctx, diag, _trace_lines(exc))
        try:
            _p = _sget(ctx, 'probe', None)
            probe_verdict = _sstr(_sget(_p, 'verdict', None)) or None if isinstance(_p, dict) else None
        except Exception:  # noqa: BLE001
            probe_verdict = None
        action_name = _sstr(_sget(ctx, 'action', '')) or _sstr(_sget(ctx, 'operation', ''))
        report.payload = _redact_obj({
            'code': report.code,
            'report_id': report.report_id,
            'level': report.level,
            'title': report.title,
            'action': action_name,
            'win32_error': win32_err,
            'http_status': http_status,
            'target_file': target_file,
            'target_url': target_url,
            'wrapper': report.wrapper,
            'chain': diag.chain if diag else [],
            'probe_verdict': probe_verdict,
        })
        log.error(
            'ERROR_REPORT id=%s code=%s action=%s message=%s',
            report.report_id,
            report.code,
            _sanitize_surrogates(redact(action_name)),
            _sanitize_surrogates(redact(raw))[:400],
        )
        return report
    except Exception as internal:  # noqa: BLE001 - the error path must never raise
        log.exception('Could not build error report')
        fallback_id = new_report_id()
        try:
            internal_msg = redact(str(internal))
        except Exception:  # noqa: BLE001
            internal_msg = ''
        fallback_code = safe_code or 'E-UNKNOWN'
        text = _sanitize_surrogates(
            f'STELLA SORA VIỆT HOÁ — MÃ LỖI {fallback_code} (#{fallback_id})\n'
            f'{redact(safe_message)}\n'
            f'(Không dựng được báo cáo đầy đủ: {type(internal).__name__}({internal_msg!r}))'
        )
        info = error_catalog.lookup(fallback_code)
        return ErrorReport(
            fallback_code,
            fallback_id,
            _sanitize_surrogates(safe_title or info.title),
            _sanitize_surrogates(info.summary),
            info.steps,
            info.level,
            _sanitize_surrogates(safe_message),
            text,
        )


def export_report(report: ErrorReport, dest_path: str | Path, fmt: Optional[str] = None) -> Path:
    """Atomically exports a PII-redacted ``ErrorReport`` as ``.txt`` or ``.json``."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    chosen_fmt = (fmt or ('json' if dest.suffix.lower() == '.json' else 'txt')).strip().lower()
    if chosen_fmt == 'json':
        atomic_json(dest, report.to_dict())
        return dest
    tmp = dest.with_name(f'.{dest.name}.{uuid.uuid4().hex}.tmp')
    try:
        with tmp.open('x', encoding='utf-8', errors='replace') as f:
            f.write(_sanitize_surrogates(redact(report.text)))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def copy_text_native(text: str) -> bool:
    """Put ``text`` on the Windows clipboard without Qt (used before the UI exists). True on success."""
    if sys.platform != 'win32':
        return False
    try:
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        data = (_sanitize_surrogates(_sstr(text)) + '\0').encode('utf-16-le', 'replace')
        handle = kernel32.GlobalAlloc(0x0002, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        for _ in range(5):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.05)
        else:
            kernel32.GlobalFree(handle)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(13, handle):   # CF_UNICODETEXT
                kernel32.GlobalFree(handle)
                return False
            return True
        finally:
            user32.CloseClipboard()
    except Exception:  # noqa: BLE001
        return False
