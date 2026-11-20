#!/usr/bin/env python3
"""Fetch regional game resources from official servers without a game install."""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request

REGIONS = {
    'EN': ('https://api-launcher-en.yo-star.com', 'DE7108E9B2842FD460F4777702727869'),
    'JP': ('https://api-launcher-jp.yo-star.com', 'DE7108E9B2842FD460F4777702727869'),
    'CN': ('https://launcher-api.yostar.net', '872550AD59A235662C5B7D5F88CEBE4B'),
}
AGENT = 'Mozilla/5.0 StellaResourceFetch/1.0'


def request(url, tag=None):
    headers = {'User-Agent': AGENT}
    if tag:
        head = {'game_tag': tag, 'time': int(time.time()), 'version': '1.6.0'}
        salt = REGIONS[tag.rsplit('_', 1)[1]][1]
        digest = hashlib.md5((json.dumps(head, separators=(',', ':')) + salt).encode()).hexdigest()
        headers['Authorization'] = json.dumps({'head': head, 'sign': digest}, separators=(',', ':'))
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45)


def json_url(url, tag=None):
    with request(url, tag) as response:
        return json.load(response)


def api(path, tag):
    result = json_url(REGIONS[tag.rsplit('_', 1)[1]][0] + path, tag)
    if result.get('code') != 200 or not isinstance(result.get('data'), dict):
        raise ValueError('Launcher API rejected request: ' + str(result.get('msg', result.get('code'))))
    return result['data']


def discover(region):
    tag = 'StellaSora_' + region
    config = api('/api/launcher/game/config', tag)
    version, basis = config['game_latest_version'], config['game_latest_file_path']
    query = urllib.parse.urlencode({'version': version, 'file_path': basis})
    address = api('/api/launcher/game/config/json?' + query, tag)['url']
    manifest = json_url(address)
    cdn = api('/api/launcher/advanced/game/download/cdn', tag)
    if not isinstance(manifest.get('file'), list) or not manifest.get('source'):
        raise ValueError('Unexpected launcher manifest')
    return version, address, manifest, cdn


def main():
    from pathlib import Path
    dependency_dir = Path(__file__).resolve().parent / '.deps'
    if dependency_dir.is_dir():
        sys.path.insert(0, str(dependency_dir))
    from stella_pull import main as pull_main
    pull_main()


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print('Error:', exc, file=sys.stderr)
        sys.exit(1)
