"""System diagnostics, non-destructive ACL/CFA writability probing, and safe ADB discovery bridge.

100% pure Python (zero Qt / PySide6 imports).
"""
from __future__ import annotations

import ctypes
import errno
import getpass
import json
import logging
import math
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]

from . import tls
from .config import LAUNCHER_VERSION, VALID_GRAPHICS_MODES
from .game_detection import is_game_process_running, read_game_versions
from .types import GameInfo

logger = logging.getLogger("launcher_v2.diagnostics")

_SAFE_USER_TOKENS = frozenset({
    "user", "admin", "administrator", "guest", "default", "public",
    "system", "windows", "stellasora", "launcher", "github", "yostar", "steam",
})
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


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if type(value) is str:
        return value
    try:
        s = str(value)
        return s if type(s) is str else (str.__str__(s) if isinstance(s, str) else default)
    except Exception:  # noqa: BLE001
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def _safe_opt_int(value: Any) -> Optional[int]:
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
    return None


def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        return getattr(obj, attr, default)
    except Exception:  # noqa: BLE001
        return default


def _safe_len(obj: Any) -> int:
    try:
        return len(obj)
    except Exception:  # noqa: BLE001
        return 0


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
    is_double_slash = full_text[end_idx:end_idx + 3] == "://"
    is_scheme_colon = (
        not is_double_slash
        and full_text[end_idx:end_idx + 1] == ":"
        and end_idx + 1 < len(full_text)
        and full_text[end_idx + 1] not in ("\\", "/", " ", "\t", "\r", "\n")
    )
    if not is_double_slash and not is_scheme_colon:
        return span, ""
    i = len(span)
    while i > 0 and (span[i - 1].isalnum() or span[i - 1] in "+.-"):
        i -= 1
    cand = span[i:]
    slen = 0
    if cand and cand[0].isalpha():
        if i == 0 or span[i - 1] in (" ", "\t", "(", "[", "{", "=", '"', "'"):
            if is_double_slash or cand.lower() in _MAILTO_SCHEMES:
                slen = len(cand)
        elif is_double_slash:
            lc = cand.lower()
            for sch in _KNOWN_SCHEMES:
                if lc.endswith(sch):
                    slen = len(sch)
                    break
    if not slen:
        return span, ""
    cut = len(span) - slen
    if cut > 0 and span[cut - 1] in (" ", "\t"):
        while cut > 0 and span[cut - 1] in (" ", "\t"):
            cut -= 1
    return span[:cut], span[cut:]


def _trim_before_adjacent_drive(span: str, full_text: str, end_idx: int) -> tuple[str, str]:
    if end_idx + 1 < len(full_text) and full_text[end_idx] == ":" and full_text[end_idx + 1] in ("\\", "/"):
        if span and span[-1].isascii() and span[-1].isalpha():
            cut = len(span) - 1
            while cut > 0 and span[cut - 1] in (" ", "\t"):
                cut -= 1
            return span[:cut], span[cut:]
    return span, ""


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
            if chunk[dpos:dpos + 3] == "://" or (dpos + 1 < len(chunk) and chunk[dpos] == ":"):
                span, sch_tail = _split_scheme_tail(span, chunk, dpos)
                tail = sch_tail + tail
        else:
            span = chunk
            tail = ""
            if idx + 2 < n and span and span[-1] in (" ", "\t"):
                stripped = span.rstrip(" \t")
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
        rprefix = root[:13] if root[0] == "%" else root[:2]
        append(rprefix)
        append(tail_sub(r"\1%USERNAME%", root[len(rprefix):] + span))
        if tail:
            append(tail)
    res = "".join(out)
    return res, (_HAS_UNREDACTED_USERS.search(res) is not None)


def _redact_unc_span(m: re.Match[str]) -> str:
    span = m.group(0)
    if _HAS_UNREDACTED_USERS.search(span) is None:
        return span
    suffix = ""
    end_idx = m.end()
    if end_idx < len(m.string) and m.string[end_idx] == ":":
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
            elif part.startswith("\\\\") and _HAS_UNREDACTED_USERS.search(part) is not None:
                rebuilt.append(_USERS_UNC_TAIL.sub(r"\1%USERNAME%", part))
            else:
                rebuilt.append(part)
        return "".join(rebuilt) + suffix
    return _USERS_UNC_TAIL.sub(r"\1%USERNAME%", span) + suffix


