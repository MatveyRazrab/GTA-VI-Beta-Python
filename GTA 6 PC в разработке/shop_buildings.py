from ursina import *
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(BASE_DIR, 'textures')

def get_tex(name):
    for ext in ['.png', '.jpg', '.jpeg']:
        p = os.path.join(TEX_DIR, name + ext)
        if os.path.exists(p):
            return Texture(p)
    return 'white_cube'

def build_all_shops(buildings):
    # Расчищаем случайные дома рядом с магазинами
    shop_spots = [Vec3(35, 0, 35), Vec3(-45, 0, 35), Vec3(520, 0, 18)]
    for b in buildings[:]:
        for spot in shop_spots:
            if 32 > distance(Vec3(b.x, 0, b.z), spot):
                b.enabled = False
                buildings.remove(b)
                break

    t_roof = get_tex('shop_roof')
    c_roof = color.white if t_roof != 'white_cube' else color.dark_gray

    make_shop(buildings, Vec3(35, 0, 48), 'shop_spray', color.rgb(35, 145, 215), color.cyan, t_roof, c_roof, True)
    make_shop(buildings, Vec3(-45, 0, 48), 'shop_gun', color.rgb(170, 45, 45), color.yellow, t_roof, c_roof, False)
    make_shop(buildings, Vec3(520, 0, 31), 'shop_turbo', color.rgb(125, 45, 175), color.magenta, t_roof, c_roof, True)

def make_shop(buildings, pos, tex_name, fallback_col, neon_col, t_roof, c_roof, is_garage):
    wall_tex = get_tex(tex_name)
    wall_col = color.white if wall_tex != 'white_cube' else fallback_col

    b = Entity(model='cube', position=(pos.x, 4.0, pos.z), scale=(18, 8, 12), texture=wall_tex, texture_scale=(3, 1.5), color=wall_col)
    buildings.append(b)

    # Козырёк и неоновая вывеска
    Entity(model='cube', position=(pos.x, 8.35, pos.z - 1.2), scale=(19.2, 0.7, 14.5), texture=t_roof, texture_scale=(3, 2), color=c_roof)
    Entity(model='cube', position=(pos.x, 9.3, pos.z - 7.8), scale=(12, 1.3, 0.4), texture='white_cube', color=neon_col, unlit=True)

    # Опорные колонны
    Entity(model='cube', position=(pos.x - 8.5, 4.0, pos.z - 7.8), scale=(0.6, 8.0, 0.6), texture=t_roof, color=c_roof)
    Entity(model='cube', position=(pos.x + 8.5, 4.0, pos.z - 7.8), scale=(0.6, 8.0, 0.6), texture=t_roof, color=c_roof)

    if is_garage:
        Entity(model='cube', position=(pos.x, 2.6, pos.z - 6.05), scale=(7.5, 5.2, 0.15), texture='white_cube', color=color.rgb(65, 70, 75))
    else:
        Entity(model='cube', position=(pos.x, 2.0, pos.z - 6.05), scale=(2.6, 4.0, 0.15), texture='white_cube', color=color.black)
        Entity(model='cube', position=(pos.x - 5.2, 2.5, pos.z - 6.05), scale=(4.5, 2.8, 0.15), texture='white_cube', color=color.rgb(25, 35, 55))
        Entity(model='cube', position=(pos.x + 5.2, 2.5, pos.z - 6.05), scale=(4.5, 2.8, 0.15), texture='white_cube', color=color.rgb(25, 35, 55))
