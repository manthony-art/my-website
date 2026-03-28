"""
Text Fighter
Two-player text-based fighting game
Monkey King vs Percy Jackson
Enhanced with Status Effects & Water Empowerment
"""

import os
import time
import random


class StatusEffect:
    """Base class for status effects"""
    
    def __init__(self, name, duration, description):
        self.name = name
        self.duration = duration
        self.description = description
        
    def apply(self, fighter):
        """Apply effect at start of turn"""
        pass
        
    def on_hit(self, attacker, defender, damage):
        """Trigger when attacker hits with this effect active"""
        return damage
        
    def on_take_damage(self, fighter, damage):
        """Trigger when fighter takes damage with this effect active"""
        return damage
        
    def on_action(self, fighter, move):
        """Trigger when fighter performs an action"""
        pass
        
    def on_turn_end(self, fighter):
        """Trigger at end of fighter's turn"""
        pass
        
    def __str__(self):
        return f"{self.name} ({self.duration} turns)"


class Stun(StatusEffect):
    def __init__(self, duration=1):
        super().__init__("Stunned", duration, "Cannot act this turn")
        
    def on_action(self, fighter, move):
        return False


class Burn(StatusEffect):
    def __init__(self, duration=3, damage=4):
        super().__init__("Burning", duration, f"Take {damage} damage each turn")
        self.damage = damage
        
    def on_turn_end(self, fighter):
        fighter.take_damage(self.damage)
        print(f"🔥 {fighter.name} takes {self.damage} burn damage!")


class Poison(StatusEffect):
    def __init__(self, duration=4, damage=3):
        super().__init__("Poisoned", duration, f"Take {damage} damage each turn")
        self.damage = damage
        self.stacks = 1
        
    def on_turn_end(self, fighter):
        total_damage = self.damage * self.stacks
        fighter.take_damage(total_damage)
        print(f"☠️ {fighter.name} takes {total_damage} poison damage! ({self.stacks} stacks)")
        self.stacks = min(5, self.stacks + 1)


class Empower(StatusEffect):
    def __init__(self, duration=2, bonus=0.5):
        super().__init__("Empowered", duration, f"+{int(bonus*100)}% damage on next attack")
        self.bonus = bonus
        
    def on_hit(self, attacker, defender, damage):
        boosted = int(damage * (1 + self.bonus))
        print(f"💪 {attacker.name}'s attack is EMPOWERED! +{int(self.bonus*100)}% damage!")
        return boosted


class Weaken(StatusEffect):
    def __init__(self, duration=2, penalty=0.5):
        super().__init__("Weakened", duration, f"-{int(penalty*100)}% damage on next attack")
        self.penalty = penalty
        
    def on_hit(self, attacker, defender, damage):
        reduced = int(damage * (1 - self.penalty))
        print(f"😫 {attacker.name}'s attack is WEAKENED! -{int(self.penalty*100)}% damage!")
        return reduced


class DefenseBreak(StatusEffect):
    def __init__(self, duration=2, reduction=0.5):
        super().__init__("Defense Broken", duration, f"Defense reduced by {int(reduction*100)}%")
        self.reduction = reduction


class Regeneration(StatusEffect):
    def __init__(self, duration=3, heal=5):
        super().__init__("Regeneration", duration, f"Heal {heal} HP each turn")
        self.heal = heal
        
    def on_turn_end(self, fighter):
        fighter.heal(self.heal)
        print(f"💚 {fighter.name} regenerates {self.heal} health!")


class Focus(StatusEffect):
    def __init__(self, duration=3, crit_chance=0.3):
        super().__init__("Focused", duration, f"+{int(crit_chance*100)}% critical hit chance")
        self.crit_chance = crit_chance
        
    def on_hit(self, attacker, defender, damage):
        if random.random() < self.crit_chance:
            crit_damage = int(damage * 1.5)
            print(f"✨ CRITICAL HIT! ✨ {crit_damage} damage!")
            return crit_damage
        return damage


