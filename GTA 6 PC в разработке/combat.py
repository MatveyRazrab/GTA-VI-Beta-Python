from ursina import *
import random
import math

class CombatSystem:
    def __init__(self, player, right_arm, car, buildings):
        self.player = player
        self.car = car
        self.buildings = buildings
        self.bullets = []
        self.effects = []
        self.npcs = []

        # Привязываем пистолет к нерастянутому суставу плеча (parent=right_arm.parent), чтобы не плющило!
        arm_pivot = right_arm.parent
        self.gun = Entity(parent=arm_pivot, position=(0, -0.62, 0.12))
        self.barrel = Entity(parent=self.gun, model='cube', position=(0, 0.04, 0.14), scale=(0.08, 0.08, 0.32), color=color.rgb(45, 45, 50))
        self.grip = Entity(parent=self.gun, model='cube', position=(0, -0.07, 0.02), rotation=(18, 0, 0), scale=(0.07, 0.18, 0.09), color=color.rgb(20, 20, 20))

        # Зелёный прицел-крестик строго по центру экрана
        self.crosshair = Text(text='+', origin=(0, 0), position=(0, 0), scale=2.2, color=color.lime, enabled=False)

        for _ in range(25):
            self.spawn_npc()

    def get_free_pos(self):
        for _ in range(30):
            rx = random.uniform(-250, 250)
            rz = random.uniform(-250, 250)
            pos = Vec3(rx, 0, rz)
            blocked = False
            for b in self.buildings:
                if abs(pos.x - b.x) < (b.scale_x / 2 + 1.5) and abs(pos.z - b.z) < (b.scale_z / 2 + 1.5):
                    blocked = True
                    break
            if not blocked:
                return pos
        return Vec3(0, 0, 15)

    def spawn_npc(self):
        pos = self.get_free_pos()
        npc = Entity(position=pos)
        col_shirt = random.choice([color.orange, color.yellow, color.lime, color.pink, color.violet, color.azure])
        col_pants = random.choice([color.dark_gray, color.blue, color.brown, color.black])

        Entity(parent=npc, model='cube', position=(0, 1.15, 0), scale=(0.55, 0.7, 0.3), color=col_shirt)
        Entity(parent=npc, model='cube', position=(0, 1.72, 0), scale=(0.38, 0.38, 0.38), color=color.rgb(235, 190, 155))
        l_leg = Entity(parent=npc, position=(-0.15, 0.8, 0))
        Entity(parent=l_leg, model='cube', position=(0, -0.4, 0), scale=(0.2, 0.8, 0.2), color=col_pants)
        r_leg = Entity(parent=npc, position=(0.15, 0.8, 0))
        Entity(parent=r_leg, model='cube', position=(0, -0.4, 0), scale=(0.2, 0.8, 0.2), color=col_pants)

        self.npcs.append({
            'root': npc, 'l_leg': l_leg, 'r_leg': r_leg,
            'dir': random.uniform(0, 360), 'timer': random.uniform(1, 5),
            'alive': True, 'respawn': 0, 'walk': random.uniform(0, 6)
        })

    def splash(self, pos, count=10):
        for _ in range(count):
            p = Entity(model='sphere', position=pos + Vec3(0, 1.1, 0), scale=random.uniform(0.12, 0.28), color=color.rgb(180, 0, 0))
            vel = Vec3(random.uniform(-3, 3), random.uniform(1, 4.5), random.uniform(-3, 3))
            self.effects.append({'e': p, 'vel': vel, 'life': 0.55})

    def shoot(self, in_car):
        if in_car:
            return
        # Вычисляем точку вдали, куда смотрит прицел, чтобы пуля летела точно в крестик
        target_point = camera.world_position + camera.forward * 100
        start_pos = self.barrel.world_position + self.barrel.forward * 0.2
        shoot_dir = (target_point - start_pos).normalized()

        b = Entity(model='sphere', position=start_pos, scale=0.14, color=color.yellow)
        self.bullets.append({'e': b, 'dir': shoot_dir, 'life': 1.5})

        flash = Entity(model='sphere', position=start_pos, scale=0.3, color=color.orange)
        self.effects.append({'e': flash, 'vel': Vec3(0, 0, 0), 'life': 0.06})

    def is_inside_building(self, pos):
        for b in self.buildings:
            if abs(pos.x - b.x) < (b.scale_x / 2 + 0.8) and abs(pos.z - b.z) < (b.scale_z / 2 + 0.8):
                return True
        return False

    def update(self, in_car, car_speed):
        self.crosshair.enabled = not in_car

        # Когда пешком — поднимаем руку с пистолетом вперёд и поворачиваем героя по камере
        if not in_car:
            arm_pivot = self.gun.parent
            arm_pivot.rotation_x = -85
            self.player.rotation_y = camera.parent.rotation_y

        for ef in self.effects[:]:
            ef['e'].position += ef['vel'] * time.dt
            ef['vel'].y -= 9.8 * time.dt
            ef['life'] -= time.dt
            if 0 > ef['life']:
                destroy(ef['e'])
                self.effects.remove(ef)

        for b in self.bullets[:]:
            b['e'].position += b['dir'] * 95 * time.dt
            b['life'] -= time.dt
            hit = False
            for n in self.npcs:
                if n['alive'] and distance(b['e'].position, n['root'].position + Vec3(0, 1.1, 0)) < 1.2:
                    n['alive'] = False
                    n['root'].rotation_x = 90
                    n['root'].y = 0.25
                    n['respawn'] = 12
                    self.splash(n['root'].position, 14)
                    hit = True
                    break
            if hit or self.is_inside_building(b['e'].position) or 0 > b['life']:
                destroy(b['e'])
                self.bullets.remove(b)

        for n in self.npcs:
            if not n['alive']:
                n['respawn'] -= time.dt
                if 0 > n['respawn']:
                    n['alive'] = True
                    n['root'].rotation_x = 0
                    n['root'].position = self.get_free_pos()
                continue

            if abs(car_speed) > 6 and distance(self.car.position, n['root'].position) < 2.3:
                n['alive'] = False
                n['root'].rotation_x = 90
                n['root'].y = 0.25
                n['respawn'] = 12
                self.splash(n['root'].position, 18)
                continue

            n['timer'] -= time.dt
            if 0 > n['timer']:
                n['dir'] = random.uniform(0, 360)
                n['timer'] = random.uniform(2, 6)

            n['root'].rotation_y = n['dir']
            next_pos = n['root'].position + n['root'].forward * 2.5 * time.dt

            if self.is_inside_building(next_pos):
                n['dir'] = (n['dir'] + random.uniform(120, 240)) % 360
                n['timer'] = random.uniform(2, 4)
            else:
                n['root'].position = next_pos

            n['walk'] += time.dt * 7
            n['l_leg'].rotation_x = math.sin(n['walk']) * 30
            n['r_leg'].rotation_x = -math.sin(n['walk']) * 30
