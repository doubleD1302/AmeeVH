#!/usr/bin/env python3
"""Read/export Unity EN texture assets and create verified OFFLINE staging bundles.

Requires the project's isolated UnityPy/Pillow environment. Never installs patches.
Streamed Texture2D replacement preserves every serialized object byte-for-byte.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile

PROJECT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def output_path(relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or p.drive or not p.parts or ".." in p.parts or ":" in str(p):
        raise ValueError("Output must be a project-relative path without traversal/ADS")
    if p.parts[0] not in {"work", "reports", "staging"}:
        raise ValueError("Output is restricted to project work/, reports/, staging/")
    current = PROJECT
    for part in p.parts:
        current = current / part
        if current.exists() and is_link(current):
            raise ValueError("Linked output paths are refused")
    target = (PROJECT / p).resolve()
    if not target.is_relative_to(PROJECT):
        raise ValueError("Output escaped project root")
    if target.exists():
        raise ValueError("Output exists; choose a new revision")
    return target


def check_hash(data: bytes, expected: str, label: str):
    if not re.fullmatch(r"[0-9a-f]{64}", expected or "") or sha(data) != expected:
        raise ValueError(f"{label} SHA256 mismatch")


def dependencies():
    import UnityPy
    from PIL import Image
    from UnityPy.export import Texture2DConverter
    from UnityPy.streams import EndianBinaryReader
    return UnityPy, Image, Texture2DConverter, EndianBinaryReader


def load_source(path: Path, expected: str):
    if not path.name.endswith(".en.unity3d"):
        raise ValueError("Explicit *.en.unity3d source required")
    if is_link(path):
        raise ValueError("Linked source refused")
    raw = path.read_bytes()
    check_hash(raw, expected, "Source")
    if not raw.startswith(b"UnityFS\0"):
        raise ValueError("Only UnityFS bundles supported")
    UnityPy, *_ = dependencies()
    env = UnityPy.load(raw)
    if not getattr(env.file, "files", None):
        raise ValueError("Expected one UnityFS bundle")
    return raw, env


def node_bytes(node):
    if hasattr(node, "reader"):
        return bytes(node.reader.bytes)
    if hasattr(node, "bytes"):
        return bytes(node.bytes)
    raise ValueError(f"Unsupported bundle node {type(node).__name__}")


def snapshots(env):
    nodes = {name: {"sha256": sha(node_bytes(value)), "bytes": len(node_bytes(value)),
                    "flags": int(value.flags)} for name, value in env.file.files.items()}
    objects = {}
    for obj in env.objects:
        key = (obj.assets_file.name, int(obj.path_id))
        if key in objects:
            raise ValueError("Duplicate CAB/path_id identity")
        objects[key] = {"type": obj.type.name, "sha256": sha(obj.get_raw_data())}
    return nodes, objects


def select_object(env, asset: str, path_id: int, kind="Texture2D"):
    matches = [o for o in env.objects if o.assets_file.name == asset and int(o.path_id) == path_id]
    if len(matches) != 1 or matches[0].type.name != kind:
        raise ValueError(f"Expected exactly one {kind} at CAB/path_id")
    return matches[0]


def texture_meta(obj):
    tex = obj.read()
    stream = tex.m_StreamData
    return {"asset": obj.assets_file.name, "path_id": int(obj.path_id), "name": tex.m_Name,
            "width": tex.m_Width, "height": tex.m_Height, "format": int(tex.m_TextureFormat),
            "mip_count": tex.m_MipCount, "image_count": tex.m_ImageCount,
            "texture_dimension": tex.m_TextureDimension, "color_space": tex.m_ColorSpace,
            "stream": {"path": stream.path, "offset": stream.offset, "size": stream.size} if stream else None,
            "inline_bytes": len(tex.image_data), "object_sha256": sha(obj.get_raw_data())}


def texture_consumers(env, asset, path_id):
    """Local Sprite users only; external bundle references still need runtime QA."""
    consumers = []
    for obj in env.objects:
        if obj.type.name != "Sprite" or obj.assets_file.name != asset:
            continue
        sprite = obj.read()
        rd = sprite.m_RD
        ptr = rd.texture
        matches = ptr.m_FileID == 0 and ptr.m_PathID == path_id
        in_atlas = False
        if not matches and sprite.m_SpriteAtlas.m_PathID:
            try:
                atlas = sprite.m_SpriteAtlas.read()
                for key, entry in atlas.m_RenderDataMap:
                    if key == sprite.m_RenderDataKey and entry.texture.m_FileID == 0 and entry.texture.m_PathID == path_id:
                        matches, in_atlas = True, True
                        break
            except (ValueError, KeyError, AttributeError):
                raise ValueError("Unresolved local SpriteAtlas reference; mesh safety cannot be established")
        if matches:
            vertices = getattr(getattr(rd, "m_VertexData", None), "m_VertexCount", None)
            if vertices is None:
                vertices = len(getattr(rd, "vertices", []) or [])
            rect = rd.textureRect
            consumers.append({"sprite_path_id": int(obj.path_id), "name": sprite.m_Name,
                              "vertex_count": int(vertices), "atlas": in_atlas,
                              "texture_rect": [rect.x, rect.y, rect.width, rect.height]})
    return consumers


def check_mesh_safety(consumers, width, height, rect=None):
    for user in consumers:
        if user["vertex_count"] != 4:
            raise ValueError("Tight/nonrectangular sprite mesh would clip replacement glyphs; mesh repair requires separate QA")
        if user["atlas"]:
            if rect is None:
                raise ValueError("Whole-atlas replacement refused; use explicit supported rect or a dedicated atlas pipeline")
        elif any(abs(a - b) > 0.01 for a, b in zip(user["texture_rect"], [0, 0, width, height])):
            raise ValueError("Sprite samples a cropped texture region; replacement geometry needs dedicated review")


def inventory(env):
    textures, sprites = [], []
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            metadata = texture_meta(obj)
            metadata["local_sprite_consumers"] = texture_consumers(env, obj.assets_file.name, obj.path_id)
            textures.append(metadata)
        elif obj.type.name == "Sprite":
            data = obj.read()
            rect = data.m_Rect
            sprites.append({"asset": obj.assets_file.name, "path_id": int(obj.path_id), "name": data.m_Name,
                            "rect": {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}})
    return {"textures": textures, "sprites": sprites}


def resolve_resource(bundle, stream):
    if stream is None or not stream.path or stream.size <= 0:
        raise ValueError("Inline/non-streamed textures are unsupported; no metadata relocation is attempted")
    name = stream.path.replace("\\", "/").rsplit("/", 1)[-1]
    matches = [key for key in bundle.files if key == name]
    if len(matches) != 1:
        raise ValueError("Texture resource is external or ambiguous; standalone bundle patch refused")
    raw = node_bytes(bundle.files[matches[0]])
    start, length = int(stream.offset), int(stream.size)
    if start < 0 or length <= 0 or start + length > len(raw):
        raise ValueError("Texture stream segment is out of bounds")
    return matches[0], raw, start, length


def replace_segment(resource: bytes, start: int, length: int, encoded: bytes):
    if start < 0 or length <= 0 or start + length > len(resource):
        raise ValueError("Invalid resource segment")
    if len(encoded) != length:
        raise ValueError("Encoded size differs; offset/resource relocation refused")
    return resource[:start] + encoded + resource[start + length:]


def check_segment_aliases(env, target, resource_name, start, length):
    for obj in env.objects:
        if obj.type.name != "Texture2D" or (obj.assets_file.name, obj.path_id) == (target.assets_file.name, target.path_id):
            continue
        stream = obj.read().m_StreamData
        if not stream or not stream.path or stream.path.replace("\\", "/").rsplit("/", 1)[-1] != resource_name:
            continue
        a, b = int(stream.offset), int(stream.offset) + int(stream.size)
        if max(a, start) < min(b, start + length):
            raise ValueError("Target stream aliases/overlaps another Texture2D; non-target image could change")


def check_alpha(source, replacement):
    original_alpha = source.convert("RGBA").getchannel("A").getextrema()
    target_alpha = replacement.convert("RGBA").getchannel("A").getextrema()
    # BC7 decoders can yield 254 for an intended fully opaque source; tolerate one level.
    if original_alpha[0] < 254 and target_alpha == (255, 255):
        raise ValueError("Source uses transparency but replacement is fully opaque; alpha loss refused")


def validate_rect(rect, width, height):
    if len(rect) != 4:
        raise ValueError("Rect must be x,y,width,height in decoded top-left pixel coordinates")
    x, y, w, h = rect
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
        raise ValueError("Rect out of texture bounds")
    return x, y, w, h


def compose_input(source_image, replacement, texture_format, mip_count, rect=None):
    source_image = source_image.convert("RGBA")
    replacement = replacement.convert("RGBA")
    if rect is None:
        if replacement.size != source_image.size:
            raise ValueError("Replacement dimensions must match exactly; automatic resize refused")
        return replacement
    x, y, w, h = validate_rect(rect, *source_image.size)
    if texture_format != 4 or mip_count != 1:
        raise ValueError("Rect replacement only supports RGBA32 with one mip; lossy atlas recompression refused")
    if replacement.size != (w, h):
        raise ValueError("Replacement image dimensions must match rect")
    result = source_image.copy()
    # No alpha blending: replacement RGBA includes the intended transparent pixels.
    result.paste(replacement, (x, y))
    return result


def encode_mips(tex, image):
    _, Image, converter, _ = dependencies()
    count = int(tex.m_MipCount or 1)
    if count < 1 or count > 32 or tex.m_ImageCount != 1 or tex.m_TextureDimension != 2:
        raise ValueError("Only ordinary single-image Texture2D with valid mip count supported")
    if getattr(tex, "m_MipsStripped", 0):
        raise ValueError("Stripped mip layouts are unsupported")
    platform = tex.object_reader.platform
    encoded = []
    current = image
    for level in range(count):
        data, actual = converter.image_to_texture2d(current, tex.m_TextureFormat, platform, tex.m_PlatformBlob)
        if int(actual) != int(tex.m_TextureFormat):
            raise ValueError(f"Encoder changed texture format {tex.m_TextureFormat} -> {actual}")
        encoded.append(bytes(data))
        if level + 1 < count:
            if current.size == (1, 1):
                raise ValueError("Mip count exceeds complete mip chain")
            current = current.resize((max(1, current.width // 2), max(1, current.height // 2)), Image.Resampling.BICUBIC)
    return b"".join(encoded)


def serialize_preserving_nodes(env, replacement=None):
    # Do not call SerializedFile.save(): it can rewrite metadata/padding even on no-op.
    *_, Reader = dependencies()
    for key, node in list(env.file.files.items()):
        raw = replacement[1] if replacement is not None and key == replacement[0] else node_bytes(node)
        reader = Reader(raw)
        reader.flags = node.flags
        env.file.files[key] = reader
    return env.file.save(packer="original")


def reopen_and_verify(original_env, candidate_raw, target_resource=None, target_segment=None):
    UnityPy, *_ = dependencies()
    original_nodes, original_objects = snapshots(original_env)
    candidate_env = UnityPy.load(candidate_raw)
    new_nodes, new_objects = snapshots(candidate_env)
    if original_objects != new_objects:
        raise ValueError("Serialized object bytes/type/identity drifted")
    if original_nodes.keys() != new_nodes.keys():
        raise ValueError("Bundle node set changed")
    for key in original_nodes:
        if original_nodes[key]["flags"] != new_nodes[key]["flags"]:
            raise ValueError("Bundle node flags changed")
        a, b = node_bytes(original_env.file.files[key]), node_bytes(candidate_env.file.files[key])
        if key != target_resource:
            if a != b:
                raise ValueError("Non-target bundle node changed")
        else:
            start, length, encoded = target_segment
            if len(a) != len(b) or a[:start] != b[:start] or a[start + length:] != b[start + length:]:
                raise ValueError("Resource bytes outside target segment changed")
            if b[start:start + length] != encoded:
                raise ValueError("Target encoded segment readback mismatch")
    return candidate_env, {"serialized_objects_checked": len(original_objects), "all_object_bytes_unchanged": True,
                           "bundle_nodes_checked": len(original_nodes), "non_target_nodes_unchanged": True,
                           "resource_outside_segment_unchanged": True}


def image_stats(image):
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    return {"size": list(image.size), "rgba_sha256": sha(image.tobytes()), "alpha_extrema": list(alpha.getextrema()),
            "alpha_bbox": list(alpha.getbbox()) if alpha.getbbox() else None}


def pixel_error(actual, intended):
    from PIL import ImageChops, ImageStat
    difference = ImageChops.difference(actual.convert("RGBA"), intended.convert("RGBA"))
    stat = ImageStat.Stat(difference)
    return {"channel_order": "RGBA", "mae_per_channel": stat.mean, "rmse_per_channel": stat.rms,
            "max_absolute_per_channel": [upper for lower, upper in difference.getextrema()],
            "quality_accepted": None, "note": "Metrics only; visual/localization reviewer must judge text and artwork"}


def prepare_patch(source_path, expected_source, asset, path_id, image_path, expected_image, rect=None):
    raw, env = load_source(source_path, expected_source)
    obj = select_object(env, asset, path_id)
    tex, before_meta = obj.read(), texture_meta(obj)
    consumers = texture_consumers(env, asset, path_id)
    check_mesh_safety(consumers, tex.m_Width, tex.m_Height, rect)
    resource_name, resource, start, length = resolve_resource(env.file, tex.m_StreamData)
    check_segment_aliases(env, obj, resource_name, start, length)
    replacement_raw = image_path.read_bytes()
    check_hash(replacement_raw, expected_image, "Replacement image")
    _, Image, converter, _ = dependencies()
    with Image.open(io.BytesIO(replacement_raw)) as img:
        if img.format != "PNG" or getattr(img, "n_frames", 1) != 1:
            raise ValueError("A static PNG replacement is required")
        img.load()
        replacement_mode = img.mode
        replacement = img.convert("RGBA")
    intended = compose_input(tex.image, replacement, int(tex.m_TextureFormat), int(tex.m_MipCount or 1), rect)
    check_alpha(tex.image, intended)
    encoded = encode_mips(tex, intended)
    changed_resource = replace_segment(resource, start, length, encoded)
    # Keep original env pristine for independent reopen/non-target comparison.
    UnityPy, *_ = dependencies()
    mutable = UnityPy.load(raw)
    candidate_raw = serialize_preserving_nodes(mutable, (resource_name, changed_resource))
    readback, verification = reopen_and_verify(env, candidate_raw, resource_name, (start, length, encoded))
    actual_obj = select_object(readback, asset, path_id)
    if texture_meta(actual_obj) != before_meta:
        raise ValueError("Texture metadata changed")
    actual = actual_obj.read().image.convert("RGBA")
    expected_decode = converter.parse_image_data(encoded, tex.m_Width, tex.m_Height, tex.m_TextureFormat,
                                                obj.assets_file.version, obj.platform, tex.m_PlatformBlob).convert("RGBA")
    if actual.tobytes() != expected_decode.tobytes():
        raise ValueError("Decoded texture differs from independently decoded encoded segment")
    if int(tex.m_TextureFormat) == 4 and actual.tobytes() != intended.tobytes():
        raise ValueError("RGBA32 pixel readback mismatch")
    if file_sha(source_path) != expected_source:
        raise ValueError("Source changed while building")
    report = {"kind": "texture_staging_only", "source_path": str(source_path.resolve()),
              "source_sha256": expected_source, "candidate_sha256": sha(candidate_raw),
              "replacement_path": str(image_path.resolve()), "replacement_sha256": expected_image,
              "replacement_png_mode": replacement_mode, "original_pixels": image_stats(tex.image),
              "texture": before_meta, "rect_top_left": list(rect) if rect else None,
              "local_sprite_consumers": consumers,
              "resource": resource_name, "segment_offset": start, "segment_size": length,
              "encoded_segment_sha256": sha(encoded), "verification": verification,
              "intended_pixels": image_stats(intended), "decoded_pixels": image_stats(actual),
              "decoded_exact_input": actual.tobytes() == intended.tobytes(),
              "compression_error": pixel_error(actual, intended),
              "compression_note": "Lossy formats can quantize replacement pixels; encoded/native metadata readback verified",
              "installed": False, "runtime": "not_tested", "semantic_review": "external_review_required"}
    return candidate_raw, actual, report


def write_package(target, payloads):
    if target.exists():
        raise ValueError("Output exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".texture-", dir=target.parent)).resolve()
    if temp.parent != target.parent.resolve():
        raise ValueError("Temporary output escaped parent")
    try:
        for name, data in payloads.items():
            if Path(name).name != name:
                raise ValueError("Payload names must be basenames")
            dest = temp / name
            if isinstance(data, bytes):
                dest.write_bytes(data)
            elif isinstance(data, dict):
                dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            else:
                data.save(dest, format="PNG")
        temp.rename(target)
    finally:
        if temp.exists() and temp.parent == target.parent.resolve() and temp.name.startswith(".texture-"):
            shutil.rmtree(temp)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ["probe", "export", "noop", "patch"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--source", required=True, type=Path)
        cmd.add_argument("--source-sha256", required=True)
        cmd.add_argument("--out", required=True, help="New project-relative output directory")
        if name in {"export", "patch"}:
            cmd.add_argument("--asset", required=True, help="Exact serialized CAB node name")
            cmd.add_argument("--path-id", required=True, type=int)
        if name == "export":
            cmd.add_argument("--sprite", action="store_true", help="Export Sprite via UnityPy instead of full Texture2D")
        if name == "patch":
            cmd.add_argument("--image", required=True, type=Path)
            cmd.add_argument("--image-sha256", required=True)
            cmd.add_argument("--rect", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    args = p.parse_args(argv)
    out = output_path(args.out)
    raw, env = load_source(args.source, args.source_sha256)
    base = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_path": str(args.source.resolve()), "source_sha256": sha(raw),
            "installed": False, "runtime": "not_tested"}
    if args.command == "probe":
        report = {**base, "kind": "texture_inventory", **inventory(env)}
        write_package(out, {"manifest.json": report})
    elif args.command == "export":
        obj = select_object(env, args.asset, args.path_id, "Sprite" if args.sprite else "Texture2D")
        image = obj.read().image.convert("RGBA")
        report = {**base, "kind": "sprite_export" if args.sprite else "texture_export",
                  "asset": args.asset, "path_id": args.path_id, "name": obj.read().m_Name,
                  "object_sha256": sha(obj.get_raw_data()), "pixels": image_stats(image)}
        if not args.sprite:
            report["texture"] = texture_meta(obj)
        write_package(out, {"image.png": image, "manifest.json": report})
    elif args.command == "noop":
        UnityPy, *_ = dependencies()
        candidate = serialize_preserving_nodes(UnityPy.load(raw))
        _, checked = reopen_and_verify(env, candidate)
        report = {**base, "kind": "noop_bundle_repack", "candidate_sha256": sha(candidate),
                  "container_byte_identical": candidate == raw, "verification": checked,
                  "note": "Compression/container bytes may differ; every decompressed node and raw serialized object is identical"}
        write_package(out, {args.source.name: candidate, "manifest.json": report})
    else:
        candidate, decoded, report = prepare_patch(args.source, args.source_sha256, args.asset, args.path_id,
                                                  args.image, args.image_sha256, args.rect)
        write_package(out, {args.source.name: candidate, "decoded.png": decoded, "manifest.json": {**base, **report}})
    print(json.dumps({"command": args.command, "output": str(out), "source_unchanged": file_sha(args.source) == args.source_sha256}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, TypeError) as exc:
        import sys
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
