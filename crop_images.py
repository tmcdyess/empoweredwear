from PIL import Image
import os

assets = '/home/ubuntu/empowerwear/assets'

# Each entry: (source_file, front_out, back_out, split_axis)
# split_axis: 'h' = split left/right (horizontal midpoint), 'v' = split top/bottom
products = [
    # 1024x1024 square images — left half = front, right half = back
    ('prod_mymoves_purple.png',    'front_mymoves_purple.jpg',    'back_mymoves_purple.jpg',    'h'),
    ('prod_sheprays_black.png',    'front_sheprays_black.jpg',    'back_sheprays_black.jpg',    'h'),
    ('prod_quitting_teal.png',     'front_quitting_teal.jpg',     'back_quitting_teal.jpg',     'h'),
    ('prod_quitting_red.png',      'front_quitting_red.jpg',      'back_quitting_red.jpg',      'h'),
    ('prod_noshrinking_navy.png',  'front_noshrinking_navy.jpg',  'back_noshrinking_navy.jpg',  'h'),
    # 1536x1024 wide images — left half = front, right half = back
    ('prod_comeback_purple.png',   'front_comeback_purple.jpg',   'back_comeback_purple.jpg',   'h'),
    ('prod_goodgod_navy.png',      'front_goodgod_navy.jpg',      'back_goodgod_navy.jpg',      'h'),
]

for src, front_out, back_out, axis in products:
    img = Image.open(os.path.join(assets, src)).convert('RGB')
    w, h = img.size
    mid = w // 2  # split at horizontal midpoint

    front = img.crop((0, 0, mid, h))
    back  = img.crop((mid, 0, w, h))

    front.save(os.path.join(assets, front_out), 'JPEG', quality=88, optimize=True)
    back.save(os.path.join(assets, back_out),   'JPEG', quality=88, optimize=True)
    print(f'  {src} -> {front_out} ({front.size}), {back_out} ({back.size})')

print('Done.')
