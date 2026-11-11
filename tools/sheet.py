"""Contact sheet of sprites (8x, nearest neighbour) for visual review. Usage: sheet.py OUT [id-prefix ...]"""
import sys
from PIL import Image, ImageDraw
import sprites

out = sys.argv[1]
prefixes = sys.argv[2:]
S = sprites.build_all()
ids = [k for k in S if not prefixes or any(k.startswith(p) for p in prefixes)]
cols = 8; cell = 32 * 5 + 8
rows = (len(ids) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 14)), (44, 46, 52))
d = ImageDraw.Draw(sheet)
for i, k in enumerate(ids):
    im = S[k].image()
    x, y = (i % cols) * cell, (i // cols) * (cell + 14)
    big = im.resize((160, 160), Image.Resampling.NEAREST)
    sheet.paste(big, (x + 4, y + 4), big)
    d.text((x + 4, y + cell - 2), k[:26], fill=(230, 226, 214))
sheet.save(out)
print(len(ids), 'sprites ->', out)
