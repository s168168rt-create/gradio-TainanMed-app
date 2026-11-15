"""產生 PWA 圖示(一次性工具,已產生的 PNG 已放在 static/icons/)。"""
from PIL import Image, ImageDraw

def draw(size, maskable=False):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # 漸層背景
    grad = Image.new("RGB", (s, s))
    px = grad.load()
    for y in range(s):
        for x in range(s):
            t = (x + y) / (2 * s)
            px[x, y] = (int(37 + (6 - 37) * t), int(99 + (182 - 99) * t), int(235 + (212 - 235) * t))
    mask = Image.new("L", (s, s), 0)
    r = 0 if maskable else int(s * 0.22)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # maskable 需保留安全區(中央 80%)
    pad = s * (0.28 if maskable else 0.2)
    w = s - 2 * pad
    bar_w = w / 5.5
    heights = [0.45, 0.75, 0.6, 1.0]
    for i, h in enumerate(heights):
        x0 = pad + i * (bar_w * 1.5)
        y1 = s - pad
        y0 = y1 - w * h
        d.rounded_rectangle([x0, y0, x0 + bar_w, y1], radius=bar_w * 0.25, fill=(255, 255, 255, 235))
    return img

for name, size, mk in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                       ("maskable-512.png", 512, True), ("apple-touch-icon.png", 180, True)]:
    img = draw(size, mk)
    if name == "apple-touch-icon.png":  # iOS 不支援透明
        bg = Image.new("RGB", img.size, (37, 99, 235)); bg.paste(img, mask=img.split()[3]); img = bg
    img.save(f"static/icons/{name}")
print("done")
