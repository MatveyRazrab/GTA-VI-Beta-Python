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

class CarDetails:
    def __init__(self, car):
        self.car = car
        self.wheel_slots = []
        self.door_angle = 0
        self.door_timer = 0

        car_tex = get_tex('car')
        body_col = color.white if car_tex != 'white_cube' else color.red
        wheel_tex = get_tex('wheel')
        tire_col = color.white if wheel_tex != 'white_cube' else color.black

        # Приподнимаем кузов над землёй, чтобы стоял ровно на колёсах
        if 0.65 > self.car.y:
            self.car.y = 0.65

        # Прячем старое плоское стекло и статичную наклейку
        for child in car.children[:]:
            if child.color == color.black and child.y > 0.3:
                child.enabled = False
            if child.model and 'quad' in str(child.model.name).lower():
                child.enabled = False

        # 1. Крыша и кабина
        self.cabin = Entity(
            parent=car,
            model='cube',
            position=(0, 0.78, -0.06),
            scale=(0.86, 0.62, 0.54),
            texture=car_tex,
            color=body_col
        )
        Entity(
            parent=self.cabin,
            model='cube',
            position=(0, -0.02, 0.505),
            scale=(0.92, 0.78, 0.02),
            texture='white_cube',
            color=color.dark_gray
        )
        Entity(
            parent=self.cabin,
            model='cube',
            position=(0, -0.02, -0.505),
            scale=(0.92, 0.75, 0.02),
            texture='white_cube',
            color=color.dark_gray
        )

        # 2. Открывающаяся водительская дверь + пасхалка
        self.door_pivot = Entity(parent=car, position=(-0.505, 0.0, 0.24))
        self.door = Entity(
            parent=self.door_pivot,
            model='cube',
            position=(0, 0.02, -0.22),
            scale=(0.05, 0.92, 0.44),
            texture=car_tex,
            color=body_col
        )
        Entity(parent=self.door, model='cube', position=(-0.55, 0.25, -0.3), scale=(0.3, 0.12, 0.22), texture='white_cube', color=color.black)

        decal_tex = get_tex('decal')
        if decal_tex != 'white_cube':
            Entity(
                parent=self.door,
                model='quad',
                texture=decal_tex,
                position=(-0.55, -0.02, 0.0),
                rotation=(0, 90, 0),
                scale=(0.92, 0.65)
            )

        # 3. Независимые 4 колеса с ровным масштабом (1, 1, 1) — больше никогда не сплющатся!
        offsets = [
            (Vec3(-0.52, -0.28, 0.32), True),   # Переднее левое
            (Vec3(0.52, -0.28, 0.32), True),    # Переднее правое
            (Vec3(-0.52, -0.28, -0.32), False), # Заднее левое
            (Vec3(0.52, -0.28, -0.32), False)   # Заднее правое
        ]

        for offset, is_front in offsets:
            steer_node = Entity(position=car.position + offset)
            spin_node = Entity(parent=steer_node)

            # Чёрная 8-гранная покрышка (диаметр 0.68, ширина 0.26)
            Entity(parent=spin_node, model='cube', rotation=(0, 0, 0), scale=(0.26, 0.68, 0.68), texture=wheel_tex, color=tire_col)
            Entity(parent=spin_node, model='cube', rotation=(45, 0, 0), scale=(0.26, 0.68, 0.68), texture=wheel_tex, color=tire_col)

            # Серый колёсный диск внутри
            Entity(parent=spin_node, model='cube', rotation=(0, 0, 0), scale=(0.28, 0.36, 0.36), texture='white_cube', color=color.gray)
            Entity(parent=spin_node, model='cube', rotation=(45, 0, 0), scale=(0.28, 0.36, 0.36), texture='white_cube', color=color.gray)

            self.wheel_slots.append({'steer': steer_node, 'spin': spin_node, 'offset': offset, 'front': is_front, 'steer_ang': 0})

    def trigger_door(self):
        self.door_timer = 1.2

    def update(self, speed, steer_input):
        target_steer = steer_input * 26

        for w in self.wheel_slots:
            # Ставим колесо строго в нужную точку относительно кузова и его поворота
            off = w['offset']
            w['steer'].position = self.car.world_position + self.car.right * off.x + self.car.up * off.y + self.car.forward * off.z

            if w['front']:
                w['steer_ang'] = lerp(w['steer_ang'], target_steer, time.dt * 12)
            w['steer'].rotation = self.car.rotation + Vec3(0, w['steer_ang'], 0)

            # Крутим само колесо от скорости
            w['spin'].rotation_x += speed * 38 * time.dt

        if self.door_timer > 0:
            self.door_timer -= time.dt
            self.door_angle = lerp(self.door_angle, 62, time.dt * 10)
        else:
            self.door_angle = lerp(self.door_angle, 0, time.dt * 8)

        self.door_pivot.rotation_y = self.door_angle