def _redact_tail_span(m: re.Match[str], head_re: re.Pattern[str], required_prefix: str) -> str:
    span = m.group(0)
    suffix = ""
    end_idx = m.end()
    if end_idx < len(m.string) and m.string[end_idx] == ":":
        span, suffix = _split_scheme_tail(span, m.string, end_idx)
        if not suffix:
            span, suffix = _trim_before_adjacent_drive(span, m.string, end_idx)
    up_idx = span.lower().find("%userprofile%")
    if up_idx != -1:
        cut = up_idx
        while cut > 0 and span[cut - 1] in (" ", "\t"):
            cut -= 1
        suffix = span[cut:] + suffix
        span = span[:cut]
    parts = _ADJACENT_PATH_SPLIT.split(span) if _ADJACENT_PATH_SPLIT.search(span) is not None else [span]
    rebuilt: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            rebuilt.append(part)
            continue
        if not part.startswith(required_prefix) or (required_prefix == "\\" and part.startswith("\\\\")):
            rebuilt.append(part)
            continue
        if _HAS_UNREDACTED_USERS.search(part) is None:
            rebuilt.append(part)
            continue
        if part.lower().count("users") <= 1:
            m_head = head_re.match(part)
            if not m_head:
                rebuilt.append(part)
                continue
            prefix, body = m_head.group(1), m_head.group(2)
            sep_idx = -1
            for ch_idx, ch in enumerate(body):
                if ch in ("/", "\\"):
                    sep_idx = ch_idx
                    break
            if sep_idx != -1:
                first_seg = body[:sep_idx]
                rest = body[sep_idx:]
                m_seg = _POSIX_USER_SEG.match(first_seg)
                if m_seg:
                    rebuilt.append(f"{prefix}%USERNAME%{first_seg[m_seg.end():]}{rest}")
                else:
                    rebuilt.append(part)
                continue
            stripped = body.rstrip(" \t")
            trailing_ws = body[len(stripped):]
            m_seg = _POSIX_USER_SEG.match(stripped)
            if m_seg:
                end_seg = m_seg.end()
                while end_seg > 0 and stripped[end_seg - 1] in (" ", "\t"):
                    end_seg -= 1
                if end_seg > 0:
                    rebuilt.append(f"{prefix}%USERNAME%{stripped[end_seg:]}{trailing_ws}")
                    continue
            rebuilt.append(part)
        else:
            rebuilt.append(_USERS_WIN_TAIL.sub(r"\1%USERNAME%", part))
    return "".join(rebuilt) + suffix


def _redact_rooted_win_span(m: re.Match[str]) -> str:
    return _redact_tail_span(m, _ROOTED_HEAD, "\\")


def _redact_posix_span(m: re.Match[str]) -> str:
    return _redact_tail_span(m, _POSIX_HEAD, "/")


def _sanitize_surrogates(text: Any) -> str:
    """Replace lone UTF-16 surrogates so UTF-8 encoding and JSON serialization never raise."""
    if type(text) is not str:
        text = _safe_str(text)
    if text.isascii():
        return text
    return text.encode("utf-8", "replace").decode("utf-8")


def _home_variants() -> list[str]:
    out = []
    home_raw: Optional[str] = None
    try:
        home_raw = str(Path.home())
    except Exception:  # noqa: BLE001
        home_raw = None
    for raw in (os.environ.get("USERPROFILE"), home_raw):
        if raw:
            norm = str(raw).rstrip("\\/")
            if len(norm) >= 4:
                out.append(norm)
    return sorted(set(out), key=lambda v: (-len(v), v))


def _username_variants() -> list[str]:
    out: list[str] = []
    candidates = [os.environ.get("USERNAME")]
    try:
        candidates.append(getpass.getuser())
    except Exception:  # noqa: BLE001
        pass
    for raw in candidates:
        name = str(raw or "").strip()
        if len(name) >= 3 and name.casefold() not in _SAFE_USER_TOKENS:
            out.append(name)
    return sorted(set(out), key=lambda v: (-len(v), v))


def _redact_pii(text: Any) -> str:
    """Redacts user profile paths, Windows usernames, and URL credentials/queries."""
    out = _safe_str(text)
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


# Keep legacy internal helper name available
_redact_user_home = _redact_pii


def is_process_admin() -> bool:
    """Returns True when the current process holds Windows Administrator privileges."""
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def get_os_build_info() -> dict[str, str]:
    """Reads Windows version, display release (e.g. 23H2), and build/UBR without Qt."""
    sys_name = platform.system()
    release = platform.release()
    arch = platform.machine()
    build = ""
    ubr = ""
    display_ver = ""
    product_name = f"{sys_name} {release}".strip()

    if sys.platform == "win32" and winreg is not None:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
                def _q(name: str) -> str:
                    try:
                        val, _ = winreg.QueryValueEx(k, name)
                        return str(val or "").strip()
                    except OSError:
                        return ""

                raw_prod = _q("ProductName")
                build = _q("CurrentBuildNumber") or _q("CurrentBuild")
                ubr = _q("UBR")
                display_ver = _q("DisplayVersion") or _q("ReleaseId")
                if raw_prod:
                    product_name = raw_prod
                try:
                    if build and int(build) >= 22000 and "Windows 10" in product_name:
                        product_name = product_name.replace("Windows 10", "Windows 11", 1)
                except ValueError:
                    pass
        except OSError:
            pass

    build_str = f"{build}.{ubr}" if build and ubr else build
    parts = [product_name]
    if display_ver:
        parts.append(display_ver)
    if build_str:
        parts.append(f"(Build {build_str})")
    summary = " ".join(p for p in parts if p)
    return {
        "os_name": sys_name,
        "os_release": release,
        "os_arch": arch,
        "product_name": product_name,
        "display_version": display_ver,
        "build": build_str,
        "summary": summary,
    }


