import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SHEET = ROOT.parent / "shepherd" / "final" / "spritesheet-extended.webp"
OUT = ROOT / "ShepherdPetAlpha" / "assets"
RAW = OUT / "raw"

CELL_W = 192
CELL_H = 208
SCALE = 0.80
ROWS = {
    "idle": (0, 6),
    "running-right": (1, 8),
    "running-left": (2, 8),
    "jumping": (4, 5),
    "waiting": (5, 8),
}
RANDOM_IDLE_ROWS = {
    "idle-random-3": (3, 4),
    "idle-random-6": (6, 6),
    "idle-random-7": (7, 6),
    "idle-random-8": (8, 6),
}
MIRROR_FRAMES = {
    "waiting": {3, 4, 5, 6},
}


def clean_transparent_rgb(frame):
    frame = frame.convert("RGBA")
    pixels = frame.load()
    for y in range(frame.height):
        for x in range(frame.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                pixels[x, y] = (0, 0, 0, 0)
    return frame


def normalize_direction(state, index, frame):
    if index in MIRROR_FRAMES.get(state, set()):
        return frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return frame


def all_frames(sheet):
    frames = []
    for name, (row, count) in ROWS.items():
        for col in range(count):
            frame = sheet.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
            frame = clean_transparent_rgb(frame)
            frame = normalize_direction(name, col, frame)
            frames.append((name, col, frame))

    for name, (row, count) in RANDOM_IDLE_ROWS.items():
        for col in range(count):
            frame = sheet.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
            frames.append((name, col, clean_transparent_rgb(frame)))

    index = 0
    for row in (9, 10):
        for col in range(8):
            frame = sheet.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
            frames.append(("look", index, clean_transparent_rgb(frame)))
            index += 1
    return frames


def union_bbox(frames):
    left, top, right, bottom = CELL_W, CELL_H, 0, 0
    for _, _, frame in frames:
        bbox = frame.getchannel("A").getbbox()
        if not bbox:
            continue
        left = min(left, bbox[0])
        top = min(top, bbox[1])
        right = max(right, bbox[2])
        bottom = max(bottom, bbox[3])
    return left, top, right, bottom


def premultiplied_bgra(frame):
    frame = frame.convert("RGBA")
    out = bytearray()
    for r, g, b, a in frame.getdata():
        if a:
            out.extend((b * a // 255, g * a // 255, r * a // 255, a))
        else:
            out.extend((0, 0, 0, 0))
    return bytes(out)


def save_icon(frame, bbox):
    cropped = frame.crop(bbox)
    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    cropped.thumbnail((232, 232), Image.Resampling.LANCZOS)
    x = (256 - cropped.width) // 2
    y = (256 - cropped.height) // 2
    icon.alpha_composite(cropped, (x, y))
    icon.save(OUT / "app.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for path in RAW.glob("*.bgra"):
        path.unlink()

    sheet = Image.open(SHEET).convert("RGBA")
    frames = all_frames(sheet)
    bbox = union_bbox(frames)
    save_icon(frames[0][2], bbox)
    width = round((bbox[2] - bbox[0]) * SCALE)
    height = round((bbox[3] - bbox[1]) * SCALE)

    manifest = {"width": width, "height": height, "states": {}}
    for state, index, frame in frames:
        cropped = frame.crop(bbox)
        if SCALE == 1.0:
            scaled = cropped
        else:
            scaled = cropped.resize((width, height), Image.Resampling.LANCZOS)
        filename = f"{state}-{index:02d}.bgra"
        (RAW / filename).write_bytes(premultiplied_bgra(scaled))
        manifest["states"].setdefault(state, []).append(filename)

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"bbox": bbox, "width": width, "height": height, "states": {k: len(v) for k, v in manifest["states"].items()}}, indent=2))


if __name__ == "__main__":
    main()
