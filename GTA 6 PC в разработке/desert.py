from ursina import *
import os
import random
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(BASE_DIR, 'textures')

def get_tex(name):
    for ext in ['.png', '.jpg', '.jpeg']:
        p = os.path.join(TEX_DIR, name + ext)
        if os.path.exists(p):
            return Texture(p)
    return 'white_cube'

class DesertBiome:
    def __init__(self, car, player):
        self.car = car
        self.player = player
        self.obstacles = []  # Точные прямоугольные хитбоксы, на 100% совпадающие со скалами

        sand_tex = get_tex('sand')
        rock_tex = get_tex('rock')
        cactus_tex = get_tex('cactus')

        sand_col = color.white if sand_tex != 'white_cube' else color.rgb(232, 198, 130)
        rock_col = color.white if rock_tex != 'white_cube' else color.rgb(185, 105, 65)
        cactus_col = color.white if cactus_tex != 'white_cube' else color.rgb(45, 135, 55)

        # 1. Песчаная земля пустыни
        self.ground = Entity(
            model='plane',
            position=(835, 0.02, 0),
            scale=(820, 1, 1600),
            texture=sand_tex,
            texture_scale=(80, 160),
            color=sand_col
        )

        # 2. Пустынное шоссе и жёлтая разметка
        self.highway = Entity(
            model='plane',
            position=(835, 0.04, 0),
            scale=(820, 1, 18),
            texture='white_cube',
            color=color.rgb(55, 55, 60)
        )
        self.stripe = Entity(
            model='plane',
            position=(835, 0.05, 0),
            scale=(820, 1, 0.5),
            texture='white_cube',
            color=color.yellow
        )

        # 3. Скалы-каньоны (чёткое совпадение модели и хитбокса 1 к 1)
        for _ in range(30):
            rx = random.uniform(460, 1180)
            rz = random.uniform(-650, 650)
            if 24 > abs(rz):
                continue

            sx = random.uniform(14, 38)
            sy = random.uniform(10, 34)
            sz = random.uniform(14, 38)

            # Нижний массив скалы
            Entity(
                model='cube',
                position=(rx, sy * 0.5, rz),
                scale=(sx, sy, sz),
                texture=rock_tex,
                texture_scale=(2, 2),
                color=rock_col
            )
            # Верхний уступ для красивого силуэта каньона
            Entity(
                model='cube',
                position=(rx, sy + sy * 0.2, rz),
                scale=(sx * 0.65, sy * 0.4, sz * 0.65),
                texture=rock_tex,
                texture_scale=(1.5, 1.5),
                color=rock_col
            )
            self.obstacles.append({'x': rx, 'z': rz, 'hx': sx * 0.5, 'hz': sz * 0.5})

        # 4. Кактусы (объединяем в один меш для 60+ FPS)
        cactus_root = Entity(texture=cactus_tex, color=cactus_col)
        for _ in range(65):
            cx = random.uniform(440, 1180)
            cz = random.uniform(-650, 650)
            if 15 > abs(cz):
                continue

            h = random.uniform(2.5, 4.5)
            Entity(parent=cactus_root, model='cube', position=(cx, h / 2, cz), scale=(0.45, h, 0.45))
            Entity(parent=cactus_root, model='cube', position=(cx + 0.45, h * 0.6, cz), scale=(0.6, 0.3, 0.3))
            Entity(parent=cactus_root, model='cube', position=(cx + 0.65, h * 0.78, cz), scale=(0.3, h * 0.35, 0.3))
            Entity(parent=cactus_root, model='cube', position=(cx - 0.45, h * 0.5, cz), scale=(0.6, 0.3, 0.3))
            Entity(parent=cactus_root, model='cube', position=(cx - 0.65, h * 0.68, cz), scale=(0.3, h * 0.35, 0.3))

        cactus_root.combine(auto_destroy=True)

        # 5. Индикатор района
        self.zone_text = Text(text='Downtown Vice', position=(0.52, -0.44), scale=1.3, color=color.cyan, background=True)

    def push_out_of_rock(self, pt, radius):
        for obs in self.obstacles:
            closest_x = clamp(pt.x, obs['x'] - obs['hx'], obs['x'] + obs['hx'])
            closest_z = clamp(pt.z, obs['z'] - obs['hz'], obs['z'] + obs['hz'])

            dx = pt.x - closest_x
            dz = pt.z - closest_z
            dist_sq = dx * dx + dz * dz

            if radius * radius > dist_sq:
                dist = math.sqrt(dist_sq) if dist_sq > 0.0001 else 0.01
                overlap = radius - dist
                return Vec3((dx / dist) * overlap, 0, (dz / dist) * overlap)
        return Vec3(0, 0, 0)

    def update(self, in_car):
        target = self.car if in_car else self.player

        if target.x > 425:
            if self.zone_text.text != 'Mojave Desert':
                self.zone_text.text = 'Mojave Desert'
                self.zone_text.color = color.orange
        else:
            if self.zone_text.text != 'Downtown Vice':
                self.zone_text.text = 'Downtown Vice'
                self.zone_text.color = color.cyan

        # Точные хитбоксы (проверяем перед и зад машины или тело пешехода)
        if in_car:
            half_len = self.car.scale_z * 0.35
            rad = self.car.scale_x * 0.55
            for pt in (self.car.position + self.car.forward * half_len, self.car.position - self.car.forward * half_len):
                push = self.push_out_of_rock(pt, rad)
                self.car.position += push
        else:
            push = self.push_out_of_rock(self.player.position, 0.5)
            self.player.position += push
