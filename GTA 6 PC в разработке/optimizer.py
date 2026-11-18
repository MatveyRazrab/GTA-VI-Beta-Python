from ursina import *
import math

class GameOptimizer:
    def __init__(self, car, player, buildings):
        self.car = car
        self.player = player
        self.buildings = buildings
        self.cull_timer = 0

        # 1. Убираем тяжёлые коллайдеры у домов
        for b in self.buildings:
            b.collider = None

        # 2. Безопасно объединяем только стволы и листья пальм (по их точному размеру)
        trunks = []
        leaves = []
        for e in scene.entities[:]:
            if e == car or e == player or e in buildings:
                continue
            # Ствол пальмы имеет толщину ровно 0.45
            if abs(e.scale_x - 0.45) < 0.01 and abs(e.scale_z - 0.45) < 0.01 and e.scale_y > 5:
                trunks.append(e)
            # Лист пальмы имеет размер (0.7, 0.12, 2.8)
            elif abs(e.scale_x - 0.7) < 0.01 and abs(e.scale_y - 0.12) < 0.01:
                leaves.append(e)

        if len(trunks) > 0:
            trunk_mesh = Entity(texture=trunks[0].texture, color=trunks[0].color)
            for t in trunks:
                t.world_parent = trunk_mesh
            trunk_mesh.combine(auto_destroy=True)

        if len(leaves) > 0:
            leaf_mesh = Entity(texture=leaves[0].texture, color=leaves[0].color)
            for l in leaves:
                l.world_parent = leaf_mesh
            leaf_mesh.combine(auto_destroy=True)

    def check_circle_building(self, pos, radius):
        for b in self.buildings:
            if not b.enabled:
                continue
            half_x = b.scale_x * 0.5
            half_z = b.scale_z * 0.5

            closest_x = clamp(pos.x, b.x - half_x, b.x + half_x)
            closest_z = clamp(pos.z, b.z - half_z, b.z + half_z)

            dx = pos.x - closest_x
            dz = pos.z - closest_z
            dist_sq = dx * dx + dz * dz

            if dist_sq < radius * radius:
                dist = math.sqrt(dist_sq) if dist_sq > 0.0001 else 0.01
                overlap = radius - dist
                nx = dx / dist
                nz = dz / dist
                return True, Vec3(nx * overlap, 0, nz * overlap), Vec3(nx, 0, nz)
        return False, Vec3(0, 0, 0), Vec3(0, 0, 0)

    def resolve_car_physics(self, speed):
        half_len = self.car.scale_z * 0.34
        rad = self.car.scale_x * 0.52

        front_pt = self.car.position + self.car.forward * half_len
        rear_pt = self.car.position - self.car.forward * half_len

        total_push = Vec3(0, 0, 0)
        hit_normal = Vec3(0, 0, 0)
        collided = False

        for pt in (front_pt, rear_pt):
            hit, push, normal = self.check_circle_building(pt, rad)
            if hit:
                collided = True
                total_push += push
                hit_normal = normal

        if collided:
            self.car.position += total_push
            move_dir = self.car.forward if speed >= 0 else -self.car.forward
            head_on = abs(move_dir.x * hit_normal.x + move_dir.z * hit_normal.z)
            return True, head_on

        return False, 0

    def resolve_player_physics(self):
        hit, push, _ = self.check_circle_building(self.player.position, 0.45)
        if hit:
            self.player.position += push

        dx = self.player.x - self.car.x
        dz = self.player.z - self.car.z
        dist = math.sqrt(dx * dx + dz * dz)
        min_d = 1.65
        if 0.001 < dist < min_d:
            overlap = min_d - dist
            self.player.x += (dx / dist) * overlap
            self.player.z += (dz / dist) * overlap

    def update(self, in_car, speed):
        if in_car:
            self.resolve_car_physics(speed)
        else:
            self.resolve_player_physics()

        # Скрываем дальние здания за 260 метров от игрока для высокого FPS
        self.cull_timer += time.dt
        if self.cull_timer > 0.35:
            self.cull_timer = 0
            px = self.car.x if in_car else self.player.x
            pz = self.car.z if in_car else self.player.z
            for b in self.buildings:
                dist_sq = (b.x - px) ** 2 + (b.z - pz) ** 2
                should_show = dist_sq < 68000
                if b.enabled != should_show:
                    b.enabled = should_show
