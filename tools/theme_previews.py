"""Small palette-based Cinnamon chooser illustrations, not runtime screenshots.

Pure standard-library rasterization keeps builds deterministic and adds no
installer dependencies. Render at 2x and downsample for rounded edges.
"""
from pathlib import Path
import struct
import zlib

WIDTH, HEIGHT, SCALE = 247, 100, 2


class Canvas:
    def __init__(self):
        self.width = WIDTH * SCALE
        self.height = HEIGHT * SCALE
        self.pixels = bytearray(self.width * self.height * 4)

    def box(self, x, y, width, height, color, radius=0):
        x, y, width, height, radius = (v * SCALE for v in (x, y, width, height, radius))
        rgba = bytes.fromhex(color[1:]) + b'\xff'
        for row in range(max(0, int(y)), min(self.height, int(y + height))):
            for column in range(max(0, int(x)), min(self.width, int(x + width))):
                dx = max(x + radius - column - .5, column + .5 - (x + width - radius), 0)
                dy = max(y + radius - row - .5, row + .5 - (y + height - radius), 0)
                if dx * dx + dy * dy <= radius * radius:
                    offset = (row * self.width + column) * 4
                    self.pixels[offset:offset + 4] = rgba

    def png(self):
        raw = bytearray()
        for y in range(HEIGHT):
            raw.append(0)  # PNG filter: None.
            for x in range(WIDTH):
                offsets = [((y * SCALE + dy) * self.width + x * SCALE + dx) * 4
                           for dy in range(SCALE) for dx in range(SCALE)]
                alpha = sum(self.pixels[i + 3] for i in offsets)
                for channel in range(3):
                    raw.append(round(sum(self.pixels[i + channel] * self.pixels[i + 3]
                                         for i in offsets) / alpha) if alpha else 0)
                raw.append(round(alpha / (SCALE * SCALE)))

        def chunk(name, data):
            return struct.pack('!I', len(data)) + name + data + struct.pack('!I', zlib.crc32(name + data))

        return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', WIDTH, HEIGHT, 8, 6, 0, 0, 0))
                + chunk(b'tEXt', b'Description\0Palette-based theme chooser illustration; not a runtime screenshot.')
                + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))


def render(colors):
    """Return all three paths Cinnamon Settings probes before its fallback icon."""
    c = colors
    result = {}
    for kind in ('cinnamon', 'gtk-3.0', 'metacity-1'):
        image = Canvas()
        box = image.box
        box(0, 0, WIDTH, HEIGHT, c['background'], 7)
        if kind == 'cinnamon':
            box(8, 8, 145, 76, c['decorative_border'], 7)
            box(9, 9, 143, 74, c['popover'], 6)
            box(17, 17, 127, 15, c['accent_text'], 4)
            box(18, 18, 125, 13, c['background'], 3)
            box(24, 23, 47, 3, c['secondary_text'], 1)
            for row, length in ((40, 57), (55, 79), (70, 49)):
                if row == 55:
                    box(16, row - 5, 128, 14, c['accent_fill'], 3)
                box(22, row - 2, 7, 7, c['foreground'], 2)
                box(36, row, length, 3, c['foreground'], 1)
            box(163, 18, 75, 58, c['popover'], 6)
            for row in range(3):
                for column in range(5):
                    box(173 + column * 12, 29 + row * 14, 4, 4, c['secondary_text'], 1)
            box(194, 40, 12, 12, c['accent_fill'], 4)
            box(198, 44, 4, 4, c['foreground'], 1)
            box(0, 89, WIDTH, 11, c['surface'])
            for x in (12, 35, 58, 81):
                box(x, 92, 6, 5, c['foreground'], 1)
            box(78, 98, 12, 2, c['accent_text'])
            box(214, 93, 20, 3, c['foreground'], 1)
        else:
            box(18, 9, 217, 65, c['decorative_border'], 7)
            box(19, 10, 215, 63, c['background'], 6)
            box(8, 24, 217, 69, c['decorative_border'], 7)
            box(9, 25, 215, 67, c['background'], 6)
            box(9, 25, 215, 23, c['surface'], 6)
            box(9, 40, 215, 8, c['surface'])
            box(24, 35, 76, 3, c['foreground'], 1)
            box(163, 38, 7, 1, c['foreground'])
            box(181, 33, 7, 7, c['foreground'])
            box(182, 34, 5, 5, c['surface'])
            box(200, 30, 15, 15, c['hover'], 7)
            # Draw the close cross without font dependencies.
            for i in range(5):
                box(205 + i, 35 + i, 1, 1, c['foreground'])
                box(209 - i, 35 + i, 1, 1, c['foreground'])
            if kind == 'gtk-3.0':
                box(20, 57, 122, 22, c['accent_text'], 4)
                box(21, 58, 120, 20, c['background'], 3)
                box(29, 67, 56, 3, c['secondary_text'], 1)
                box(152, 57, 60, 22, c['accent_fill'], 4)
                box(167, 67, 29, 3, c['foreground'], 1)
            else:
                # A quiet client area keeps the decoration itself easy to see.
                box(24, 60, 165, 3, c['secondary_text'], 1)
                box(24, 71, 116, 3, c['decorative_border'], 1)
        result[Path(kind) / 'thumbnail.png'] = image.png()
    return result
