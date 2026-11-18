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

class GameplaySystem:
    def __init__(self, car, player, buildings, combat):
        self.car = car
        self.player = player
        self.buildings = buildings
        self.combat = combat

        self.wanted = 0
        self.wanted_timer = 0
        self.money = 0
        self.traffic = []
        self.cops = []
        self.siren_timer = 0
        self.siren_state = False

        # 1. Графические иконки 5 звёзд розыска из твоей текстуры star.png
        star_tex = get_tex('star')
        self.has_star_tex = (star_tex != 'white_cube')
        self.star_icons = []

        for i in range(5):
            # Ставим 5 звёзд в ряд в правом верхнем углу экрана
            icon = Entity(
                parent=camera.ui,
                model='quad',
                texture=star_tex,
                position=(0.56 + i * 0.055, 0.44),
                scale=0.045 if self.has_star_tex else 0.032,
                rotation_z=0 if self.has_star_tex else 45,
                color=color.rgba(40, 40, 40, 140)
            )
            self.star_icons.append(icon)

        # Деньги и миссии
        self.money_text = Text(text='$0', position=(0.54, 0.39), scale=1.4, color=color.lime, background=True)
        self.mission_text = Text(text='MISSION: Drive to the Beacon', position=(-0.85, 0.33), scale=1.05, color=color.yellow, background=True)

        # Светящийся маяк-чекпоинт для миссий
        self.beacon = Entity(model='cube', position=(80, 40, 80), scale=(4.5, 80, 4.5), texture='white_cube', color=color.rgba(255, 220, 0, 110), unlit=True)
        self.beacon_ring = Entity(model='cube', position=(80, 0.2, 80), scale=(7, 0.3, 7), texture='white_cube', color=color.yellow, unlit=True)
        self.new_mission()

        # 2. Более спокойный трафик с нормальными углами поворота (0, 90, 180, 270)
        colors = [color.yellow, color.cyan, color.orange, color.white, color.violet, color.rgb(40, 180, 90)]
        for i in range(18):
            is_desert = (i >= 13)
            pos = self.get_road_pos(is_desert)
            t_car = Entity(
                model='cube',
                position=pos,
                scale=(1.8, 0.9, 3.6),
                texture='white_cube',
                color=random.choice(colors)
            )
            Entity(parent=t_car, model='cube', position=(0, 0.4, 0.2), scale=(0.85, 0.45, 0.35), texture='white_cube', color=color.black)
            t_car.rotation_y = random.choice([0, 90, 180, 270]) if not is_desert else random.choice([90, 270])
            self.traffic.append({'e': t_car, 'speed': random.uniform(11, 18), 'turn_timer': random.uniform(4, 9), 'desert': is_desert})

    def get_road_pos(self, is_desert=False):
        if is_desert:
            return Vec3(random.uniform(460, 1100), 0.5, random.choice([-4.5, 4.5]))
        for _ in range(30):
            rx = random.uniform(-350, 350)
            rz = random.uniform(-350, 350)
            blocked = False
            for b in self.buildings:
                if abs(rx - b.x) < (b.scale_x * 0.5 + 4) and abs(rz - b.z) < (b.scale_z * 0.5 + 4):
                    blocked = True
                    break
            if not blocked:
                return Vec3(rx, 0.5, rz)
        return Vec3(0, 0.5, 40)

    def new_mission(self):
        to_desert = random.choice([True, False])
        pos = self.get_road_pos(to_desert)
        self.beacon.position = Vec3(pos.x, 40, pos.z)
        self.beacon_ring.position = Vec3(pos.x, 0.2, pos.z)
        self.target_zone = 'Mojave Desert' if to_desert else 'Downtown Vice'

    def add_wanted(self, amount=1):
        self.wanted = min(5, self.wanted + amount)
        self.wanted_timer = 18

    def clear_wanted(self):
        self.wanted = 0
        for c in self.cops[:]:
            destroy(c['e'])
            self.cops.remove(c)

    def spawn_cop(self, target_pos):
        angle = random.uniform(0, 360)
        dist = random.uniform(65, 95)
        sx = target_pos.x + math.sin(math.radians(angle)) * dist
        sz = target_pos.z + math.cos(math.radians(angle)) * dist

        cop_car = Entity(model='cube', position=(sx, 0.5, sz), scale=(1.85, 0.92, 3.7), texture='white_cube', color=color.rgb(20, 25, 45))
        Entity(parent=cop_car, model='cube', position=(0, 0.42, 0.2), scale=(0.85, 0.45, 0.35), texture='white_cube', color=color.white)
        light_r = Entity(parent=cop_car, model='cube', position=(-0.25, 0.56, 0), scale=(0.35, 0.16, 0.22), texture='white_cube', color=color.red, unlit=True)
        light_b = Entity(parent=cop_car, model='cube', position=(0.25, 0.56, 0), scale=(0.35, 0.16, 0.22), texture='white_cube', color=color.blue, unlit=True)

        self.cops.append({'e': cop_car, 'lr': light_r, 'lb': light_b, 'speed': 0})

    def is_blocked(self, pos):
        for b in self.buildings:
            if abs(pos.x - b.x) < (b.scale_x * 0.5 + 2.2) and abs(pos.z - b.z) < (b.scale_z * 0.5 + 2.2):
                return True
        return False

    def update(self, in_car, car_speed):
        target = self.car if in_car else self.player

        # 1. Проверка миссии
        dist_m = math.sqrt((target.x - self.beacon_ring.x) ** 2 + (target.z - self.beacon_ring.z) ** 2)
        self.mission_text.text = f'MISSION ({self.target_zone}): {int(dist_m)}m'
        if 6.0 > dist_m:
            self.money += 500
            self.money_text.text = f'${self.money}'
            if self.wanted > 0:
                self.wanted -= 1
            self.new_mission()

        # 2. Обновление звёзд розыска и перекраска иконок star.png
        if self.wanted > 0:
            self.wanted_timer -= time.dt
            if 0 > self.wanted_timer:
                self.wanted -= 1
                self.wanted_timer = 15
        else:
            if len(self.cops) > 0:
                self.clear_wanted()

        for i in range(5):
            if self.wanted > i:
                # Активная звезда ярко горит и слегка переливается сиреной
                if self.has_star_tex:
                    self.star_icons[i].color = color.white if self.siren_state else color.rgb(255, 220, 120)
                else:
                    self.star_icons[i].color = color.gold if self.siren_state else color.red
            else:
                # Неактивная звезда полупрозрачная тёмная
                self.star_icons[i].color = color.rgba(40, 40, 40, 130)

        desired_cops = min(4, self.wanted)
        while desired_cops > len(self.cops):
            self.spawn_cop(target.position)

        self.siren_timer += time.dt
        if self.siren_timer > 0.22:
            self.siren_timer = 0
            self.siren_state = not self.siren_state

        for c in self.cops[:]:
            ce = c['e']
            c['lr'].color = color.red if self.siren_state else color.dark_gray
            c['lb'].color = color.blue if not self.siren_state else color.dark_gray

            to_target = target.position - ce.position
            to_target.y = 0
            dist_c = to_target.length()

            if dist_c > 160:
                destroy(ce)
                self.cops.remove(c)
                continue

            if dist_c > 1:
                desired_yaw = math.degrees(math.atan2(to_target.x, to_target.z))
                ce.rotation_y = lerp_angle(ce.rotation_y, desired_yaw, time.dt * 4.5)
                c['speed'] = lerp(c['speed'], 34 + self.wanted * 2, time.dt * 2)
                next_p = ce.position + ce.forward * c['speed'] * time.dt
                if not self.is_blocked(next_p):
                    ce.position = next_p
                else:
                    ce.rotation_y += 90 * time.dt

            if 2.8 > dist_c:
                push = (self.car.position - ce.position).normalized() * 0.4
                self.car.position += Vec3(push.x, 0, push.z)
                c['speed'] = -8

        # 3. Спокойное движение трафика по сетке улиц
        for t in self.traffic:
            te = t['e']
            t['turn_timer'] -= time.dt
            if 0 > t['turn_timer']:
                t['turn_timer'] = random.uniform(4, 9)
                if t['desert']:
                    te.rotation_y = random.choice([90, 270])
                else:
                    te.rotation_y = random.choice([0, 90, 180, 270])

            next_p = te.position + te.forward * t['speed'] * time.dt
            if self.is_blocked(next_p) or abs(next_p.x) > 1150 or abs(next_p.z) > 700:
                te.rotation_y = (te.rotation_y + 180) % 360
            else:
                te.position = next_p

            if in_car and 2.7 > distance(self.car.position, te.position):
                push_dir = (te.position - self.car.position).normalized()
                te.position += Vec3(push_dir.x, 0, push_dir.z) * 1.8
                if abs(car_speed) > 12 and self.wanted == 0:
                    self.add_wanted(1)
