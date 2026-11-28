"""Pure Pillow renderer for the Friday tray icon."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from PIL import Image, ImageDraw, ImageFilter, ImageOps

log = logging.getLogger(__name__)

DEFAULT_SIZE = 64
MIN_SIZE = 16
MAX_SIZE = 512
SUPERSAMPLE = 4
DEFAULT_STATE = "idle"
_VIGNETTE_LUT = [int(((i / 255.0) ** 2.2) * 135) for i in range(256)]
_GLOW_LUT = [int(i * 0.42) for i in range(256)]
_ACCENT_STATES = frozenset({"idle", "loading"})

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class IconPalette:
    base: RGB
    highlight: RGB
    core: RGB
    deep: RGB
    rim_light: RGB
    rim_dark: RGB
    bar_tint: RGB


PALETTES: dict[str, IconPalette] = {
    "idle": IconPalette(
        base=(10, 16, 38),
        highlight=(76, 206, 255),
        core=(47, 94, 241),
        deep=(122, 76, 245),
        rim_light=(140, 226, 255),
        rim_dark=(118, 112, 255),
        bar_tint=(214, 236, 255),
    ),
    "loading": IconPalette(
        base=(10, 16, 38),
        highlight=(76, 206, 255),
        core=(47, 94, 241),
        deep=(122, 76, 245),
        rim_light=(140, 226, 255),
        rim_dark=(118, 112, 255),
        bar_tint=(214, 236, 255),
    ),
    "listening": IconPalette(
        base=(34, 10, 24),
        highlight=(255, 118, 166),
        core=(232, 54, 109),
        deep=(255, 114, 86),
        rim_light=(255, 168, 200),
        rim_dark=(240, 96, 130),
        bar_tint=(255, 224, 235),
    ),
    "thinking": IconPalette(
        base=(22, 12, 42),
        highlight=(192, 132, 252),
        core=(124, 58, 237),
        deep=(168, 85, 247),
        rim_light=(216, 178, 255),
        rim_dark=(148, 104, 255),
        bar_tint=(235, 222, 255),
    ),
    "speaking": IconPalette(
        base=(8, 30, 36),
        highlight=(94, 234, 212),
        core=(14, 165, 233),
        deep=(45, 212, 191),
        rim_light=(165, 245, 235),
        rim_dark=(56, 189, 248),
        bar_tint=(220, 250, 248),
    ),
    "error": IconPalette(
        base=(38, 10, 14),
        highlight=(255, 128, 128),
        core=(220, 38, 38),
        deep=(249, 115, 22),
        rim_light=(255, 175, 175),
        rim_dark=(239, 68, 68),
        bar_tint=(255, 226, 226),
    ),
}


def normalize_state(state: str | None) -> str:
    """Normalizes a state string and falls back to 'idle' for unknown values."""
    if not isinstance(state, str):
        return DEFAULT_STATE
    cleaned = state.strip().lower()
    if cleaned in PALETTES:
        return cleaned
    log.warning("unknown tray icon state %r, falling back to %s", state, DEFAULT_STATE)
    return DEFAULT_STATE


def _parse_hex_rgb(value: str | None) -> RGB | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if len(cleaned) != 7 or not cleaned.startswith("#"):
        return None
    try:
        return (
            int(cleaned[1:3], 16),
            int(cleaned[3:5], 16),
            int(cleaned[5:7], 16),
        )
    except ValueError:
        return None


def _mix(a: int, b: int, t: float) -> int:
    return max(0, min(255, round(a + (b - a) * t)))


def _accent_palette(rgb: RGB) -> IconPalette:
    r, g, b = rgb
    core = (_mix(r, 12, 0.25), _mix(g, 16, 0.25), _mix(b, 38, 0.25))
    return IconPalette(
        base=(max(8, r // 9), max(10, g // 9), max(16, b // 7)),
        highlight=(_mix(r, 255, 0.35), _mix(g, 255, 0.35), _mix(b, 255, 0.35)),
        core=core,
        deep=(_mix(r, 28, 0.45), _mix(g, 22, 0.50), _mix(b, 85, 0.35)),
        rim_light=(_mix(r, 255, 0.50), _mix(g, 255, 0.50), _mix(b, 255, 0.50)),
        rim_dark=core,
        bar_tint=(_mix(215, r, 0.18), _mix(228, g, 0.18), _mix(242, b, 0.18)),
    )


def palette_for(state: str | None = None, accent: str | None = None) -> IconPalette:
    """Returns the icon colour palette for the given state and optional hex accent."""
    name = normalize_state(state)
    if accent is not None and name in _ACCENT_STATES:
        rgb = _parse_hex_rgb(accent)
        if rgb is not None:
            return _accent_palette(rgb)
    return PALETTES[name]


def _diagonal_gradient(canvas: int) -> Image.Image:
    big = canvas * 2
    grad = Image.linear_gradient("L").resize((big, big), Image.Resampling.BILINEAR)
    rotated = grad.rotate(45, resample=Image.Resampling.BILINEAR)
    offset = canvas // 2
    return rotated.crop((offset, offset, offset + canvas, offset + canvas))


def _tinted_layer(canvas: int, rgb: RGB, mask: Image.Image) -> Image.Image:
    layer = Image.new("RGBA", (canvas, canvas), (*rgb, 255))
    layer.putalpha(mask)
    return layer


def _draw_voice_bars_mask(canvas: int, s: float) -> Image.Image:
    mask = Image.new("L", (canvas, canvas), 0)
    draw = ImageDraw.Draw(mask)
    cx = canvas / 2.0
    cy = canvas / 2.0
    bar_w = 6.0 * s
    gap = 5.0 * s
    step = bar_w + gap
    radius = round(bar_w / 2.0)

    bars = (
        (cx - step, 16.0 * s),
        (cx, 30.0 * s),
        (cx + step, 16.0 * s),
    )
    for bx, bh in bars:
        box = (
            round(bx - bar_w / 2.0),
            round(cy - bh / 2.0),
            round(bx + bar_w / 2.0),
            round(cy + bh / 2.0),
        )
        draw.rounded_rectangle(box, radius=radius, fill=255)
    return mask


def make_tray_icon(
    size: int = DEFAULT_SIZE,
    *,
    state: str = DEFAULT_STATE,
    accent: str | None = None,
) -> Image.Image:
    """Renders an anti-aliased RGBA tray icon of the requested size."""
    if (
        isinstance(size, bool)
        or not isinstance(size, int)
        or not (MIN_SIZE <= size <= MAX_SIZE)
    ):
        raise ValueError(f"size must be an int in {MIN_SIZE}..{MAX_SIZE}, got {size!r}")

    palette = palette_for(state, accent=accent)
    canvas = size * SUPERSAMPLE
    s = canvas / 64.0
    margin = 3.0 * s
    circle_box = (
        round(margin),
        round(margin),
        round(canvas - margin),
        round(canvas - margin),
    )

    orb = Image.new("RGBA", (canvas, canvas), (*palette.base, 255))
    diag = _diagonal_gradient(canvas)

    aura = ImageOps.colorize(
        diag, palette.highlight, palette.deep, mid=palette.core
    ).convert("RGBA")
    aura.putalpha(180)
    orb = Image.alpha_composite(orb, aura)

    radial = Image.radial_gradient("L").resize(
        (canvas, canvas), Image.Resampling.BILINEAR
    )
    vignette_mask = radial.point(_VIGNETTE_LUT)
    orb = Image.alpha_composite(orb, _tinted_layer(canvas, palette.base, vignette_mask))

    sheen_mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(sheen_mask).ellipse(
        (round(13 * s), round(5.5 * s), round(51 * s), round(23 * s)), fill=54
    )
    sheen_mask = sheen_mask.filter(ImageFilter.GaussianBlur(radius=2.6 * s))
    orb = Image.alpha_composite(orb, _tinted_layer(canvas, (255, 255, 255), sheen_mask))

    rim_mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(rim_mask).ellipse(
        circle_box, outline=215, width=max(2, round(3.4 * s))
    )
    rim = ImageOps.colorize(diag, palette.rim_light, palette.rim_dark).convert("RGBA")
    rim.putalpha(rim_mask)
    orb = Image.alpha_composite(orb, rim)

    arc_layer = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    inset = round((3.0 + 0.9) * s)
    arc_box = (inset, inset, canvas - inset, canvas - inset)
    ImageDraw.Draw(arc_layer).arc(
        arc_box,
        start=195,
        end=330,
        fill=(240, 250, 255, 195),
        width=max(1, round(1.5 * s)),
    )
    orb = Image.alpha_composite(orb, arc_layer)

    bars_mask = _draw_voice_bars_mask(canvas, s)
    glow_mask = bars_mask.filter(ImageFilter.GaussianBlur(radius=4.5 * s)).point(
        _GLOW_LUT
    )
    orb = Image.alpha_composite(
        orb, _tinted_layer(canvas, palette.highlight, glow_mask)
    )

    vert_grad = Image.linear_gradient("L").resize(
        (canvas, canvas), Image.Resampling.BILINEAR
    )
    bars = ImageOps.colorize(vert_grad, (255, 255, 255), palette.bar_tint).convert(
        "RGBA"
    )
    bars.putalpha(bars_mask)
    orb = Image.alpha_composite(orb, bars)

    orb_mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(orb_mask).ellipse(circle_box, fill=255)
    orb.putalpha(orb_mask)

    return orb.resize((size, size), Image.Resampling.LANCZOS)
