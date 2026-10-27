"""Version and compatibility decisions for the visible update controls."""
import re

def version_parts(value):
    match = re.fullmatch(r'v?(\d+(?:\.\d+){0,3})', str(value or '').strip(), re.I)
    if not match:
        return None
    parts = tuple(int(p) for p in match.group(1).split('.'))
    return parts + (0,) * (4 - len(parts))

def newer(latest, installed):
    latest, installed = version_parts(latest), version_parts(installed)
    return latest is not None and installed is not None and latest > installed

def matches(observed, expected):
    # Wildcards or client-only values cannot prove compatibility for a write.
    observed, expected = str(observed or '').strip(), str(expected or '').strip()
    if observed.lower() in ('', 'unknown', '*', 'all') or expected.lower() in ('', 'unknown', '*', 'all'):
        return False
    if any(c in observed or c in expected for c in '*;,|'):
        return False
    return observed == expected

def translation_state(sync, game):
    if sync.get('release_status') != 'online' or sync.get('manifest_status') != 'online':
        return {'available': False, 'can_install': False, 'message': 'Chưa có bảng kê bản Việt hoá đáng tin cậy.'}
    version = sync.get('translation_version')
    receipt = getattr(game, 'installed_receipt', None)
    if not getattr(game, 'installed', False):
        return {'available': False, 'can_install': False, 'message': f'Bản Việt hoá: {version}. Hãy chọn thư mục game.'}
    if matches(getattr(game, 'version', ''), sync.get('translation_game')) and matches(getattr(game, 'resource_version', ''), sync.get('translation_resource')):
        version_note = 'Phiên bản game và tài nguyên khớp bảng kê; chưa xác minh hiển thị trong game.'
    else:
        version_note = 'Phiên bản game hoặc tài nguyên khác bảng kê hoặc chưa đọc được; chưa xác minh tương thích.'
    if version_parts(version) is None:
        return {'available': False, 'can_install': False, 'message': 'Phiên bản bản Việt hoá trong bảng kê không hợp lệ.'}
    if not receipt:
        return {'available': False, 'can_install': True, 'message': f'Bản Việt hoá: {version}. Chưa có biên bản cài để đối chiếu phiên bản. {version_note}', 'version_note': version_note}
    current = receipt.get('version')
    if version_parts(version) is None or version_parts(current) is None:
        return {'available': False, 'can_install': False, 'message': f'Không thể so sánh phiên bản đã cài ({current}) với bản trong bảng kê ({version}).'}
    if newer(version, current):
        return {'available': True, 'can_install': True, 'message': f'Có bản Việt hoá {version} mới hơn bản đã cài {current}. {version_note}', 'version': version, 'version_note': version_note}
    return {'available': False, 'can_install': False, 'message': f'Bản đã cài: {current} · Bảng kê: {version}. Không có bản mới hơn.'}
