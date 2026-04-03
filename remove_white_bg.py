"""
Remove the white/near-white background from the EmpoweredWear logo.
Pixels that are very bright (all channels > threshold) are made transparent.
A soft feather edge is applied for a clean result.
"""
from PIL import Image
import numpy as np

src = "/home/ubuntu/empowerwear/assets/logo_new.png"
dst = "/home/ubuntu/empowerwear/assets/logo_transparent.png"

img = Image.open(src).convert("RGBA")
data = np.array(img, dtype=np.float32)

r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]

# A pixel is "white background" if all channels are very bright
# and the saturation (max-min) is low
max_c = np.maximum(np.maximum(r, g), b)
min_c = np.minimum(np.minimum(r, g), b)
saturation = max_c - min_c  # 0 = grey/white, high = colourful

# Threshold: pixels brighter than this AND low saturation become transparent
bright_threshold = 230
sat_threshold = 30   # low saturation = near-white/grey
feather = 15         # feather zone width

# Condition: bright AND desaturated → background
is_bg = (r >= bright_threshold) & (g >= bright_threshold) & (b >= bright_threshold) & (saturation <= sat_threshold)

# Feather: pixels just inside the threshold get partial alpha
# Use distance from the threshold as a blend factor
brightness = (r + g + b) / 3.0
feather_alpha = np.clip((bright_threshold - brightness) / feather, 0, 1) * 255

new_alpha = np.where(is_bg, 0.0, np.where(brightness > bright_threshold - feather, feather_alpha, 255.0))

data[..., 3] = np.clip(new_alpha, 0, 255)

result = Image.fromarray(data.astype(np.uint8), "RGBA")
result.save(dst, "PNG")
print(f"Saved transparent logo to {dst}")
print(f"Size: {result.size}")