class Armor(StatusEffect):
    def __init__(self, duration=1, reduction=0.5):
        super().__init__("Armor", duration, f"Next hit reduced by {int(reduction*100)}%")
        self.reduction = reduction
        
    def on_take_damage(self, fighter, damage):
        reduced = int(damage * (1 - self.reduction))
        print(f"🛡️ {fighter.name}'s armor absorbs {damage - reduced} damage!")
        return reduced


class Bleeding(StatusEffect):
    def __init__(self, duration=3, damage=5):
        super().__init__("Bleeding", duration, f"Take {damage} damage when acting")
        self.damage = damage
        
    def on_action(self, fighter, move):
        fighter.take_damage(self.damage)
        print(f"🩸 {fighter.name} takes {self.damage} bleed damage from acting!")
        return True


class Frozen(StatusEffect):
    def __init__(self, duration=1):
        super().__init__("Frozen", duration, "Cannot act this turn")
        
    def on_action(self, fighter, move):
        return False


class Confused(StatusEffect):
    def __init__(self, duration=2):
        super().__init__("Confused", duration, "May hit self when attacking")
        
    def on_hit(self, attacker, defender, damage):
        if random.random() < 0.3:
            print(f"🌀 {attacker.name} is confused and hits themself!")
            attacker.take_damage(damage)
            return 0
        return damage


