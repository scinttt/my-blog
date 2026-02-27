#!/usr/bin/env python3
"""Generate favicon PNG files using pure Python stdlib.

Design: purple-to-blue gradient background with white </>  pixel art.
"""

import struct
import zlib
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static')

# --- Color palette ---
COLOR_BG_TOP = (124, 58, 237)      # #7c3aed purple
COLOR_BG_BOTTOM = (37, 99, 235)    # #2563eb blue
COLOR_TEXT = (255, 255, 255)        # white
COLOR_SHADOW = (0, 0, 0, 60)        # subtle shadow (unused in RGB mode)


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def create_png_bytes(width, height, pixels_rgb):
    """Encode a list-of-rows-of-(r,g,b) tuples into a PNG byte string."""
    def make_chunk(chunk_type, data):
        content = chunk_type + data
        crc = zlib.crc32(content) & 0xffffffff
        return struct.pack('>I', len(data)) + content + struct.pack('>I', crc)

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = make_chunk(b'IHDR', ihdr_data)

    raw_rows = b''
    for row in pixels_rgb:
        raw_rows += b'\x00'  # Filter type: None
        for r, g, b in row:
            raw_rows += bytes([r, g, b])

    compressed = zlib.compress(raw_rows, 9)
    idat_chunk = make_chunk(b'IDAT', compressed)
    iend_chunk = make_chunk(b'IEND', b'')

    return signature + ihdr_chunk + idat_chunk + iend_chunk


def draw_rounded_rect_gradient(pixels, width, height, radius):
    """Fill pixels with a diagonal gradient and rounded corners."""
    for y in range(height):
        for x in range(width):
            t = (x + y) / (width + height - 2)
            bg = lerp_color(COLOR_BG_TOP, COLOR_BG_BOTTOM, t)

            # Rounded corner masking
            in_corner = False
            corners = [
                (radius, radius),
                (width - 1 - radius, radius),
                (radius, height - 1 - radius),
                (width - 1 - radius, height - 1 - radius),
            ]
            near_corner = False
            for cx, cy in corners:
                if abs(x - cx) <= radius and abs(y - cy) <= radius:
                    near_corner = True
                    dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    if dist > radius:
                        in_corner = True
                    break

            if in_corner:
                pixels[y][x] = (0, 0, 0)  # transparent placeholder (will stay black)
            else:
                pixels[y][x] = bg


# Pixel font: each glyph is a list of rows, each row is a list of 0/1
# Grid: 5 columns x 7 rows
GLYPH_SCALE = None  # computed per size

GLYPHS_5x7 = {
    '<': [
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
    ],
    '/': [
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    '>': [
        [0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
    ],
}

GLYPH_ROWS = 7
GLYPH_COLS = 5


def render_text(pixels, width, height, scale, gap_scale):
    """Draw </> onto pixels using the pixel font."""
    text = ['<', '/', '>']
    char_width = GLYPH_COLS * scale
    char_height = GLYPH_ROWS * scale
    gap = max(1, gap_scale)

    total_width = len(text) * char_width + (len(text) - 1) * gap
    start_x = (width - total_width) // 2
    start_y = (height - char_height) // 2

    for char_index, char in enumerate(text):
        glyph = GLYPHS_5x7[char]
        char_start_x = start_x + char_index * (char_width + gap)

        for row_index, row in enumerate(glyph):
            for col_index, pixel_on in enumerate(row):
                if pixel_on:
                    px = char_start_x + col_index * scale
                    py = start_y + row_index * scale
                    for dy in range(scale):
                        for dx in range(scale):
                            tx, ty = px + dx, py + dy
                            if 0 <= tx < width and 0 <= ty < height:
                                pixels[ty][tx] = COLOR_TEXT


def generate_favicon(size, filename, font_scale, gap_scale, corner_radius_ratio=0.18):
    """Generate a single favicon PNG at the given size."""
    radius = max(1, int(size * corner_radius_ratio))
    pixels = [[(0, 0, 0)] * size for _ in range(size)]

    draw_rounded_rect_gradient(pixels, size, size, radius)
    render_text(pixels, size, size, font_scale, gap_scale)

    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, 'wb') as f:
        f.write(create_png_bytes(size, size, pixels))
    print(f'Generated: {output_path}')


def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # favicon-16x16.png: scale=1, gap=1
    generate_favicon(16, 'favicon-16x16.png', font_scale=1, gap_scale=1)

    # favicon-32x32.png: scale=2, gap=2
    generate_favicon(32, 'favicon-32x32.png', font_scale=2, gap_scale=2)

    # apple-touch-icon.png (180x180): scale=10, gap=8
    generate_favicon(180, 'apple-touch-icon.png', font_scale=10, gap_scale=8)

    print('Done.')


if __name__ == '__main__':
    generate_all()
