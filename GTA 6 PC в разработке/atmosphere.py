from ursina import *
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(BASE_DIR, 'textures')

def get_tex(name):
    for ext in ['.png', '.jpg', '.jpeg']:
        p = os.path.join(TEX_DIR, name + ext)
        if os.path.exists(p):
            return Texture(p)
    return 'white_cube'

class AtmosphereSystem:
    def __init__(self, car, buildings):
        self.car = car
        self.buildings = buildings
        self.mode = 0  # 0 - День, 1 - Закат Vice City, 2 - Ночь

        scene.fog_density = 0
        camera.clip_plane_far = 3000

        # 1. Надёжный купол неба с текстурой (чтобы цвет 100% работал и не было белизны)
        sky_tex = get_tex('sky')
        self.bg_sky = Sky(texture='white_cube', color=color.rgb(85, 175, 255))
        self.sky_dome = Entity(
            model='sphere',
            scale=2200,
            double_sided=True,
            texture=sky_tex,
            color=color.rgb(85, 175, 255),
            unlit=True
        )

        # 2. Солнце / Луна в небе
        self.celestial = Entity(model='sphere', position=(250, 280, 350), scale=50, texture='white_cube', color=color.rgb(255, 245, 160), unlit=True)

        # 3. Плывущие 3D-облака
        self.clouds = []
        for _ in range(35):
            cx = random.uniform(-450, 450)
            cz = random.uniform(-450, 450)
            cy = random.uniform(95, 145)
            cloud = Entity(
                model='cube',
                position=(cx, cy, cz),
                scale=(random.uniform(25, 65), random.uniform(4, 9), random.uniform(20, 50)),
                texture='white_cube',
                color=color.rgba(255, 255, 255, 230),
                unlit=True
            )
            self.clouds.append(cloud)

        # 4. Фары машины (включаются на закате и ночью)
        self.headlight_l = Entity(parent=car, model='cube', position=(-0.32, 0.0, 0.51), scale=(0.2, 0.15, 0.05), texture='white_cube', color=color.yellow, unlit=True, enabled=False)
        self.headlight_r = Entity(parent=car, model='cube', position=(0.32, 0.0, 0.51), scale=(0.2, 0.15, 0.05), texture='white_cube', color=color.yellow, unlit=True, enabled=False)
        self.beam_l = Entity(parent=car, model='cone', position=(-0.32, -0.1, 2.2), rotation=(90, 0, 0), scale=(1.2, 3.5, 0.6), texture='white_cube', color=color.rgba(255, 255, 180, 65), unlit=True, enabled=False)
        self.beam_r = Entity(parent=car, model='cone', position=(0.32, -0.1, 2.2), rotation=(90, 0, 0), scale=(1.2, 3.5, 0.6), texture='white_cube', color=color.rgba(255, 255, 180, 65), unlit=True, enabled=False)

        # 5. Пальмы с поддержкой твоих текстур palm_trunk.png и palm_leaf.png
        self.spawn_palms(65)

        self.apply_time()

    def spawn_palms(self, count):
        trunk_tex = get_tex('palm_trunk')
        leaf_tex = get_tex('palm_leaf')

        trunk_col = color.white if trunk_tex != 'white_cube' else color.rgb(125, 85, 50)
        leaf_col = color.white if leaf_tex != 'white_cube' else color.rgb(35, 160, 60)

        for _ in range(count):
            rx = random.uniform(-320, 320)
            rz = random.uniform(-320, 320)
            blocked = False
            for b in self.buildings:
                if abs(rx - b.x) < (b.scale_x / 2 + 2.5) and abs(rz - b.z) < (b.scale_z / 2 + 2.5):
                    blocked = True
                    break
            if blocked:
                continue

            h = random.uniform(6.5, 10.5)
            palm = Entity(position=(rx, 0, rz), rotation_y=random.uniform(0, 360))
            Entity(parent=palm, model='cube', position=(0, h / 2, 0), scale=(0.45, h, 0.45), texture=trunk_tex, color=trunk_col)
            for angle in range(0, 360, 60):
                leaf = Entity(parent=palm, position=(0, h, 0), rotation=(25, angle, 0))
                Entity(parent=leaf, model='cube', position=(0, 0, 1.4), scale=(0.7, 0.12, 2.8), texture=leaf_tex, color=leaf_col)

    def next_time(self):
        self.mode = (self.mode + 1) % 3
        self.apply_time()

    def apply_time(self):
        if self.mode == 0:  # ДЕНЬ
            window.color = color.rgb(85, 175, 255)
            self.bg_sky.color = color.rgb(85, 175, 255)
            self.celestial.color = color.rgb(255, 245, 160)
            for c in self.clouds:
                c.color = color.rgba(255, 255, 255, 230)
            self.toggle_lights(False)

        elif self.mode == 1:  # ЗАКАТ VICE CITY
            window.color = color.rgb(255, 105, 150)
            self.bg_sky.color = color.rgb(255, 105, 150)
            self.celestial.color = color.rgb(255, 155, 55)
            for c in self.clouds:
                c.color = color.rgba(255, 180, 195, 220)
            self.toggle_lights(True)

        else:  # НОЧЬ
            window.color = color.rgb(14, 18, 42)
            self.bg_sky.color = color.rgb(14, 18, 42)
            self.celestial.color = color.rgb(230, 235, 255)
            for c in self.clouds:
                c.color = color.rgba(45, 55, 95, 180)
            self.toggle_lights(True)

    def toggle_lights(self, state):
        self.headlight_l.enabled = state
        self.headlight_r.enabled = state
        self.beam_l.enabled = state
        self.beam_r.enabled = state

    def update(self):
        self.sky_dome.position = self.car.position
        for c in self.clouds:
            c.x += 2.5 * time.dt
            if c.x > 480:
                c.x = -480

