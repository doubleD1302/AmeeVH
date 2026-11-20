"""CLI and coverage planning for standalone Stella Sora resource downloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse

from stella_resource_sync import safe_path, version_component, selected, validate_plan, sync, atomic_json, guard_snapshot


def launcher_plan(region, profile):
    from stella_resource_fetch import discover
    version, address, manifest, cdn = discover(region)
    version_component(version)
    if not manifest['source'].strip('/').startswith(f'StellaSora_{region}_'):
        raise ValueError('Launcher manifest source does not match requested region')
    files = []
    for entry in manifest['file']:
        p = safe_path(entry['path'])
        if not selected(str(p), profile):
            continue
        relative = str(safe_path(manifest['source'].strip('/') + '/' + str(p)))
        url = cdn['primary_cdn'].rstrip('/') + '/' + urllib.parse.quote(relative, safe='/')
        files.append({'path': str(p), 'size': int(entry['size']), 'algorithm': 'crc64',
                      'checksum': str(entry['hash']), 'url': url})
    return {'schema': 2, 'region': region, 'client_version': version, 'game_version': None,
            'resource_version': None, 'latest_verified': False, 'scope': 'launcher_package_only',
            'manifest_url': address, 'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            'manifest_hash_encoding': 'json_sort_keys_utf8', 'profile': profile, 'files': files,
            'coverage_note': 'All selected base-package bundles; in-game updates and external banners not resolved.'}


def main():
    tool_dir = Path(__file__).resolve().parent
    workspace = tool_dir.parents[2] if tool_dir.name == 'tools' and tool_dir.parent.name == 'StellaSora_VietHoa' else tool_dir.parent
    parser = argparse.ArgumentParser(description='Pull original regional resources without installing the game.')
    parser.add_argument('region', choices=['EN', 'CN', 'JP', 'ALL'])
    parser.add_argument('--list', '--plan', dest='plan', action='store_true', help='Inspect coverage and bytes, no payload download')
    parser.add_argument('--profile', choices=['localization', 'text'], default='localization', help='localization includes every regional asset bundle to cover textures/dependencies')
    parser.add_argument('--launcher-only', action='store_true', help='Explicitly accept base package without in-game updates')
    parser.add_argument('--allow-partial', action='store_true', help='Deprecated alias of --launcher-only')
    parser.add_argument('--sample', action='store_true', help='Verify archives, one SRT and two representative texture bundles instead of downloading every bundle')
    parser.add_argument('--output', type=Path, default=workspace / 'StellaResourceDownloads')
    args = parser.parse_args()
    errors = []
    for region in (['EN', 'CN', 'JP'] if args.region == 'ALL' else [args.region]):
        try:
            print(f'{region}: checking official metadata...', flush=True)
            if args.launcher_only or args.allow_partial:
                plan = launcher_plan(region, args.profile)
            else:
                from stella_hot_update import latest_plan
                plan = latest_plan(region, args.profile)
            validate_plan(plan)
            if args.sample:
                full = plan['files']
                chosen = [x for x in full if Path(x['path']).name in ('data.arcx', 'lua.arcx')]
                for predicate in (
                    lambda x: x['path'].lower().endswith('.srt'),
                    lambda x: x['path'].lower().endswith('.unity3d') and any(s in x['path'].lower() for s in ('gacha', 'banner')),
                    lambda x: Path(x['path']).name.lower().startswith('icon-1.') and x['path'].lower().endswith('.unity3d'),
                ):
                    candidates = [x for x in full if predicate(x) and x not in chosen]
                    if candidates:
                        chosen.append(min(candidates, key=lambda x: x['size']))
                plan = dict(plan, files=chosen, selection='verification_sample', full_selection_files=len(full),
                            full_selection_bytes=sum(x['size'] for x in full))
            plan['checked_at_utc'] = datetime.now(timezone.utc).isoformat()
            count, total = len(plan['files']), sum(x['size'] for x in plan['files'])
            dependencies = {}
            def visit(item):
                key = (item['algorithm'], item['checksum'], item['size'])
                if key in dependencies:
                    return
                dependencies[key] = item
                if 'patch' in item:
                    visit(item['base'])
                    visit(item['patch'])
            for item in plan['files']:
                if 'patch' in item:
                    visit(item['base'])
                    visit(item['patch'])
            plan['download_bytes_before_reuse'] = sum(x['size'] for x in dependencies.values() if 'patch' not in x) + sum(x['size'] for x in plan['files'] if 'patch' not in x)
            plan['storage_bytes_upper_bound'] = total + sum(x['size'] for x in dependencies.values())
            print(f'{region}: client={plan["client_version"]}, game={plan["game_version"]}, resources={plan["resource_version"]}; {count} files, {total / 1024**3:.3f} GiB; latest_verified={plan["latest_verified"]}', flush=True)
            print(f'Download before reuse: {plan["download_bytes_before_reuse"] / 1024**3:.3f} GiB; storage with patch inputs up to {plan["storage_bytes_upper_bound"] / 1024**3:.3f} GiB', flush=True)
            if not count:
                raise ValueError('Manifest selection is empty')
            version = version_component(plan['game_version'] or plan['client_version'])
            snapshot = version + '_' + (version_component(plan['resource_version']) if plan['resource_version'] else 'launcher_only')
            snapshot += '_' + args.profile + '_' + plan['manifest_sha256'][:12]
            if args.sample:
                snapshot += '_sample_v2'
            target = args.output / region / snapshot
            if args.plan:
                guard_snapshot(plan, target)
                atomic_json(target / 'plan.json', plan)
                print('Plan:', target / 'plan.json', flush=True)
            else:
                sync(plan, target)
        except (OSError, ValueError, KeyError, ImportError) as exc:
            print(f'{region}: FAILED: {exc}', flush=True)
            errors.append(region)
    if errors:
        raise ValueError('Incomplete regions: ' + ', '.join(errors))
