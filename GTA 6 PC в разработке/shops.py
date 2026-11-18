from ursina import *
import random
import math

class ShopSystem:
    def __init__(self, car, player, gameplay, combat, repair_fn):
        self.car = car
        self.player = player
        self.gameplay = gameplay
        self.combat = combat
        self.repair_fn = repair_fn

        self.has_turbo = False
        self.has_rapid_fire = False
        self.fire_cooldown = 0
        self.msg_timer = 0

        # Сообщение по центру экрана при покупке или нехватке денег
        self.shop_msg = Text(text='', origin=(0, 0), position=(0, 0.25), scale=1.5, color=color.gold, background=True, enabled=False)

        # 3 точки магазинов на карте (координаты, цена, цвет, название)
        self.shops = [
            {'name': "Pay 'n' Spray (Repair + Clear Wanted)", 'cost': 200, 'pos': Vec3(35, 0.2, 35), 'col': color.cyan, 'type': 'spray'},
            {'name': 'Ammu-Nation (Rapid-Fire Gun)', 'cost': 400, 'pos': Vec3(-45, 0.2, 35), 'col': color.red, 'type': 'gun'},
            {'name': 'Desert Turbo (Speed + Nitro [Shift])', 'cost': 600, 'pos': Vec3(520, 0.2, 18), 'col': color.magenta, 'type': 'turbo'}
        ]

        for s in self.shops:
            # Светящийся круг-зона на асфальте/песке
            Entity(model='cube', position=s['pos'], scale=(7, 0.25, 7), texture='white_cube', color=s['col'], unlit=True)
            # Невысокий столб-ориентир, чтобы легко найти магазин
            Entity(model='cube', position=s['pos'] + Vec3(0, 12, 0), scale=(0.6, 24, 0.6), texture='white_cube', color=color.rgba(s['col'].r * 255, s['col'].g * 255, s['col'].b * 255, 110), unlit=True)

    def show_message(self, text, col=color.gold):
        self.shop_msg.text = text
        self.shop_msg.color = col
        self.shop_msg.enabled = True
        self.msg_timer = 2.8

    def try_buy(self, shop):
        if shop['cost'] > self.gameplay.money:
            self.show_message(f"Not enough cash! Need ${shop['cost']}", color.red)
            return

        if shop['type'] == 'spray':
            self.gameplay.money -= shop['cost']
            self.gameplay.money_text.text = f"${self.gameplay.money}"
            self.repair_fn()
            self.gameplay.clear_wanted()
            # Перекрашиваем машину в новый стильный цвет
            new_col = random.choice([color.gold, color.cyan, color.magenta, color.lime, color.orange, color.white])
            self.car.color = new_col
            for child in self.car.children:
                if child.y > 0.5:  # Крыша
                    child.color = new_col
            self.show_message("PAY 'N' SPRAY: Repaired & Wanted Cleared!", color.cyan)

        elif shop['type'] == 'gun':
            if self.has_rapid_fire:
                self.show_message("You already own the Rapid-Fire Gun!", color.yellow)
                return
            self.gameplay.money -= shop['cost']
            self.gameplay.money_text.text = f"${self.gameplay.money}"
            self.has_rapid_fire = True
            # Удлиняем ствол пистолета до автомата
            self.combat.barrel.scale_z = 0.55
            self.combat.barrel.color = color.gold
            self.show_message("AMMU-NATION: Rapid-Fire Unlocked! (Hold LMB)", color.lime)

        elif shop['type'] == 'turbo':
            if self.has_turbo:
                self.show_message("Turbo Engine already installed!", color.yellow)
                return
            self.gameplay.money -= shop['cost']
            self.gameplay.money_text.text = f"${self.gameplay.money}"
            self.has_turbo = True
            self.show_message("TURBO INSTALLED: Max Speed Up + Hold [Shift] for Nitro!", color.magenta)

    def update(self, in_car, speed):
        target = self.car if in_car else self.player

        if self.msg_timer > 0:
            self.msg_timer -= time.dt
            if 0 > self.msg_timer:
                self.shop_msg.enabled = False

        # Автоматическая стрельба очередью при зажатии ЛКМ, если куплен апгрейд в Ammu-Nation
        if self.has_rapid_fire and not in_car and held_keys['left mouse']:
            self.fire_cooldown -= time.dt
            if 0 > self.fire_cooldown:
                self.fire_cooldown = 0.11
                self.combat.shoot(in_car)
                self.gameplay.add_wanted(1)

        # Нитро-ускорение на Shift в машине, если куплен Турбо-гараж в пустыне
        if self.has_turbo and in_car and held_keys['shift'] and held_keys['w']:
            self.car.position += self.car.forward * 22 * time.dt
            # Синее пламя нитро сзади бампера
            flame = Entity(model='sphere', position=self.car.position - self.car.forward * 1.9 + Vec3(0, -0.2, 0), scale=0.35, texture='white_cube', color=color.cyan, unlit=True)
            destroy(flame, delay=0.08)

        # Проверка заезда/захода в любой из 3 магазинов
        for s in self.shops:
            dist = math.sqrt((target.x - s['pos'].x) ** 2 + (target.z - s['pos'].z) ** 2)
            if 4.2 > dist:
                self.shop_msg.text = f"{s['name']} - ${s['cost']} [Press E]"
                self.shop_msg.color = s['col']
                self.shop_msg.enabled = True
                self.msg_timer = 0.2
                if held_keys['e']:
                    self.try_buy(s)
