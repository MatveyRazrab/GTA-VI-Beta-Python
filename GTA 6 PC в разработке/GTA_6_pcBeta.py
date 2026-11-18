from ursina import *
import os
import random
import math
from combat import CombatSystem
from atmosphere import AtmosphereSystem
from optimizer import GameOptimizer
from desert import DesertBiome
from gameplay import GameplaySystem
from car_details import CarDetails
from shops import ShopSystem
from expansion import ExpansionPack

app = Ursina()

window.title = 'GTA 6 Python - Big City'
window.borderless = False
window.color = color.rgb(135, 206, 250)

mouse.locked = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(BASE_DIR, 'textures')

def get_texture(name):
    for ext in ['.png', '.jpg', '.jpeg']:
        full_path = os.path.join(TEX_DIR, name + ext)
        if os.path.exists(full_path):
            return Texture(full_path)
    return 'white_cube'

road_tex = get_texture('road')
ground = Entity(
    model='plane',
    scale=(2000, 1, 2000),
    color=color.dark_gray if road_tex == 'white_cube' else color.white,
    texture=road_tex,
    texture_scale=(200, 200),
    collider='box'
)

tex_wood = get_texture('wood')
tex_metal = get_texture('metal')
tex_concrete = get_texture('concrete')

buildings = []