class Fighter:
    """Base class for all fighters"""
    
    def __init__(self, name, health, power, speed, defense, meter_gain):
        self.name = name
        self.max_health = health
        self.health = health
        self.power = power
        self.speed = speed
        self.base_defense = defense
        self.defense = defense
        self.meter_gain = meter_gain
        self.super_meter = 0
        self.position = "Medium"
        self.status_effects = []
        self.stunned = False
        
    def take_damage(self, damage, ignore_defense=False):
        original_damage = damage
        
        if not ignore_defense:
            for effect in self.status_effects:
                if isinstance(effect, DefenseBreak):
                    effective_defense = self.defense * (1 - effect.reduction)
                    damage = int(damage * effective_defense)
                else:
                    damage = int(damage * self.defense)
        
        for effect in self.status_effects[:]:
            if isinstance(effect, Armor):
                damage = effect.on_take_damage(self, damage)
                self.status_effects.remove(effect)
                break
                
        for effect in self.status_effects:
            if hasattr(effect, 'on_take_damage') and not isinstance(effect, Armor):
                damage = effect.on_take_damage(self, damage)
        
        self.health -= damage
        meter_loss = int(original_damage * 0.5)
        self.super_meter = max(0, self.super_meter - meter_loss)
        self.health = max(0, self.health)
        return int(damage)
        
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        
    def add_meter(self, amount):
        self.super_meter = min(100, self.super_meter + amount)
        
    def spend_meter(self, amount):
        if self.super_meter >= amount:
            self.super_meter -= amount
            return True
        return False
        
    def add_status(self, effect):
        for existing in self.status_effects:
            if type(existing) == type(effect):
                existing.duration = max(existing.duration, effect.duration)
                return
        self.status_effects.append(effect)
        
    def reset_round(self):
        self.health = min(self.max_health, self.health + int(self.max_health * 0.3))
        self.position = "Medium"
        self.status_effects = []
        self.defense = self.base_defense
        self.stunned = False
        
    def is_alive(self):
        return self.health > 0
        
    def get_status_text(self):
        meter_bar = "█" * (self.super_meter // 10) + "░" * (10 - self.super_meter // 10)
        status_str = ""
        if self.status_effects:
            effects = [str(e) for e in self.status_effects[:3]]
            status_str = f" | 🌀 {', '.join(effects)}"
        return f"{self.name}: ❤️ {self.health}/{self.max_health}  ⚡ [{meter_bar}] {self.super_meter}%  📍 {self.position}{status_str}"
        
    def apply_status_effects(self):
        effects_to_remove = []
        for effect in self.status_effects:
            effect.on_turn_end(self)
            effect.duration -= 1
            if effect.duration <= 0:
                effects_to_remove.append(effect)
        for effect in effects_to_remove:
            self.status_effects.remove(effect)


class MonkeyKing(Fighter):
    def __init__(self):
        super().__init__(
            name="Monkey King",
            health=90,
            power=1.0,
            speed=13,
            defense=0.9,
            meter_gain=1.1
        )
        self.clone_active = False
        self.evasion_boost = False
        
    def get_moves(self):
        moves = {
            "1": {"name": "Staff Strike", "type": "normal", "damage": 8, "effect": None, "desc": "Quick staff jab"},
            "2": {"name": "Monkey Kick", "type": "normal", "damage": 7, "effect": "advance", "desc": "Leaping kick, closes distance"},
            "3": {"name": "Tail Sweep", "type": "normal", "damage": 6, "effect": "stun", "desc": "Low sweep, 50% stun chance"},
            "4": {"name": "Flurry", "type": "normal", "damage": 5, "effect": "multi_hit", "desc": "Rapid strikes (2 hits)"},
            "5": {"name": "Ruyi Extension", "type": "special", "damage": 10, "cost": 25, "effect": "any_range", "desc": "Staff extends to any range"},
            "6": {"name": "Cloud Somersault", "type": "special", "damage": 0, "cost": 20, "effect": "evade_retreat", "desc": "Evade and retreat"},
            "7": {"name": "分身 (Fēnshēn)", "type": "special", "damage": 6, "cost": 30, "effect": "clone", "desc": "Create clone, empower next attack"},
            "8": {"name": "Golden Gaze", "type": "special", "damage": 0, "cost": 25, "effect": "reveal", "desc": "See opponent's next move"},
            "9": {"name": "Great Sage's Wrath", "type": "super", "damage": 20, "cost": 100, "effect": "unblockable_stun", "desc": "Unblockable! Stuns opponent"},
            "B": {"name": "Block", "type": "defense", "effect": "block", "desc": "Reduce damage by 75%"},
            "D": {"name": "Dodge", "type": "defense", "cost": 20, "effect": "dodge", "desc": "Evade entirely, costs meter"},
            "T": {"name": "Throw", "type": "throw", "damage": 8, "effect": "throw", "desc": "Unblockable at close range"}
        }
        return moves
    
    def activate_trickster_advantage(self):
        self.evasion_boost = True
        print(f"🎭 {self.name}'s Trickster's Advantage activates! Next attack empowered!")
        
    def clear_trickster_advantage(self):
        self.evasion_boost = False


class PercyJackson(Fighter):
    def __init__(self):
        super().__init__(
            name="Percy Jackson",
            health=110,
            power=1.0,
            speed=10,
            defense=1.0,
            meter_gain=0.95
        )
        self.water_stacks = 0
        self.heal_cooldown = False
        
    def get_moves(self):
        moves = {
            "1": {"name": "Riptide Slash", "type": "normal", "damage": 8, "effect": None, "desc": "Standard sword strike"},
            "2": {"name": "Spartan Kick", "type": "normal", "damage": 7, "effect": "knockback", "desc": "Kicks opponent back"},
            "3": {"name": "Hilt Strike", "type": "normal", "damage": 5, "effect": "stun", "desc": "Strike with hilt, 50% stun"},
            "4": {"name": "Combo Strikes", "type": "normal", "damage": 6, "effect": "advance", "desc": "Two slashes, closes distance"},
            "5": {"name": "Tidal Wave", "type": "special", "damage": 9, "cost": 25, "effect": "water_push", "desc": "Water wave pushes opponent"},
            "6": {"name": "Water Healing", "type": "special", "damage": 0, "cost": 30, "effect": "heal", "desc": "Heal 12 HP"},
            "7": {"name": "Hydro Armor", "type": "special", "damage": 0, "cost": 20, "effect": "armor", "desc": "Reduce next hit by 50%"},
            "8": {"name": "Riptide Throw", "type": "special", "damage": 7, "cost": 20, "effect": "close_only", "desc": "Grapple at close range"},
            "9": {"name": "Poseidon's Wrath", "type": "super", "damage": 18, "cost": 100, "effect": "earthquake", "desc": "Earthquake! Stuns opponent"},
            "B": {"name": "Block", "type": "defense", "effect": "block", "desc": "Reduce damage by 75%"},
            "D": {"name": "Dodge", "type": "defense", "cost": 20, "effect": "dodge", "desc": "Evade entirely, costs meter"},
            "T": {"name": "Throw", "type": "throw", "damage": 7, "effect": "throw", "desc": "Unblockable at close range"}
        }
        return moves
    
    def add_water_stack(self):
        self.water_stacks = min(3, self.water_stacks + 1)
        print(f"💧 {self.name} gains Water Empowerment! (Stack {self.water_stacks}/3)")
        
    def consume_water_stacks(self):
        if self.water_stacks > 0:
            bonus = 0.15 * self.water_stacks
            self.water_stacks = 0
            return bonus
        return 0
        
    def get_water_status(self):
        if self.water_stacks > 0:
            return f" 💧{self.water_stacks}"
        return ""
        
    def get_status_text(self):
        base_text = super().get_status_text()
        return base_text + self.get_water_status()


class Combat:
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_game_background(self):
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                         ☁️☁️      ☁️☁️                           ║
║                    ☁️☁️                  ☁️☁️                     ║
║                                                                ║
║        🌲                    ╭─────────╮              🌲        ║
║       🌲🌲                  │  🪜🪜🪜  │            🌲🌲         ║
║      🌲  🌲                 │   🚪    │           🌲  🌲        ║
║     🌲    🌲                │  🪜🪜🪜  │          🌲    🌲       ║
║    🌲      🌲               ╰─────────╯         🌲      🌲      ║
║   🌲        🌲               🌳🌳🌳🌳            🌲        🌲     ║
║  🌲          🌲            🌳     🌳           🌲          🌲    ║
║ 🌲            🌲          🌳       🌳         🌲            🌲   ║
║🌲              🌲        🌳         🌳       🌲              🌲  ║
║ ╲______________╱       🌳           🌳      ╲______________╱   ║
║                                                                ║
║      ~~~~~~~~~~~~🌊~~~~~~~~~~~~🌊~~~~~~~~~~~~🌊~~~~~~~~~~      ║
║                                                                ║
║    🌿🌿          🌿🌿                      🌿🌿        🌿🌿      ║
║   🌿   🌿      🌿   🌿                  🌿   🌿    🌿   🌿      ║
║  🌿     🌿    🌿     🌿                🌿     🌿  🌿     🌿     ║
║                                                                ║
║              🕊️          🕊️          🕊️                       ║
║                                                                ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    def display_controls(self):
        """Display controls menu for both players"""
        self.clear_screen()
        print("""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                              🎮 CONTROLS MENU 🎮                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ╔══════════════════════════════╗    ╔══════════════════════════════╗           ║
║  ║     🐒 MONKEY KING 🐒        ║    ║      🌊 PERCY JACKSON 🌊     ║           ║
║  ╠══════════════════════════════╣    ╠══════════════════════════════╣           ║
║  ║ NORMALS:                     ║    ║ NORMALS:                     ║           ║
║  ║  [1] Staff Strike (8 dmg)   ║    ║  [1] Riptide Slash (8 dmg)   ║           ║
║  ║  [2] Monkey Kick (7 dmg)    ║    ║  [2] Spartan Kick (7 dmg)    ║           ║
║  ║  [3] Tail Sweep (6 dmg)     ║    ║  [3] Hilt Strike (5 dmg)     ║           ║
║  ║  [4] Flurry (5 dmg x2)      ║    ║  [4] Combo Strikes (6 dmg)   ║           ║
║  ╠══════════════════════════════╣    ╠══════════════════════════════╣           ║
║  ║ SPECIALS (Cost):             ║    ║ SPECIALS (Cost):             ║           ║
║  ║  [5] Ruyi Extension (25%)    ║    ║  [5] Tidal Wave (25%)        ║           ║
║  ║  [6] Cloud Somersault (20%)  ║    ║  [6] Water Healing (30%)     ║           ║
║  ║  [7] 分身 Clone (30%)        ║    ║  [7] Hydro Armor (20%)       ║           ║
║  ║  [8] Golden Gaze (25%)       ║    ║  [8] Riptide Throw (20%)     ║           ║
║  ╠══════════════════════════════╣    ╠══════════════════════════════╣           ║
║  ║ SUPER:                       ║    ║ SUPER:                       ║           ║
║  ║  [9] Great Sage's Wrath      ║    ║  [9] Poseidon's Wrath        ║           ║
║  ║      (100% - Unblockable)    ║    ║      (100% - Stun)           ║           ║
║  ╠══════════════════════════════╣    ╠══════════════════════════════╣           ║
║  ║ DEFENSE:                     ║    ║ DEFENSE:                     ║           ║
║  ║  [B] Block (75% reduction)   ║    ║  [B] Block (75% reduction)   ║           ║
║  ║  [D] Dodge (20% - 70% evade) ║    ║  [D] Dodge (20% - 70% evade) ║           ║
║  ╠══════════════════════════════╣    ╠══════════════════════════════╣           ║
║  ║ THROW:                       ║    ║ THROW:                       ║           ║
║  ║  [T] Throw (8 dmg)           ║    ║  [T] Throw (7 dmg)           ║           ║
║  ║      (Close range only)      ║    ║      (Close range only)      ║           ║
║  ╚══════════════════════════════╝    ╚══════════════════════════════╝           ║
║                                                                                  ║
║  ╔══════════════════════════════════════════════════════════════════════════╗   ║
║  ║ ⚔️  COMBAT MECHANICS:                                                    ║   ║
║  ║ • Super meter builds by dealing/taking damage (max 100%)                 ║   ║
║  ║ • Special moves cost meter, Super moves cost 100%                        ║   ║
║  ║ • Position affects moves: Close | Medium | Far                           ║   ║
║  ║ • Status effects: Stun, Burn, Poison, Empower, Weaken, and more!        ║   ║
║  ║ • Monkey King: Trickster's Advantage (+50% damage after evading)        ║   ║
║  ║ • Percy Jackson: Water Empowerment (up to 3 stacks, +15% each)          ║   ║
║  ╚══════════════════════════════════════════════════════════════════════════╝   ║
║                                                                                  ║
║                              Press ENTER to return                               ║
╚══════════════════════════════════════════════════════════════════════════════════╝
        """)
        input()
        
    def display_status(self):
        self.display_game_background()
        print("\n" + "="*70)
        print(f"⚔️  ROUND {self.round}  |  Best of 3  ⚔️")
        print("="*70)
        print(self.p1.get_status_text())
        print(self.p2.get_status_text())
        print("-"*70)
        
    def display_move_menu(self, fighter, moves):
        if isinstance(fighter, PercyJackson) and fighter.water_stacks > 0:
            print(f"\n💧 WATER EMPOWERMENT: +{int(fighter.water_stacks * 15)}% damage on next attack! 💧")
        
        print(f"\n🎮 {fighter.name}'s Turn - Choose your move:")
        print("-"*50)
        print("  [C] Show Controls")
        print("-"*50)
        
        print("\n⚡ NORMALS:")
        for key, move in moves.items():
            if move["type"] == "normal":
                print(f"  [{key}] {move['name']:<18} DMG: {move['damage']:<3} | {move['desc']}")
                
        print("\n🌀 SPECIALS:")
        for key, move in moves.items():
            if move["type"] == "special":
                cost = move.get("cost", 0)
                print(f"  [{key}] {move['name']:<18} DMG: {move['damage']:<3} Cost: {cost}% | {move['desc']}")
                
        print("\n💥 SUPER:")
        for key, move in moves.items():
            if move["type"] == "super":
                cost = move.get("cost", 0)
                print(f"  [{key}] {move['name']:<18} DMG: {move['damage']:<3} Cost: {cost}% | {move['desc']}")
                
        print("\n🛡️ DEFENSE:")
        for key, move in moves.items():
            if move["type"] == "defense":
                cost = move.get("cost", 0)
                if cost > 0:
                    print(f"  [{key}] {move['name']:<18} Cost: {cost}% | {move['desc']}")
                else:
                    print(f"  [{key}] {move['name']:<18} {move['desc']}")
                    
        print("\n🤼 THROW:")
        for key, move in moves.items():
            if move["type"] == "throw":
                print(f"  [{key}] {move['name']:<18} DMG: {move['damage']:<3} | {move['desc']}")
                
        print("-"*50)
        
    def get_player_action(self, fighter, moves):
        for effect in fighter.status_effects:
            if isinstance(effect, (Stun, Frozen)):
                print(f"\n😵 {fighter.name} is STUNNED and cannot act this turn!")
                time.sleep(1.5)
                return None, None
                
        while True:
            choice = input(f"\n{fighter.name}, enter your choice: ").upper()
            
            if choice == "C":
                self.display_controls()
                self.display_status()
                self.display_move_menu(fighter, moves)
                continue
            
            if choice in moves:
                move = moves[choice]
                
                if "cost" in move and move["cost"] > 0:
                    if fighter.super_meter < move["cost"]:
                        print(f"❌ Not enough super meter! Need {move['cost']}%, have {fighter.super_meter}%")
                        continue
                        
                if move.get("effect") == "close_only" and fighter.position != "Close":
                    print(f"❌ {move['name']} can only be used at Close range! Current range: {fighter.position}")
                    continue
                    
                return move, choice
            else:
                print("❌ Invalid choice. Select from the menu or press C for controls.")
                
    def resolve_action(self, attacker, defender, move, move_choice):
        result_text = ""
        
        for effect in attacker.status_effects:
            if isinstance(effect, (Stun, Frozen)):
                return f"😵 {attacker.name} is stunned and cannot act!", 0, None
                
        if move["type"] == "defense":
            if move["effect"] == "block":
                result_text = f"🛡️ {attacker.name} raises their guard. (Block ready - 75% damage reduction)"
                return result_text, 0, "block"
            elif move["effect"] == "dodge":
                if "cost" in move:
                    attacker.spend_meter(move["cost"])
                result_text = f"💨 {attacker.name} prepares to dodge!"
                return result_text, 0, "dodge"
                
        elif move["type"] == "throw":
            if attacker.position == "Close":
                damage = int(move["damage"] * attacker.power)
                
                for effect in attacker.status_effects[:]:
                    if isinstance(effect, Empower):
                        damage = effect.on_hit(attacker, defender, damage)
                        attacker.status_effects.remove(effect)
                    elif isinstance(effect, Weaken):
                        damage = effect.on_hit(attacker, defender, damage)
                        attacker.status_effects.remove(effect)
                        
                if isinstance(attacker, PercyJackson):
                    water_bonus = attacker.consume_water_stacks()
                    if water_bonus > 0:
                        damage = int(damage * (1 + water_bonus))
                        result_text += f"💧 WATER EMPOWERED! +{int(water_bonus*100)}% damage! "
                        
                for effect in attacker.status_effects:
                    if isinstance(effect, Confused):
                        damage = effect.on_hit(attacker, defender, damage)
                        
                actual_damage = defender.take_damage(damage, ignore_defense=True)
                attacker.add_meter(attacker.meter_gain * 10)
                result_text += f"🤼 {attacker.name} grabs and throws {defender.name}! {defender.name} takes {actual_damage} damage!"
                return result_text, actual_damage, None
            else:
                result_text = f"❌ {attacker.name} attempts a throw but is too far away!"
                return result_text, 0, None
                
        else:
            damage = int(move["damage"] * attacker.power)
            
            for effect in attacker.status_effects[:]:
                if isinstance(effect, Empower):
                    damage = effect.on_hit(attacker, defender, damage)
                    attacker.status_effects.remove(effect)
                elif isinstance(effect, Weaken):
                    damage = effect.on_hit(attacker, defender, damage)
                    attacker.status_effects.remove(effect)
                    
            if isinstance(attacker, MonkeyKing) and attacker.evasion_boost:
                damage = int(damage * 1.5)
                result_text += f"🎭 TRICKSTER'S ADVANTAGE! +50% damage! "
                attacker.clear_trickster_advantage()
                
            if isinstance(attacker, PercyJackson):
                water_bonus = attacker.consume_water_stacks()
                if water_bonus > 0:
                    damage = int(damage * (1 + water_bonus))
                    result_text += f"💧 WATER EMPOWERED! +{int(water_bonus*100)}% damage! "
                    
            if "cost" in move:
                attacker.spend_meter(move["cost"])
                
            for effect in attacker.status_effects[:]:
                if isinstance(effect, Confused):
                    damage = effect.on_hit(attacker, defender, damage)
                    
            actual_damage = defender.take_damage(damage)
            
            meter_gain = attacker.meter_gain * 10
            if move.get("effect") == "multi_hit":
                meter_gain += attacker.meter_gain * 5
            attacker.add_meter(meter_gain)
            
            result_text += f"⚔️ {attacker.name} uses {move['name']}! {defender.name} takes {actual_damage} damage!"
            
            if move.get("effect") == "advance":
                if attacker.position != "Close":
                    attacker.position = "Close"
                    result_text += f" {attacker.name} advances to Close range!"
                    
            elif move.get("effect") == "knockback":
                defender.position = "Far"
                result_text += f" {defender.name} is knocked back to Far range!"
                
            elif move.get("effect") == "water_push":
                defender.position = "Far"
                result_text += f" 🌊 {defender.name} is swept back to Far range!"
                if isinstance(attacker, PercyJackson):
                    attacker.add_water_stack()
                    
            elif move.get("effect") == "stun":
                if random.random() < 0.5:
                    defender.add_status(Stun())
                    result_text += f" {defender.name} is STUNNED!"
                    
            elif move.get("effect") == "multi_hit":
                result_text += f" (2 hits!)"
                
            elif move.get("effect") == "heal":
                heal_amount = 12
                attacker.heal(heal_amount)
                result_text += f" 💚 {attacker.name} heals {heal_amount} HP!"
                if isinstance(attacker, PercyJackson):
                    attacker.add_water_stack()
                    
            elif move.get("effect") == "armor":
                attacker.add_status(Armor(duration=1, reduction=0.5))
                result_text += f" 🛡️ {attacker.name} is protected by Hydro Armor!"
                if isinstance(attacker, PercyJackson):
                    attacker.add_water_stack()
                    
            elif move.get("effect") == "unblockable_stun":
                result_text += f" ⚡ UNBLOCKABLE! ⚡ {defender.name} is STUNNED!"
                defender.add_status(Stun())
                
            elif move.get("effect") == "earthquake":
                result_text += f" 🌍 The ground shakes violently! {defender.name} is STUNNED!"
                defender.add_status(Stun())
                if isinstance(attacker, PercyJackson):
                    attacker.add_water_stack()
                    attacker.add_water_stack()
                    
            elif move.get("effect") == "clone":
                attacker.clone_active = True
                attacker.add_status(Empower(duration=1, bonus=0.5))
                result_text += f" 🌀 A clone of {attacker.name} appears! Next attack empowered!"
                
            elif move.get("effect") == "