def get_system_dpi_info() -> str:
    """Queries system DPI and process DPI awareness via Win32 ctypes (zero Qt)."""
    if sys.platform != "win32":
        return "96 DPI (100%)"
    dpi = 96
    awareness_label = ""
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        if hasattr(user32, "GetDpiForSystem"):
            user32.GetDpiForSystem.restype = ctypes.c_uint
            val = int(user32.GetDpiForSystem())
            if val > 0:
                dpi = val
    except Exception:  # noqa: BLE001
        pass
    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        if hasattr(shcore, "GetProcessDpiAwareness"):
            awareness = ctypes.c_int(0)
            if shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness)) == 0:
                awareness_label = {
                    0: "Unaware",
                    1: "System Aware",
                    2: "Per-Monitor V2",
                }.get(awareness.value, f"Mode {awareness.value}")
    except Exception:  # noqa: BLE001
        pass
    pct = int(round((dpi / 96.0) * 100))
    if awareness_label:
        return f"{dpi} DPI ({pct}%, {awareness_label})"
    return f"{dpi} DPI ({pct}%)"


def _read_cfa_registry_enabled() -> Optional[bool]:
    """Read-only check of Windows Defender Controlled Folder Access state."""
    if sys.platform != "win32" or winreg is None:
        return None
    subkey = r"SOFTWARE\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as k:
            val, _ = winreg.QueryValueEx(k, "EnableControlledFolderAccess")
            return int(val) == 1
    except OSError:
        return None


def _is_protected_windows_path(path: Path) -> bool:
    try:
        p_str = _safe_str(path)
        if not p_str:
            return False
        norm = os.path.normcase(os.path.abspath(p_str)).replace("/", "\\")
    except Exception:  # noqa: BLE001
        return False
    protected_roots: list[str] = []
    for env_key in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "SystemRoot", "WINDIR"):
        raw = os.environ.get(env_key)
        if raw:
            protected_roots.append(os.path.normcase(os.path.abspath(raw)).replace("/", "\\").rstrip("\\"))
    for fallback in (r"c:\program files", r"c:\program files (x86)", r"c:\windows"):
        if fallback not in protected_roots:
            protected_roots.append(fallback)
    return any(norm == root or norm.startswith(root + "\\") for root in protected_roots)


def _has_readonly_attr(path: Path) -> bool:
    if sys.platform == "win32":
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:
                return bool(attrs & 0x1)  # FILE_ATTRIBUTE_READONLY
        except Exception:  # noqa: BLE001
            pass
    try:
        mode = path.stat().st_mode
        return not bool(mode & stat.S_IWUSR)
    except Exception:  # noqa: BLE001
        return False


