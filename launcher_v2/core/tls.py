"""HTTPS trust for the whole launcher.

Python on Windows only trusts the root certificates that are *already* in the Windows certificate store. Windows
downloads a missing root on demand when a browser needs it, but Python never triggers that, so on some PCs
``api.github.com`` fails with "unable to get local issuer certificate" while the same machine reads
``raw.githubusercontent.com`` fine (GitHub moved api/github.com to a Sectigo chain rooted in USERTrust ECC).

``build_context`` therefore trusts the union of the Windows store and the Mozilla bundle shipped by ``certifi``.
Verification stays strict (``CERT_REQUIRED`` + hostname check): this only adds well-known public roots.
``install`` makes it the default for every ``urllib.request.urlopen`` call in the process.
"""
from __future__ import annotations

import logging
import ssl
import urllib.request

log = logging.getLogger("launcher_v2.tls")


def _certifi_path(extra_cafile=None):
    if extra_cafile:
        return str(extra_cafile)
    try:
        import certifi

        return certifi.where()
    except Exception:  # noqa: BLE001 - certifi is a fallback, never a hard requirement
        return None


def build_context(extra_cafile=None):
    """Default verifying context plus the certifi roots (or ``extra_cafile``). Never raises."""
    ctx = ssl.create_default_context()
    cafile = _certifi_path(extra_cafile)
    if cafile:
        try:
            ctx.load_verify_locations(cafile=cafile)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not load fallback CA bundle %s: %s", cafile, exc)
    return ctx


def info(extra_cafile=None):
    """Small dict describing the trust setup (used by ``--tls-check`` and the diagnostic report)."""
    cafile = _certifi_path(extra_cafile)
    plain = ssl.create_default_context().cert_store_stats().get("x509_ca", 0)
    merged = build_context(extra_cafile).cert_store_stats().get("x509_ca", 0)
    return {
        "fallback_bundle": cafile or "không có",
        "system_roots": plain,
        "trusted_roots": merged,
        "extra_roots": merged - plain,
    }


def install(extra_cafile=None):
    """Make the merged trust the process-wide default for ``urllib.request.urlopen``. Returns :func:`info`."""
    ctx = build_context(extra_cafile)
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)))
    result = info(extra_cafile)
    log.info("TLS trust installed: %s", result)
    return result