for x in range(-400, 401, 45):
    for z in range(-400, 401, 45):
        if abs(x) < 30 and abs(z) < 30:
            continue
        if random.random() > 0.3:
            b_type = random.choice(['wood', 'metal', 'concrete'])
            if b_type == 'wood':
                h = random.randint(8, 16)
                b_tex = tex_wood
                fallback_color = color.brown
            elif b_type == 'metal':
                h = random.randint(18, 32)
                b_tex = tex_metal
                fallback_color = color.light_gray
            else:
                h = random.randint(35, 70)
                b_tex = tex_concrete
                fallback_color = color.gray

            b_color = color.white if b_tex != 'white_cube' else fallback_color
            b = Entity(
                model='cube',
                position=(x, h / 2, z),
                scale=(22, h, 22),
                texture=b_tex,
                texture_scale=(2, max(1, h // 10)),
                color=b_color,
                collider='box'
            )
            buildings.append(b)

car_tex = get_texture('car')
base_car_scale = Vec3(1.8, 0.9, 3.6)
base_car_color = color.white if car_tex != 'white_cube' else color.red

car = Entity(
    model='cube',
    position=(0, 0.5, 0),
    scale=base_car_scale,
    texture=car_tex,
    color=base_car_color,
    collider='box'
)
windshield = Entity(parent=car, model='cube', position=(0, 0.4, 0.2), scale=(0.85, 0.45, 0.35), color=color.black)

decal_tex = get_texture('decal')
if decal_tex != 'white_cube':
    door_sticker = Entity(
        parent=car,
        model='quad',
        texture=decal_tex,
        position=(-0.505, 0.0, 0.0),
        rotation=(0, 90, 0),
        scale=(0.65, 0.45)
    )

tex_shirt = get_texture('shirt')
tex_pants = get_texture('pants')
tex_face = get_texture('face')

shirt_col = color.white if tex_shirt != 'white_cube' else color.cyan
pants_col = color.white if tex_pants != 'white_cube' else color.blue
skin_col = color.rgb(240, 195, 160)

player = Entity(position=(0, 0, 0), enabled=False)
player_collider = Entity(parent=player, model='cube', position=(0, 0.9, 0), scale=(0.6, 1.8, 0.6), visible=False, collider='box')
torso = Entity(parent=player, model='cube', position=(0, 1.15, 0), scale=(0.55, 0.7, 0.3), texture=tex_shirt, color=shirt_col)

head = Entity(parent=player, model='cube', position=(0, 1.72, 0), scale=(0.4, 0.4, 0.4), color=skin_col)
if tex_face != 'white_cube':
    face_plane = Entity(parent=head, model='quad', position=(0, 0, 0.51), rotation=(0, 180, 0), texture=tex_face, scale=(0.95, 0.95))
else:
    Entity(parent=head, model='cube', position=(-0.2, 0.1, 0.5), scale=(0.15, 0.1, 0.05), color=color.black)
    Entity(parent=head, model='cube', position=(0.2, 0.1, 0.5), scale=(0.15, 0.1, 0.05), color=color.black)

left_arm_pivot = Entity(parent=player, position=(-0.38, 1.45, 0))
left_arm = Entity(parent=left_arm_pivot, model='cube', position=(0, -0.32, 0), scale=(0.18, 0.65, 0.18), texture=tex_shirt, color=shirt_col)

right_arm_pivot = Entity(parent=player, position=(0.38, 1.45, 0))
right_arm = Entity(parent=right_arm_pivot, model='cube', position=(0, -0.32, 0), scale=(0.18, 0.65, 0.18), texture=tex_shirt, color=shirt_col)

left_leg_pivot = Entity(parent=player, position=(-0.15, 0.8, 0))
left_leg = Entity(parent=left_leg_pivot, model='cube', position=(0, -0.4, 0), scale=(0.22, 0.8, 0.22), texture=tex_pants, color=pants_col)

right_leg_pivot = Entity(parent=player, position=(0.15, 0.8, 0))
right_leg = Entity(parent=right_leg_pivot, model='cube', position=(0, -0.4, 0), scale=(0.22, 0.8, 0.22), texture=tex_pants, color=pants_col)

hint_text = Text(text='[F] Exit/Enter | [R] Repair', position=(-0.85, 0.45), scale=1.1, color=color.white, background=True)
hp_text = Text(text='Car HP: 100%', position=(-0.85, 0.39), scale=1.1, color=color.lime, background=True)
combat = CombatSystem(player, right_arm, car, buildings)
atmo = AtmosphereSystem(car, buildings)
opt = GameOptimizer(car, player, buildings)
desert = DesertBiome(car, player)
gameplay = GameplaySystem(car, player, buildings, combat)
car_det = CarDetails(car)
shops = ShopSystem(car, player, gameplay, combat, lambda: repair_car())
exp_pack = ExpansionPack(car, player, buildings, combat, gameplay, shops)
camera_pivot = Entity(position=car.position + Vec3(0, 1.5, 0))
camera.parent = camera_pivot
camera.position = (0, 0, -12)
camera.rotation = (0, 0, 0)

cam_yaw = 0
cam_pitch = 15
mouse_idle_timer = 0

in_car = True
speed = 0
max_speed = 45
turn_speed = 110

car_hp = 100
is_wrecked = False
burn_timer = 0
smoke_timer = 0
particles = []
shake_amount = 0

walk_timer = 0
velocity_y = 0
is_grounded = True

def spawn_particle(pos, col, size, up_speed, life):
    p = Entity(model='sphere', position=pos, scale=size, color=col)
    particles.append({'entity': p, 'vel': Vec3(random.uniform(-1, 1), up_speed, random.uniform(-1, 1)), 'life': life, 'max_life': life})

def explode_car():
    global is_wrecked, car_hp, speed, shake_amount
    if is_wrecked:
        return
    is_wrecked = True
    car_hp = 0
    speed = 0
    shake_amount = 0.6
    car.color = color.rgb(40, 40, 40)
    car.y += 1.2
    car.rotation_z = random.choice([-12, 12])
    for _ in range(25):
        col = random.choice([color.orange, color.red, color.yellow, color.dark_gray])
        spawn_particle(car.position + Vec3(random.uniform(-1, 1), 0.5, random.uniform(-1.5, 1.5)), col, random.uniform(0.8, 2.2), random.uniform(4, 10), 1.2)

def repair_car():
    global car_hp, is_wrecked, burn_timer
    car_hp = 100
    is_wrecked = False
    burn_timer = 0
    car.scale = base_car_scale
    car.color = base_car_color
    car.rotation_x = 0
    car.rotation_z = 0
    car.y = 0.5

def update():
    global speed, cam_yaw, cam_pitch, mouse_idle_timer, walk_timer, velocity_y, is_grounded
    global car_hp, burn_timer, smoke_timer, shake_amount
    combat.update(in_car, speed)
    atmo.update()
    opt.update(in_car, speed)
    desert.update(in_car)
    gameplay.update(in_car, speed)
    
    for p in particles[:]:
        p['entity'].position += p['vel'] * time.dt
        p['entity'].scale += Vec3(1.5, 1.5, 1.5) * time.dt
        p['life'] -= time.dt
        p['entity'].alpha = max(0, p['life'] / p['max_life'])
        if 0.5 > p['life']:
            destroy(p['entity'])
            particles.remove(p)
    if is_wrecked and car.y > 0.5:
        car.y = max(0.5, car.y - 6 * time.dt)

    if not is_wrecked and car_hp < 55 :
        smoke_timer += time.dt
        if smoke_timer > 0.12 :
            smoke_timer = 0
            hood_pos = car.position + car.forward * 1.2 + Vec3(0, 0.5, 0)
            if car_hp < 23 :
                spawn_particle(hood_pos, random.choice([color.orange, color.red]), 0.5, 3.5, 0.6)
            else:
                spawn_particle(hood_pos, color.dark_gray, 0.45, 2.5, 0.9)

    if not is_wrecked and car_hp < 23 :
        burn_timer += time.dt
        if burn_timer > 4.5 :
            explode_car()

    if is_wrecked:
        hp_text.text = f'Car HP: {int(car_hp)}%'
        hp_text.color = color.red
    else:
        hp_text.text = f'Car HP: {int(car_hp)}%'
        hp_text.color = color.lime if car_hp > 55 else (color.yellow if car_hp > 22 else color.red)

    if mouse.locked and (abs(mouse.velocity.x) > 0.0005 or abs(mouse.velocity.y) > 0.0005):
        cam_yaw += mouse.velocity.x * 150
        cam_pitch -= mouse.velocity.y * 150
        cam_pitch = clamp(cam_pitch, -35, 75)
        mouse_idle_timer = 0
    else:
        mouse_idle_timer += time.dt
        if in_car and mouse_idle_timer > 1.5 and abs(speed) > 2:
            cam_yaw = lerp_angle(cam_yaw, car.rotation_y, time.dt * 2.5)

    if in_car:
        old_pos = car.position
        current_max = 0 if is_wrecked else (max_speed * 0.55 if car_hp < 23 else max_speed)

        if not is_wrecked:
            if held_keys['w']:
                speed = lerp(speed, current_max, time.dt * 1.5)
            elif held_keys['s']:
                speed = lerp(speed, -current_max / 2, time.dt * 2)
            else:
                speed = lerp(speed, 0, time.dt * 2.5)

            if abs(speed) > 0.5:
                direction = 1 if speed > 0 else -1
                if held_keys['a']:
                    car.rotation_y -= turn_speed * time.dt * direction
                if held_keys['d']:
                    car.rotation_y += turn_speed * time.dt * direction
        else:
            speed = 0

        car.position += car.forward * speed * time.dt

        hit_car, head_on = opt.resolve_car_physics(speed)
        if hit_car and head_on > 0.35:
            impact_speed = abs(speed)
            speed = speed * (1 - head_on * 0.85)

            if impact_speed > 8 and not is_wrecked:
                dmg = (impact_speed - 6) * 1.4
                car_hp = max(0, car_hp - dmg)
                shake_amount = min(0.5, impact_speed / 80)

                car.scale_z = max(2.6, car.scale_z - dmg * 0.012)
                car.scale_x = min(2.1, car.scale_x + dmg * 0.004)
                car.rotation_z = clamp(car.rotation_z + random.uniform(-3, 3), -10, 10)

                for _ in range(6):
                    spawn_particle(car.position + car.forward * 1.5, color.yellow, 0.2, random.uniform(1, 4), 0.35)

                if car_hp < 1 :
                    explode_car()

        camera.position = lerp(camera.position, Vec3(0, 0, -12), time.dt * 5)
        camera_pivot.position = lerp(camera_pivot.position, car.position + Vec3(0, 1.5, 0), time.dt * 15)
        hint_text.text = '[F] Exit/Enter | [R] Repair'

    else:
        speed = lerp(speed, 0, time.dt * 3)
        car.position += car.forward * speed * time.dt

        cam_forward = Vec3(math.sin(math.radians(cam_yaw)), 0, math.cos(math.radians(cam_yaw))).normalized()
        cam_right = Vec3(math.cos(math.radians(cam_yaw)), 0, -math.sin(math.radians(cam_yaw))).normalized()

        move_dir = Vec3(0, 0, 0)
        if held_keys['w']:
            move_dir += cam_forward
        if held_keys['s']:
            move_dir -= cam_forward
        if held_keys['d']:
            move_dir += cam_right
        if held_keys['a']:
            move_dir -= cam_right

        is_sprinting = held_keys['shift']
        move_speed = 11 if is_sprinting else 6

        if move_dir.length() > 0:
            move_dir = move_dir.normalized()
            old_p_pos = player.position

            target_angle = math.degrees(math.atan2(move_dir.x, move_dir.z))
            player.rotation_y = lerp_angle(player.rotation_y, target_angle, time.dt * 12)

            player.position += move_dir * move_speed * time.dt

            p_hit = player_collider.intersects()
            if p_hit.hit and (p_hit.entity in buildings or p_hit.entity == car):
                player.position = old_p_pos

            anim_speed = 16 if is_sprinting else 10
            swing_angle = 55 if is_sprinting else 35
            walk_timer += time.dt * anim_speed

            left_leg_pivot.rotation_x = math.sin(walk_timer) * swing_angle
            right_leg_pivot.rotation_x = -math.sin(walk_timer) * swing_angle
            left_arm_pivot.rotation_x = -math.sin(walk_timer) * swing_angle
            right_arm_pivot.rotation_x = math.sin(walk_timer) * swing_angle
            torso.y = 1.15 + abs(math.cos(walk_timer)) * 0.04
            head.y = 1.72 + abs(math.cos(walk_timer)) * 0.04
        else:
            walk_timer += time.dt * 2
            left_leg_pivot.rotation_x = lerp(left_leg_pivot.rotation_x, 0, time.dt * 10)
            right_leg_pivot.rotation_x = lerp(right_leg_pivot.rotation_x, 0, time.dt * 10)
            left_arm_pivot.rotation_x = lerp(left_arm_pivot.rotation_x, 0, time.dt * 10)
            right_arm_pivot.rotation_x = lerp(right_arm_pivot.rotation_x, 0, time.dt * 10)
            torso.y = 1.15 + math.sin(walk_timer) * 0.015
            head.y = 1.72 + math.sin(walk_timer) * 0.015

        if not is_grounded:
            velocity_y -= 25 * time.dt
            player.y += velocity_y * time.dt
            if player.y < 0 :
                player.y = 0
                velocity_y = 0
                is_grounded = True

        camera.position = lerp(camera.position, Vec3(0, 0, -6.5), time.dt * 6)
        camera_pivot.position = lerp(camera_pivot.position, player.position + Vec3(0, 1.6, 0), time.dt * 15)

        if distance(player.position, car.position) < 4.5:
            hint_text.text = '[F] Exit/Enter | [R] Repair'
        else:
            hint_text.text = '[F] Exit/Enter | [R] Repair'

    if shake_amount > 0:
        camera_pivot.position += Vec3(random.uniform(-shake_amount, shake_amount), random.uniform(-shake_amount, shake_amount), 0)
        shake_amount = max(0, shake_amount - time.dt * 2)

    camera_pivot.rotation_x = cam_pitch
    camera_pivot.rotation_y = cam_yaw
    camera_pivot.rotation_z = 0
    steer_val = (1 if held_keys['d'] else 0) - (1 if held_keys['a'] else 0) if in_car else 0
    car_det.update(speed, steer_val)
    shops.update(in_car, speed)
    exp_pack.update(in_car)

def input(key):
    global in_car, velocity_y, is_grounded
    if key == 'left mouse down':
        combat.shoot(in_car)
        if not in_car: gameplay.add_wanted(1)
    if key == 'c': gameplay.clear_wanted()
    exp_pack.input(key, in_car)

    if key == 't': atmo.next_time()
    if key == 'tab':
        mouse.locked = not mouse.locked

    if key == 'r':
        repair_car()

    if key == 'f':
        car_det.trigger_door()
        if in_car:
            in_car = False
            player.position = car.position - car.right * 2.2
            player.y = 0
            player.rotation_y = car.rotation_y
            player.enabled = True
        else:
            if distance(player.position, car.position) < 4.5:
                in_car = True
                player.enabled = False

    if key == 'space' and not in_car and is_grounded:
        velocity_y = 9.5
        is_grounded = False

app.run()
