def _default_write_probe(probe_path: Path) -> None:
    fd = os.open(str(probe_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)


@dataclass(frozen=True)
class WritabilityProbeResult:
    target_dir: str
    writable: Optional[bool]
    status: str                  # "writable" | "cfa_blocked" | "access_denied" | "read_only" | "locked" | "missing" | "unknown"
    cfa_suspected: bool
    cfa_registry_enabled: Optional[bool]
    is_protected_path: bool
    win32_error: Optional[int]
    detail: str


def probe_dir_writability(
    target_dir: str | Path | None,
    *,
    write_probe_fn: Optional[Callable[[Path], None]] = None,
    cfa_reader: Optional[Callable[[], Optional[bool]]] = None,
    is_admin: Optional[bool] = None,
) -> WritabilityProbeResult:
    """Non-destructively probes directory writability using a unique temporary file.

    Creates ``<target_dir>/.ssvh_write_probe_<uuid>.tmp`` with ``O_CREAT|O_EXCL`` (0 bytes)
    and removes it immediately in ``finally:``. Never touches any game file or folder.
    """
    tdir_str = _safe_str(target_dir)
    if not tdir_str:
        return WritabilityProbeResult(
            target_dir="",
            writable=None,
            status="missing",
            cfa_suspected=False,
            cfa_registry_enabled=None,
            is_protected_path=False,
            win32_error=None,
            detail="Chưa xác định thư mục đích",
        )

    try:
        p = Path(target_dir)
        is_dir = p.is_dir()
    except Exception as exc:  # noqa: BLE001
        return WritabilityProbeResult(
            target_dir=tdir_str,
            writable=None,
            status="unknown",
            cfa_suspected=False,
            cfa_registry_enabled=None,
            is_protected_path=False,
            win32_error=_safe_opt_int(_safe_getattr(exc, "winerror", None)) if isinstance(exc, OSError) else None,
            detail=f"{type(exc).__name__}: {_safe_str(exc)}",
        )
    p_str = _safe_str(p, tdir_str)
    if not is_dir:
        return WritabilityProbeResult(
            target_dir=p_str,
            writable=None,
            status="missing",
            cfa_suspected=False,
            cfa_registry_enabled=None,
            is_protected_path=_is_protected_windows_path(p),
            win32_error=None,
            detail="Thư mục chưa tồn tại",
        )

    protected = _is_protected_windows_path(p)
    if cfa_reader is not None:
        try:
            raw_cfa = cfa_reader()
        except Exception:  # noqa: BLE001
            raw_cfa = None
        cfa_reg = None if raw_cfa is None else _safe_bool(raw_cfa)
    else:
        cfa_reg = _read_cfa_registry_enabled()
    admin_flag = is_process_admin() if is_admin is None else _safe_bool(is_admin)
    probe_fn = write_probe_fn or _default_write_probe
    probe_file = p / f".ssvh_write_probe_{uuid.uuid4().hex}.tmp"

    try:
        probe_fn(probe_file)
        return WritabilityProbeResult(
            target_dir=p_str,
            writable=True,
            status="writable",
            cfa_suspected=False,
            cfa_registry_enabled=cfa_reg,
            is_protected_path=protected,
            win32_error=None,
            detail="Hợp lệ",
        )
    except OSError as exc:
        win = _safe_opt_int(_safe_getattr(exc, "winerror", None))
        eno = _safe_opt_int(_safe_getattr(exc, "errno", None))
        if win in (32, 33):
            return WritabilityProbeResult(
                target_dir=p_str,
                writable=False,
                status="locked",
                cfa_suspected=False,
                cfa_registry_enabled=cfa_reg,
                is_protected_path=protected,
                win32_error=win,
                detail=f"Tệp/thư mục đang bị khóa (WinError {win})",
            )
        if win == 19 or eno == errno.EROFS:
            return WritabilityProbeResult(
                target_dir=p_str,
                writable=False,
                status="read_only",
                cfa_suspected=False,
                cfa_registry_enabled=cfa_reg,
                is_protected_path=protected,
                win32_error=win,
                detail="Ổ đĩa hoặc phương tiện chỉ đọc",
            )
        if isinstance(exc, PermissionError) or win == 5 or eno in (errno.EACCES, errno.EPERM):
            eff_win = win if win is not None else 5
            readonly_attr = _has_readonly_attr(p)
            cfa_hit = bool(
                cfa_reg is True
                or admin_flag
                or (not protected and not readonly_attr)
            )
            if cfa_hit:
                return WritabilityProbeResult(
                    target_dir=p_str,
                    writable=False,
                    status="cfa_blocked",
                    cfa_suspected=True,
                    cfa_registry_enabled=cfa_reg,
                    is_protected_path=protected,
                    win32_error=eff_win,
                    detail="Bị chặn ghi (nghi Controlled Folder Access / Diệt virus)",
                )
            return WritabilityProbeResult(
                target_dir=p_str,
                writable=False,
                status="access_denied",
                cfa_suspected=False,
                cfa_registry_enabled=cfa_reg,
                is_protected_path=protected,
                win32_error=eff_win,
                detail="Bị chặn (Cần quyền Quản trị)",
            )
        return WritabilityProbeResult(
            target_dir=p_str,
            writable=False,
            status="unknown",
            cfa_suspected=False,
            cfa_registry_enabled=cfa_reg,
            is_protected_path=protected,
            win32_error=win,
            detail=f"{type(exc).__name__}: {_safe_str(exc)}",
        )
    except Exception as exc:  # noqa: BLE001
        return WritabilityProbeResult(
            target_dir=p_str,
            writable=False,
            status="unknown",
            cfa_suspected=False,
            cfa_registry_enabled=cfa_reg,
            is_protected_path=protected,
            win32_error=None,
            detail=f"{type(exc).__name__}: {_safe_str(exc)}",
        )
    finally:
        try:
            probe_file.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def _safe_url(url: Any) -> str:
    """scheme://host[:port]/path only (no credentials, query or fragment), plus PII redaction."""
    if url is None:
        return ""
    try:
        import urllib.parse

        raw_str = _safe_str(url)
        if not raw_str:
            return ""
        raw = raw_str.replace("\\", "/") if raw_str.lstrip().lower().startswith("file:") else raw_str
        u = urllib.parse.urlparse(raw)
        scheme = u.scheme.lower()
        if scheme == "file":
            if not u.hostname and not u.path.strip("/"):
                return ""
            host = (f"[{u.hostname}]" if ":" in u.hostname else u.hostname) if u.hostname else ""
            u_port = u.port
            port = f":{u_port}" if u_port else ""
            clean_path = re.sub(r"/+", "/", u.path)
            return _redact_pii(f"{u.scheme}://{host}{port}{clean_path}")
        if scheme not in ("http", "https") or not u.hostname:
            return ""
        host = f"[{u.hostname}]" if ":" in u.hostname else u.hostname
        u_port = u.port
        port = f":{u_port}" if u_port else ""
        clean_path = re.sub(r"/+", "/", u.path)
        return _redact_pii(f"{u.scheme}://{host}{port}{clean_path}")
    except Exception:  # noqa: BLE001
        return ""


def _safe_pm_path(pm: Any, prop_name: str, fallback_attr: str = "") -> str:
    if pm is None:
        return ""
    try:
        val = getattr(pm, prop_name)
        return _safe_str(val) if val is not None else ""
    except Exception:  # noqa: BLE001
        if fallback_attr:
            try:
                raw = getattr(pm, fallback_attr, None)
                return _safe_str(raw) if raw is not None else ""
            except Exception:  # noqa: BLE001
                return ""
        return ""


@dataclass
class SystemReport:
    timestamp: str
    os_name: str
    os_release: str
    os_arch: str
    python_version: str
    is_frozen: bool
    screen_dpi_info: str
    launcher_dir: str
    app_data_dir: str
    backup_dir: str
    game_detected: bool
    game_source: str
    game_path: str
    game_executable_found: bool
    game_running: bool
    disk_free_gb: float
    receipt_summary: Optional[Dict[str, Any]] = None
    launcher_version: str = LAUNCHER_VERSION
    game_version: str = "unknown"
    resource_version: str = "unknown"
    game_disk_free_gb: float = 0.0
    # v2.0 diagnostic fields (optional defaults preserve positional legacy callers)
    os_build: str = ""
    is_admin: bool = False
    folder_writable: Optional[bool] = None
    writability_status: str = "unknown"
    writability_detail: str = ""
    cfa_suspected: bool = False
    win32_error_code: Optional[int] = None
    http_status: Optional[int] = None
    target_file: str = ""
    target_url: str = ""
    tls_info: Dict[str, Any] = field(default_factory=dict)
    graphics_mode: str = "auto"
    migration_status: str = ""

    def to_dict(self) -> Dict[str, Any]:
        def _safe_key(k: Any, *, redact: bool = False) -> str:
            ks = _safe_str(k, "?")
            return _redact_pii(ks) if redact else _sanitize_surrogates(ks)

        def _sanitize_value(val: Any, *, redact: bool = False, seen: Optional[set[int]] = None) -> Any:
            if type(val) is str:
                return _redact_pii(val) if redact else _sanitize_surrogates(val)
            if isinstance(val, str):
                s = _safe_str(val)
                return _redact_pii(s) if redact else _sanitize_surrogates(s)
            if isinstance(val, Path):
                s = _safe_str(val)
                return _redact_pii(s) if redact else _sanitize_surrogates(s)
            if isinstance(val, dict):
                if seen is None:
                    seen = set()
                obj_id = id(val)
                if obj_id in seen:
                    return "[CyclicRef]"
                seen.add(obj_id)
                try:
                    items = list(val.items())
                    return {
                        _safe_key(k, redact=redact): _sanitize_value(v, redact=redact, seen=seen)
                        for k, v in items
                    }
                except Exception:  # noqa: BLE001
                    return {}
                finally:
                    seen.discard(obj_id)
            if isinstance(val, (list, tuple)):
                if seen is None:
                    seen = set()
                obj_id = id(val)
                if obj_id in seen:
                    return "[CyclicRef]"
                seen.add(obj_id)
                try:
                    seq = list(val)
                    return [_sanitize_value(v, redact=redact, seen=seen) for v in seq]
                except Exception:  # noqa: BLE001
                    return []
                finally:
                    seen.discard(obj_id)
            if val is None or type(val) in (bool, int):
                return val
            if type(val) is float:
                return val if math.isfinite(val) else None
            if isinstance(val, bool):
                return _safe_bool(val)
            if isinstance(val, int):
                return _safe_opt_int(val)
            if isinstance(val, float):
                try:
                    v = float(val)
                    return v if (type(v) is float and math.isfinite(v)) else None
                except Exception:  # noqa: BLE001
                    return None
            s = _safe_str(val)
            if not s:
                return None
            return _redact_pii(s) if redact else _sanitize_surrogates(s)

        _SAFE_TECH_FIELDS = frozenset({
            "timestamp", "os_name", "os_release", "os_version", "os_build",
            "os_arch", "arch", "python_version", "graphics_mode",
            "writability_status", "running_exe_name",
        })
        data: Dict[str, Any] = {
            f.name: _safe_getattr(self, f.name, None)
            for f in fields(self)
        }
        for key in list(data.keys()):
            if key == "target_url":
                val = data.get(key)
                if val is not None and _safe_str(val):
                    data[key] = _safe_url(val)
                elif val is not None:
                    data[key] = ""
            elif key in _SAFE_TECH_FIELDS:
                data[key] = _sanitize_value(data[key], redact=False)
            else:
                data[key] = _sanitize_value(data[key], redact=True)
        return data

    def to_text(self) -> str:
        w_status = _safe_str(self.writability_status, "unknown")
        w_detail = _safe_str(self.writability_detail)
        writable_txt = (
            w_detail
            or {
                "writable": "Hợp lệ",
                "cfa_blocked": "Bị chặn (CFA / Diệt virus)",
                "access_denied": "Bị chặn (Cần quyền Quản trị)",
                "read_only": "Chỉ đọc",
                "locked": "Đang bị khóa",
                "missing": "Thư mục không tồn tại",
            }.get(w_status, "Chưa kiểm tra")
        )
        os_build_str = _safe_str(self.os_build) or (f"{_safe_str(self.os_name)} {_safe_str(self.os_release)}".strip())
        lines = [
            "=== BÁO CÁO CHẨN ĐOÁN HỆ THỐNG STELLA SORA LAUNCHER ===",
            f"Thời gian tạo: {_safe_str(self.timestamp)}",
            f"Phiên bản Launcher: v{_safe_str(self.launcher_version)} (Đóng gói EXE: {_safe_bool(self.is_frozen)})",
            f"Hệ điều hành: {os_build_str} ({_safe_str(self.os_arch)})",
            f"Quyền Quản trị: {'Có' if _safe_bool(self.is_admin) else 'Không'}",
            f"Môi trường Python: {_safe_str(self.python_version)}",
            f"Độ phân giải / DPI: {_safe_str(self.screen_dpi_info)}",
            f"Chế độ đồ họa: {_safe_str(self.graphics_mode)}",
            f"Trạng thái di trú r02: {_safe_str(self.migration_status) or 'Chưa ghi nhận'}",
            f"Thư mục ứng dụng: {_safe_str(self.launcher_dir)}",
            f"Thư mục cấu hình (AppData): {_safe_str(self.app_data_dir)}",
            f"Thư mục sao lưu: {_safe_str(self.backup_dir)}",
            f"Dung lượng trống ổ AppData: {_safe_float(self.disk_free_gb):.2f} GB",
            f"Dung lượng trống ổ cài game: {_safe_float(self.game_disk_free_gb):.2f} GB",
            f"Quyền ghi thư mục đích: {writable_txt}",
        ]
        if self.win32_error_code is not None or self.http_status is not None:
            w_code = "-" if self.win32_error_code is None else _safe_str(self.win32_error_code, "-")
            h_code = "-" if self.http_status is None else _safe_str(self.http_status, "-")
            lines.append(f"Mã hệ thống: WinError={w_code} · HTTP={h_code}")
        t_file = _safe_str(self.target_file)
        if t_file:
            lines.append(f"Tệp mục tiêu: {t_file}")
        if self.target_url is not None and _safe_str(self.target_url):
            lines.append(f"URL mục tiêu: {_safe_url(self.target_url)}")
        if isinstance(self.tls_info, dict) and _safe_len(self.tls_info) > 0:
            lines.append(
                f"TLS Root Store: hệ thống {_safe_str(self.tls_info.get('system_roots', '?'), '?')} · "
                f"tổng {_safe_str(self.tls_info.get('trusted_roots', '?'), '?')} (+{_safe_str(self.tls_info.get('extra_roots', 0), '0')} certifi)"
            )
        lines.extend([
            "",
            "--- Trạng thái Game ---",
            f"Phát hiện game: {'Có' if _safe_bool(self.game_detected) else 'Không'}",
            f"Nguồn phát hiện: {_safe_str(self.game_source)}",
            f"Phiên bản Game / Tài nguyên: {_safe_str(self.game_version)} / {_safe_str(self.resource_version)}",
            f"Đường dẫn cài đặt: {_safe_str(self.game_path) or 'Chưa xác định'}",
            f"Tệp thực thi game: {'Tồn tại' if _safe_bool(self.game_executable_found) else 'Không tìm thấy'}",
            f"Tiến trình đang chạy: {'CẢNH BÁO: ĐANG CHẠY' if _safe_bool(self.game_running) else 'Không chạy'}",
            "",
        ])
        if isinstance(self.receipt_summary, dict) and _safe_len(self.receipt_summary) > 0:
            _files = self.receipt_summary.get('files')
            _files_count = _safe_len(_files) if isinstance(_files, (dict, list, tuple, set)) else 0
            raw_pv = self.receipt_summary.get('patch_version')
            if raw_pv is None or _safe_str(raw_pv) == '':
                raw_pv = self.receipt_summary.get('version', 'N/A')
            patch_ver = _safe_str(raw_pv, 'N/A')
            inst_at = _safe_str(self.receipt_summary.get('installed_at', 'N/A'), 'N/A')
            lines.extend([
                "--- Biên bản cài đặt hiện tại ---",
                f"Phiên bản patch: {patch_ver}",
                f"Thời gian cài: {inst_at}",
                f"Số tệp đã vá: {_files_count}",
            ])
        else:
            lines.append("--- Biên bản cài đặt hiện tại: Chưa cài đặt bản vá ---")

        return _redact_pii("\n".join(lines))


def _read_graphics_mode(path_manager, config_data: Optional[dict[str, Any]]) -> str:
    if isinstance(config_data, dict):
        try:
            gm = config_data.get("graphics_mode")
            if type(gm) is str and gm in VALID_GRAPHICS_MODES:
                return gm
        except Exception:  # noqa: BLE001
            pass
    if path_manager is not None:
        try:
            cfg_file = Path(path_manager.config_file)
            if cfg_file.is_file():
                parsed = json.loads(cfg_file.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    gm = parsed.get("graphics_mode")
                    if type(gm) is str and gm in VALID_GRAPHICS_MODES:
                        return gm
        except Exception:  # noqa: BLE001
            pass
    return "auto"


def _read_migration_status(path_manager) -> str:
    if path_manager is None:
        return ""
    try:
        marker = getattr(path_manager, "migration_marker_file", None)
        if marker and Path(marker).is_file():
            data = json.loads(Path(marker).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return str(data.get("status") or "")
    except Exception:  # noqa: BLE001
        pass
    return ""


class DiagnosticsCollector:
    """Collects system, environment, writability, TLS, and game diagnostic information."""

    @staticmethod
    def collect(
        path_manager,
        game_info: Optional[GameInfo] = None,
        screen_info: str = "",
        *,
        win32_error_code: Optional[int] = None,
        http_status: Optional[int] = None,
        target_file: str = "",
        target_url: str = "",
        check_writability: bool = True,
        refresh_running: bool = True,
        config_data: Optional[dict[str, Any]] = None,
    ) -> SystemReport:
        import datetime

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        g = game_info if game_info is not None else GameInfo()

        g_path = _safe_str(_safe_getattr(g, "game_path", None))
        g_installed = _safe_bool(_safe_getattr(g, "installed", False))
        g_platform = _safe_str(_safe_getattr(g, "platform", ""))
        g_running_attr = _safe_bool(_safe_getattr(g, "is_running", False))

        free_bytes = 0
        try:
            free_bytes = shutil.disk_usage(path_manager.app_data_dir).free
        except Exception:
            try:
                free_bytes = shutil.disk_usage("C:\\").free
            except Exception:
                pass
        free_gb = free_bytes / (1024 ** 3)

        game_free_gb = free_gb
        if g_path:
            try:
                gp = Path(g_path)
                target_check = gp if gp.exists() else gp.anchor
                if target_check:
                    game_free_gb = shutil.disk_usage(target_check).free / (1024 ** 3)
            except Exception:
                pass

        receipt_summary = None
        receipt_file = None
        try:
            receipt_file = (Path(g_path) / ".vietnamese_patch_receipt.json") if g_path else path_manager.receipt_file
        except Exception:  # noqa: BLE001
            receipt_file = None
        if receipt_file is not None:
            try:
                rf = Path(receipt_file)
                if rf.is_file():
                    with open(rf, "r", encoding="utf-8") as f:
                        receipt_summary = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read patch receipt: {e}")

        exe_found = False
        game_ver = _safe_str(_safe_getattr(g, "version", "unknown"), "unknown") or "unknown"
        res_ver = _safe_str(_safe_getattr(g, "resource_version", "unknown"), "unknown") or "unknown"
        if g_path:
            try:
                gp = Path(g_path)
                exe_path = gp / "StellaSora.exe"
                exe_found = exe_path.is_file()
                if (game_ver == "unknown" or res_ver == "unknown") and gp.is_dir():
                    v = read_game_versions(gp)
                    if game_ver == "unknown":
                        game_ver = _safe_str(v.get("game", "unknown"), "unknown") or "unknown"
                    if res_ver == "unknown":
                        res_ver = _safe_str(v.get("resource", "unknown"), "unknown") or "unknown"
            except Exception:  # noqa: BLE001
                pass

        running = g_running_attr
        if _safe_bool(refresh_running, True):
            try:
                running = is_game_process_running() or g_running_attr
            except Exception:  # noqa: BLE001
                running = g_running_attr

        admin_flag = is_process_admin()
        os_info = get_os_build_info()
        dpi_str = _safe_str(screen_info) or get_system_dpi_info()

        try:
            tls_data = dict(tls.info())
        except Exception as exc:  # noqa: BLE001
            tls_data = {"error": _safe_str(exc) or type(exc).__name__}

        w_res: Optional[WritabilityProbeResult] = None
        if _safe_bool(check_writability, True):
            try:
                probe_target = g_path if (g_path and Path(g_path).is_dir()) else path_manager.app_data_dir
            except Exception:  # noqa: BLE001
                try:
                    probe_target = getattr(path_manager, "_app", None)
                except Exception:  # noqa: BLE001
                    probe_target = None
            try:
                w_res = probe_dir_writability(probe_target, is_admin=admin_flag)
            except Exception:  # noqa: BLE001
                w_res = None

        launcher_dir_str = _safe_pm_path(path_manager, "resource_dir", "_resource")
        app_data_dir_str = _safe_pm_path(path_manager, "app_data_dir", "_app")
        backup_dir_str = _safe_pm_path(path_manager, "backup_root")

        return SystemReport(
            timestamp=now,
            os_name=os_info["os_name"],
            os_release=os_info["os_release"],
            os_arch=os_info["os_arch"],
            python_version=platform.python_version(),
            is_frozen=bool(getattr(sys, "frozen", False)),
            screen_dpi_info=dpi_str,
            launcher_dir=launcher_dir_str,
            app_data_dir=app_data_dir_str,
            backup_dir=backup_dir_str,
            game_detected=g_installed,
            game_source=g_platform,
            game_path=g_path,
            game_executable_found=exe_found,
            game_running=running,
            disk_free_gb=free_gb,
            receipt_summary=receipt_summary,
            launcher_version=LAUNCHER_VERSION,
            game_version=game_ver,
            resource_version=res_ver,
            game_disk_free_gb=game_free_gb,
            os_build=os_info["summary"],
            is_admin=admin_flag,
            folder_writable=w_res.writable if w_res is not None else None,
            writability_status=w_res.status if w_res is not None else "unknown",
            writability_detail=w_res.detail if w_res is not None else "",
            cfa_suspected=bool(w_res.cfa_suspected) if w_res is not None else False,
            win32_error_code=win32_error_code,
            http_status=http_status,
            target_file=_redact_pii(target_file),
            target_url=_safe_url(target_url),
            tls_info=tls_data,
            graphics_mode=_read_graphics_mode(path_manager, config_data),
            migration_status=_read_migration_status(path_manager),
        )


class AdbBridge:
    """Safe ADB bridge for emulator discovery and status check.

    Adheres strictly to read-only discovery. Never modifies or pushes files
    automatically without user instruction.
    """

    KNOWN_SEARCH_LOCATIONS = [
        r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\Program Files (x86)\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"D:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\LDPlayer\LDPlayer9\adb.exe",
        r"D:\LDPlayer\LDPlayer9\adb.exe",
        r"C:\Program Files\nox\bin\nox_adb.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
    ]

    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = custom_adb_path or self.locate_adb()

    @classmethod
    def locate_adb(cls) -> Optional[str]:
        """Find adb.exe in PATH or well-known emulator paths."""
        which_path = shutil.which("adb")
        if which_path and os.path.isfile(which_path):
            return which_path

        for loc in cls.KNOWN_SEARCH_LOCATIONS:
            if os.path.isfile(loc):
                return loc

        return None

    def is_available(self) -> bool:
        return bool(self.adb_path and os.path.isfile(self.adb_path))

    def list_devices(self) -> List[Dict[str, str]]:
        """Run 'adb devices -l' safely with a short timeout."""
        if not self.is_available():
            return []

        devices = []
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            cmd = [self.adb_path, "devices", "-l"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=creationflags,
            )
            if proc.returncode == 0:
                lines = proc.stdout.splitlines()
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        state = parts[1]
                        details = " ".join(parts[2:]) if len(parts) > 2 else ""
                        devices.append({
                            "serial": serial,
                            "state": state,
                            "details": details,
                        })
        except Exception as e:
            logger.warning(f"Error querying adb devices: {e}")

        return devices
