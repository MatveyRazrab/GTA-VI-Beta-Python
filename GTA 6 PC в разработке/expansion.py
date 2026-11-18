from ursina import *
import random
from sounds import SoundGenerator
from shop_buildings import build_all_shops

class ExpansionPack:
    def __init__(self, car, player, buildings, combat, gameplay, shops):
        self.car = car
        self.player = player
        self.buildings = buildings
        self.combat = combat
        self.gameplay = gameplay
        self.shops = shops

        self.sfx = SoundGenerator()
        self.siren_cd = 0

        self.char_idx = 0
        self.characters = [
            {'name': 'Tommy (Vice)', 'shirt': color.cyan, 'pants': color.blue, 'skin': color.rgb(240, 195, 160)},
            {'name': 'CJ (Grove)', 'shirt': color.white, 'pants': color.rgb(40, 75, 130), 'skin': color.rgb(125, 78, 48)},
            {'name': 'Claude (Liberty)', 'shirt': color.rgb(30, 30, 35), 'pants': color.rgb(45, 70, 50), 'skin': color.rgb(235, 190, 155)}
        ]
        self.char_text = Text(text='HERO: Tommy (Vice) [V]', position=(-0.85, 0.27), scale=1.0, color=color.cyan, background=True)

        self.weapon_id = 1
        self.unlocked = {1: True, 2: False, 3: False, 4: False}
        self.rockets = []
        self.fire_cd = 0
        self.weapon_text = Text(text='WEAPON [1-4]: Pistol', position=(-0.85, 0.21), scale=1.05, color=color.orange, background=True)

        build_all_shops(self.buildings)
        self.setup_extra_weapons()

    def setup_extra_weapons(self):
        self.shops.shops.append({'name': 'Ammu-Nation: Shotgun', 'cost': 700, 'pos': Vec3(-53, 0.2, 35), 'col': color.orange, 'type': 'shotgun'})
        self.shops.shops.append({'name': 'Ammu-Nation: RPG Launcher', 'cost': 1200, 'pos': Vec3(-37, 0.2, 35), 'col': color.yellow, 'type': 'rpg'})

        for p_pos, p_col in [(Vec3(-53, 0.2, 35), color.orange), (Vec3(-37, 0.2, 35), color.yellow)]:
            Entity(model='cube', position=p_pos, scale=(5.5, 0.25, 5.5), texture='white_cube', color=p_col, unlit=True)

        orig_buy = self.shops.try_buy
        def custom_buy(shop):
            if shop['type'] == 'gun':
                if self.gameplay.money >= shop['cost'] and not self.unlocked[2]:
                    self.unlocked[2] = True
                    self.select_weapon(2)
                    self.sfx.play('buy.wav')
                orig_buy(shop)
                return

            if shop['type'] in ('shotgun', 'rpg'):
                w_num = 3 if shop['type'] == 'shotgun' else 4
                if self.unlocked[w_num]:
                    self.shops.show_message("Already owned!", color.yellow)
                    return
                if shop['cost'] > self.gameplay.money:
                    self.shops.show_message(f"Need ${shop['cost']}!", color.red)
                    return
                self.gameplay.money -= shop['cost']
                self.gameplay.money_text.text = f"${self.gameplay.money}"
                self.unlocked[w_num] = True
                self.select_weapon(w_num)
                self.sfx.play('buy.wav')
                self.shops.show_message(f"BOUGHT: {shop['name']}! Press [{w_num}]", color.lime)
                return

            prev = self.gameplay.money
            orig_buy(shop)
            if prev > self.gameplay.money:
                self.sfx.play('buy.wav')

        self.shops.try_buy = custom_buy

    def switch_character(self):
        self.char_idx = (self.char_idx + 1) % len(self.characters)
        hero = self.characters[self.char_idx]
        self.char_text.text = f"HERO: {hero['name']} [V]"
        for part in self.player.children:
            if part.y > 1.6:
                part.color = hero['skin']
            elif part.y > 1.0:
                part.color = hero['shirt']
                for sub in part.children:
                    if sub != self.combat.gun:
                        sub.color = hero['shirt']
            elif part.y > 0.6:
                for sub in part.children:
                    sub.color = hero['pants']

    def select_weapon(self, w_id):
        if not self.unlocked.get(w_id, False):
            self.shops.show_message(f"Locked! Buy at Ammu-Nation", color.red)
            return
        self.weapon_id = w_id
        names = {1: 'Pistol', 2: 'SMG (Rapid)', 3: 'Shotgun', 4: 'RPG Launcher'}
        self.weapon_text.text = f"WEAPON [1-4]: {names[w_id]}"
        scales = {1: (0.08, 0.08, 0.32), 2: (0.09, 0.1, 0.48), 3: (0.11, 0.11, 0.68), 4: (0.16, 0.16, 0.95)}
        cols = {1: color.rgb(45, 45, 50), 2: color.gold, 3: color.brown, 4: color.rgb(55, 85, 45)}
        self.combat.barrel.scale = scales[w_id]
        self.combat.barrel.color = cols[w_id]

    def fire_special(self, in_car):
        target_pt = camera.world_position + camera.forward * 100
        start_pos = self.combat.barrel.world_position + self.combat.barrel.forward * 0.3
        base_dir = (target_pt - start_pos).normalized()

        if self.weapon_id == 3:
            self.sfx.play('shotgun.wav')
            for _ in range(5):
                spread = Vec3(random.uniform(-0.08, 0.08), random.uniform(-0.06, 0.06), random.uniform(-0.08, 0.08))
                b = Entity(model='sphere', position=start_pos, scale=0.13, color=color.orange)
                self.combat.bullets.append({'e': b, 'dir': (base_dir + spread).normalized(), 'life': 0.7})
        elif self.weapon_id == 4:
            self.sfx.play('rpg.wav')
            r = Entity(model='cube', position=start_pos, scale=(0.18, 0.18, 0.55), color=color.red)
            r.look_at(start_pos + base_dir)
            self.rockets.append({'e': r, 'dir': base_dir, 'life': 2.5})
        self.gameplay.add_wanted(1)

    def explode_rocket(self, pos):
        self.sfx.play('boom.wav')
        for _ in range(18):
            p = Entity(model='sphere', position=pos, scale=random.uniform(0.6, 1.8), color=random.choice([color.orange, color.red, color.yellow]))
            self.combat.effects.append({'e': p, 'vel': Vec3(random.uniform(-6, 6), random.uniform(2, 9), random.uniform(-6, 6)), 'life': 0.7})
        for n in self.combat.npcs:
            if n['alive'] and 9.0 > distance(pos, n['root'].position):
                n['alive'] = False
                n['root'].rotation_x = 90
                n['root'].y = 0.25
                n['respawn'] = 12
                self.combat.splash(n['root'].position, 14)

    def input(self, key, in_car):
        if key == 'v':
            self.switch_character()
        elif key in ('1', '2', '3', '4'):
            self.select_weapon(int(key))
        elif key == 'left mouse down' and not in_car:
            if self.weapon_id in (3, 4):
                self.fire_special(in_car)
            elif self.weapon_id == 1:
                self.sfx.play('pistol.wav')

    def update(self, in_car):
        if self.weapon_id == 2 and not in_car and held_keys['left mouse']:
            self.fire_cd -= time.dt
            if 0 > self.fire_cd:
                self.fire_cd = 0.12
                self.sfx.play('smg.wav')
                self.combat.shoot(in_car)
                self.gameplay.add_wanted(1)

        for r in self.rockets[:]:
            r['e'].position += r['dir'] * 55 * time.dt
            r['life'] -= time.dt
            hit = (0.3 > r['e'].y or self.combat.is_inside_building(r['e'].position) or 0 > r['life'])
            for n in self.combat.npcs:
                if n['alive'] and 1.6 > distance(r['e'].position, n['root'].position + Vec3(0, 1, 0)):
                    hit = True
                    break
            if hit:
                self.explode_rocket(r['e'].position)
                destroy(r['e'])
                self.rockets.remove(r)

        if self.gameplay.wanted > 0:
            self.siren_cd -= time.dt
            if 0 > self.siren_cd:
                self.siren_cd = 0.9
                self.sfx.play('siren.wav')
