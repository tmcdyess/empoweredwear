"""
Remove the black background from the EmpoweredWear logo.
Pixels that are very dark (all channels < threshold) are made transparent.
A soft edge is created by blending the alpha based on luminance.
"""
from PIL import Image
import numpy as np

src = "/home/ubuntu/empowerwear/assets/logo.png"
dst = "/home/ubuntu/empowerwear/assets/logo_transparent.png"

img = Image.open(src).convert("RGBA")
data = np.array(img, dtype=np.float32)

r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]

# Luminance of each pixel (0–255)
lum = 0.299 * r + 0.587 * g + 0.114 * b

# Threshold: pixels darker than this become transparent
threshold = 40
# Feather zone: pixels between threshold and feather_end get partial alpha
feather_end = 80

alpha = np.where(
    lum <= threshold,
    0.0,
    np.where(
        lum >= feather_end,
        255.0,
        (lum - threshold) / (feather_end - threshold) * 255.0
    )
)

data[..., 3] = np.clip(alpha, 0, 255)

result = Image.fromarray(data.astype(np.uint8), "RGBA")
result.save(dst, "PNG")
print(f"Saved transparent logo to {dst}")
print(f"Size: {result.size}")
