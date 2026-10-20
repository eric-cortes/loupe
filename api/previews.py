"""Serves Lightroom Classic's own JPEG previews (the `<Catalog> Previews.lrdata`
folder next to the .lrcat) so RAF photos can be shown in the browser. Both
layouts are handled: per-size extensionless JPEG files named
`<uuid>-<digest>_<longEdge>` (Lightroom Classic 13.x) and older `.lrprev`
pyramids. The previews.db / preview file layouts are community
reverse-engineered, not official Adobe documentation, and may change between
Lightroom versions.
"""
from __future__ import annotations

import io
import os
import sqlite3
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
THUMB_MIN_LONG_EDGE = 800
SECTION_MARKER = b"AgHg"
JPEG_START = b"\xff\xd8\xff"
JPEG_END = b"\xff\xd9"

ORIENTATION_TRANSPOSE = {
    "BC": Image.Transpose.ROTATE_270,
    "CD": Image.Transpose.ROTATE_180,
    "DA": Image.Transpose.ROTATE_90,
}


def _find_previews_dir() -> Path | None:
    env = os.environ.get("LR_PREVIEWS_DIR")
    if env:
        return Path(env)
    matches = sorted(REPO_ROOT.glob("catalog/*Previews.lrdata"))
    return matches[0] if matches else None


PREVIEWS_DIR = _find_previews_dir()


def _lookup(lrcat_id: int) -> tuple[str, str, str | None] | None:
    db_path = PREVIEWS_DIR / "previews.db"
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
    try:
        return conn.execute(
            "SELECT uuid, digest, orientation FROM ImageCacheEntry WHERE imageId = ?",
            (lrcat_id,),
        ).fetchone()
    finally:
        conn.close()


def _extract_jpegs(data: bytes) -> list[tuple[bytes, tuple[int, int]]]:
    found = []
    for chunk in data.split(SECTION_MARKER):
        start = chunk.find(JPEG_START)
        end = chunk.rfind(JPEG_END)
        if start == -1 or end == -1 or end < start:
            continue
        jpeg = chunk[start : end + 2]
        try:
            with Image.open(io.BytesIO(jpeg)) as img:
                size = img.size
        except Exception:
            continue
        found.append((jpeg, size))
    return found


def get_preview_jpeg(lrcat_id: int, size: str) -> bytes | None:
    if PREVIEWS_DIR is None:
        return None
    try:
        row = _lookup(lrcat_id)
    except sqlite3.Error:
        return None
    if row is None:
        return None
    uuid, digest, orientation = row
    folder = PREVIEWS_DIR / uuid[0] / uuid[:4]
    prefix = f"{uuid}-{digest}_"
    sized = []
    if folder.is_dir():
        for entry in folder.iterdir():
            suffix = entry.name[len(prefix) :]
            if entry.name.startswith(prefix) and suffix.isdigit() and entry.is_file():
                sized.append((int(suffix), entry))
    if sized:
        sized.sort(key=lambda s: s[0])
        if size == "thumb":
            big_enough = [s for s in sized if s[0] >= THUMB_MIN_LONG_EDGE]
            chosen = big_enough[0] if big_enough else sized[-1]
        else:
            chosen = sized[-1]
        jpeg = chosen[1].read_bytes()
        try:
            with Image.open(io.BytesIO(jpeg)) as img:
                exif_orientation = img.getexif().get(274)
        except Exception:
            exif_orientation = None
        if exif_orientation not in (None, 1):
            return jpeg
    else:
        path = folder / f"{uuid}-{digest}.lrprev"
        if not path.is_file():
            return None
        candidates = _extract_jpegs(path.read_bytes())
        if not candidates:
            return None
        candidates.sort(key=lambda c: max(c[1]))
        if size == "thumb":
            big_enough = [c for c in candidates if max(c[1]) >= THUMB_MIN_LONG_EDGE]
            jpeg = (big_enough[0] if big_enough else candidates[-1])[0]
        else:
            jpeg = candidates[-1][0]
    transpose = ORIENTATION_TRANSPOSE.get(orientation)
    if transpose is None:
        return jpeg
    with Image.open(io.BytesIO(jpeg)) as img:
        out = io.BytesIO()
        img.transpose(transpose).convert("RGB").save(out, format="JPEG", quality=90)
    return out.getvalue()
