# -*- coding: utf-8 -*-
"""
Text Fighter - Strategic Combat Edition
Monkey King vs Percy Jackson
Enhanced: Risk/Reward Moves, Defensive Options, Meter Management, Positioning Strategy, AI Personalities
"""

import os
import random
import time
import logging
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect, CSRFError

# ==================== LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== APP INIT ====================

app = Flask(__name__)

# ==================== PRODUCTION DETECTION ====================

IS_PRODUCTION = bool(
    os.environ.get('RENDER') or 
    os.environ.get('RAILWAY_ENVIRONMENT') or 
    os.environ.get('DYNO')
)

# ==================== SECURITY ====================
if IS_PRODUCTION:
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable required!")
    app.config["SECRET_KEY"] = secret_key
else:
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24).hex())

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

if IS_PRODUCTION:
    app.config['SESSION_COOKIE_SECURE'] = True

csrf = CSRFProtect(app)


# ==================== AI PERSONALITY TYPES ====================

class AIPersonality:
    """AI behaviour types for varied gameplay"""
    
    PERSONALITIES = {
        'easy': {
            'name': 'Easy',
            'special_chance': 0.15,
            'super_chance': 0.05,
            'heal_threshold': 0.25,
            'block_chance': 0.1,
            'dodge_chance': 0.05,
            'combo_awareness': False,
            'description': 'Random moves, rarely uses specials'
        },
        'normal': {
            'name': 'Normal',
            'special_chance': 0.3,
            'super_chance': 0.15,
            'heal_threshold': 0.35,
            'block_chance': 0.2,
            'dodge_chance': 0.1,
            'combo_awareness': True,
            'description': 'Strategic, uses healing, supers to finish'
        },
        'hard': {
            'name': 'Hard',
            'special_chance': 0.45,
            'super_chance': 0.3,
            'heal_threshold': 0.45,
            'block_chance': 0.35,
            'dodge_chance': 0.2,
            'combo_awareness': True,
            'counter_chance': 0.15,
            'predict_moves': True,
            'description': 'Predicts patterns, counters, optimal meter usage'
        }
    }
    
    @staticmethod
    def get_random():
        return random.choice(['easy', 'normal', 'hard'])
    
    @staticmethod
    def get_stats(level):
        return AIPersonality.PERSONALITIES.get(level, AIPersonality.PERSONALITIES['normal'])


# ==================== MOVE CATEGORIES (Risk/Reward) ====================

class MoveCategory:
    """Attack categories with risk/reward profiles"""
    
    LIGHT = {
        'name': 'Light',
        'damage_range': (8, 12),
        'accuracy': 0.95,
        'punish_chance': 0.1,
        'meter_gain': 5,
        'button': '1',
        'desc': 'Fast, accurate, hard to punish'
    }
    
    HEAVY = {
        'name': 'Heavy',
        'damage_range': (18, 25),
        'accuracy': 0.75,
        'punish_chance': 0.4,
        'meter_gain': 12,
        'button': '2',
        'desc': 'Slow, powerful, risky if misses'
    }
    
    SPECIAL = {
        'name': 'Special',
        'damage_range': (25, 35),
        'accuracy': 0.85,
        'punish_chance': 0.3,
        'meter_cost': 25,
        'button': '3',
        'desc': 'Uses meter, strong effects'
    }
    
    SUPER = {
        'name': 'Super',
        'damage_range': (40, 55),
        'accuracy': 0.8,
        'punish_chance': 0.5,
        'meter_cost': 100,
        'button': '4',
        'desc': 'Massive damage, very punishable if misses'
    }


# ==================== STATUS EFFECTS ====================

class StatusEffect:
    def __init__(self, name, duration, description, color=""):
        self.name = name
        self.duration = duration
        self.description = description
        self.color = color
        
    def on_hit(self, attacker, defender, damage): return damage
    def on_take_damage(self, fighter, damage): return damage
    def on_action(self, fighter, move): pass
    def on_turn_end(self, fighter): pass
    def __str__(self):
        return u"{}{} ({})".format(self.color, self.name, self.duration)


class Stun(StatusEffect):
    def __init__(self, duration=1):
        super(Stun, self).__init__("Stunned", duration, "Cannot act", "💫")
    def on_action(self, fighter, move): return False


class Burn(StatusEffect):
    def __init__(self, duration=3, damage=4):
        super(Burn, self).__init__("Burning", duration, u"{} dmg/turn".format(damage), "🔥")
        self.damage = damage
    def on_turn_end(self, fighter):
        fighter.take_damage(self.damage)
        fighter.add_log(u"{} {} takes {} burn damage!".format(self.color, fighter.name, self.damage))


class Poison(StatusEffect):
    def __init__(self, duration=4, damage=3):
        super(Poison, self).__init__("Poisoned", duration, u"{} dmg/turn (stacks)".format(damage), "☠️")
        self.damage = damage
        self.stacks = 1
    def on_turn_end(self, fighter):
        total = self.damage * self.stacks
        fighter.take_damage(total)
        fighter.add_log(u"{} {} takes {} poison damage! ({} stacks)".format(self.color, fighter.name, total, self.stacks))
        self.stacks = min(5, self.stacks + 1)


class Empower(StatusEffect):
    def __init__(self, duration=1, bonus=0.5):
        super(Empower, self).__init__("Empowered", duration, u"+{}%".format(int(bonus*100)), "💪")
        self.bonus = bonus
    def on_hit(self, attacker, defender, damage):
        boosted = int(damage * (1 + self.bonus))
        attacker.add_log(u"{} EMPOWERED! +{}% damage!".format(self.color, int(self.bonus*100)))
        return boosted


class Weaken(StatusEffect):
    def __init__(self, duration=1, penalty=0.5):
        super(Weaken, self).__init__("Weakened", duration, u"-{}%".format(int(penalty*100)), "😫")
        self.penalty = penalty
    def on_hit(self, attacker, defender, damage):
        reduced = int(damage * (1 - self.penalty))
        attacker.add_log(u"{} WEAKENED! -{}% damage!".format(self.color, int(self.penalty*100)))
        return reduced


class Armor(StatusEffect):
    def __init__(self, duration=2, reduction=0.3):
        super(Armor, self).__init__("Armor", duration, u"-{}%".format(int(reduction*100)), "🛡️")
        self.reduction = reduction
    def on_take_damage(self, fighter, damage):
        reduced = int(damage * (1 - self.reduction))
        fighter.add_log(u"{} Armor absorbs {} damage!".format(self.color, damage - reduced))
        return reduced


# ==================== COMBO FINISHER ====================

class ComboFinisher:
    @staticmethod
    def check_combo(combo_count, attacker, defender):
        """Apply combo finisher effects based on combo length"""
        if combo_count >= 7:
            if random.random() < 0.4:
                defender.add_status(Stun(1))
                return u"🔥 ULTRA COMBO FINISHER! Enemy STUNNED! 🔥"
            return u"💥 MEGA COMBO! 💥"
        elif combo_count >= 5:
            bonus_damage = int(attacker.power * 8)
            defender.take_damage(bonus_damage)
            return u"✨ COMBO FINISHER! +{} damage! ✨".format(bonus_damage)
        elif combo_count >= 3:
            return u"🔥 COMBO! x{} 🔥".format(combo_count)
        return None


# ==================== RAGE MODE ====================

class RageMode:
    @staticmethod
    def is_active(health, max_health):
        return health < max_health * 0.3
    
    @staticmethod
    def get_damage_bonus(health, max_health):
        if RageMode.is_active(health, max_health):
            return 0.1
        return 0.0
    
    @staticmethod
    def get_meter_gain_bonus(health, max_health):
        if RageMode.is_active(health, max_health):
            return 1.5
        return 1.0


# ==================== CHARACTER PASSIVES ====================

class CharacterPassives:
    @staticmethod
    def apply_monkey_king_passive(fighter, dodge_success):
        if dodge_success:
            fighter.next_attack_guaranteed = True
            fighter.add_log(u"🎭 Trickster's Focus: Next attack will hit!")
    
    @staticmethod
    def apply_percy_passive(fighter, healed):
        if healed:
            fighter.add_status(Armor(duration=2, reduction=0.3))
            fighter.add_log(u"💧 Water's Blessing: Gained armor from healing!")


# ==================== ROUND INTRO MESSAGES ====================

ROUND_INTRO_MESSAGES = [
    u"⚔️ A CLASH OF LEGENDS BEGINS! ⚔️",
    u"🌊 THE WAVES RISE! THE MOUNTAINS SHAKE! 🌊",
    u"💥 ONLY ONE WILL STAND! 💥",
    u"🎭 FIGHT WITH HONOR! 🎭",
    u"⚡ THE BATTLE INTENSIFIES! ⚡",
    u"🔥 WILL YOU RISE OR FALL? 🔥",
    u"💫 LET THE COMBAT BEGIN! 💫",
    u"🏆 GLORY AWAITS THE VICTOR! 🏆"
]

def get_random_intro_message():
    return random.choice(ROUND_INTRO_MESSAGES)


# ==================== SOUND HOOKS ====================

def play_sound(sound_name):
    """Sound hook - placeholder for future audio implementation"""
    pass


# ==================== FIGHTER CLASS ====================

class Fighter:
    def __init__(self, name, health, power, speed, defense, meter_gain, accuracy=0.85, evasion=0.1):
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
        self.log_messages = []
        self.combo_count = 0
        self.next_attack_guaranteed = False
        self.rage_mode_active = False
        
    def add_log(self, message):
        self.log_messages.append(message)
    
    def add_meter(self, amount):
        self.super_meter = min(100, self.super_meter + amount)
    
    def spend_meter(self, amount):
        if self.super_meter >= amount:
            self.super_meter -= amount
            return True
        return False
    
    def take_damage(self, damage):
        self.health -= damage
        self.health = max(0, self.health)
        self.combo_count = 0
        return damage
    
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
    
    def add_status(self, effect):
        for existing in self.status_effects:
            if type(existing) == type(effect):
                existing.duration = max(existing.duration, effect.duration)
                return
        self.status_effects.append(effect)
    
    def is_alive(self):
        return self.health > 0
    
    def apply_status_effects(self):
        effects_to_remove = []
        for effect in self.status_effects:
            effect.on_turn_end(self)
            effect.duration -= 1
            if effect.duration <= 0:
                effects_to_remove.append(effect)
        for effect in effects_to_remove:
            self.status_effects.remove(effect)
    
    def check_rage_mode(self):
        if not self.rage_mode_active and self.health < self.max_health * 0.3:
            self.rage_mode_active = True
            self.add_log(u"🔥 RAGE MODE ACTIVATED! +10% damage, faster meter gain! 🔥")
        elif self.rage_mode_active and self.health >= self.max_health * 0.3:
            self.rage_mode_active = False


class MonkeyKing(Fighter):
    def __init__(self):
        super(MonkeyKing, self).__init__("Monkey King", 90, 1.0, 13, 0.9, 1.1, 0.88, 0.15)
        self.evasion_boost = False
    
    def activate_trickster_advantage(self):
        self.evasion_boost = True
        self.add_log(u"🎭 Trickster's Advantage activates! Next attack +50% damage!")
    
    def clear_trickster_advantage(self):
        self.evasion_boost = False


class PercyJackson(Fighter):
    def __init__(self):
        super(PercyJackson, self).__init__("Percy Jackson", 110, 1.0, 10, 1.0, 0.95, 0.85, 0.12)
        self.water_stacks = 0
    
    def add_water_stack(self):
        self.water_stacks = min(3, self.water_stacks + 1)
        self.add_log(u"💧 Water Empowerment! (Stack {}/3)".format(self.water_stacks))
    
    def consume_water_stacks(self):
        if self.water_stacks > 0:
            bonus = 0.15 * self.water_stacks
            self.water_stacks = 0
            return bonus
        return 0


# ==================== ENHANCED CPU AI ====================

class CPUOpponent:
    def __init__(self, fighter, difficulty='normal'):
        self.fighter = fighter
        self.difficulty = difficulty
        self.stats = AIPersonality.get_stats(difficulty)
        self.last_player_moves = []
    
    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.stats = AIPersonality.get_stats(difficulty)
    
    def predict_player_move(self, player_moves_history):
        if not self.stats.get('predict_moves', False) or len(player_moves_history) < 2:
            return None
        
        if len(player_moves_history) >= 3:
            last_three = player_moves_history[-3:]
            if all(m == last_three[0] for m in last_three):
                return 'block'
        return None
    
    def choose_move(self, moves, opponent, player_moves_history=None):
        available = list(moves.items())
        valid_moves = []
        
        for key, move in available:
            if move.get("effect") == "close_only" and self.fighter.position != "Close":
                continue
            if move.get("cost", 0) > 0:
                if self.fighter.super_meter < move["cost"]:
                    continue
            valid_moves.append((key, move))
        
        if not valid_moves:
            return "B", moves["B"]
        
        predicted = self.predict_player_move(player_moves_history)
        if predicted == 'block' and self.stats.get('counter_chance', 0) > random.random():
            for key, move in valid_moves:
                if move.get("damage", 0) >= 15:
                    return key, move
        
        if self.stats.get('combo_awareness', False) and opponent.combo_count >= 3:
            for key, move in valid_moves:
                if move.get("effect") in ['dodge', 'block']:
                    return key, move
        
        for key, move in valid_moves:
            damage = move.get("damage", 0)
            if damage >= opponent.health:
                return key, move
        
        if random.random() < self.stats['super_chance']:
            for key, move in valid_moves:
                if move["type"] == "super":
                    return key, move
        
        if self.fighter.health < self.fighter.max_health * self.stats['heal_threshold']:
            for key, move in valid_moves:
                if move.get("effect") == "heal":
                    return key, move
        
        if random.random() < self.stats['special_chance']:
            specials = [(k, m) for k, m in valid_moves if m["type"] == "special"]
            if specials:
                return random.choice(specials)
        
        if random.random() < self.stats['block_chance']:
            for key, move in valid_moves:
                if move["type"] == "defense":
                    return key, move
        
        return max(valid_moves, key=lambda x: x[1].get("damage", 0))


# ==================== SESSION MANAGER ====================

class SessionManager:
    @staticmethod
    def get(key, default=None):
        return session.get(key, default)
    
    @staticmethod
    def set(key, value):
        session[key] = value
        session.permanent = True
    
    @staticmethod
    def ensure():
        if 'player_health' not in session:
            session.permanent = True
            SessionManager.set('player_health', 100)
            SessionManager.set('player_max_health', 100)
            SessionManager.set('enemy_health', 100)
            SessionManager.set('enemy_max_health', 100)
            SessionManager.set('player_super_meter', 0)
            SessionManager.set('enemy_super_meter', 0)
            SessionManager.set('turn', 1)
            SessionManager.set('game_over', False)
            SessionManager.set('winner', None)
            SessionManager.set('message', u"⚔️ Battle Started! Choose your action!")
            SessionManager.set('heal_cooldown', 0)
            SessionManager.set('player_position', "Medium")
            SessionManager.set('enemy_position', "Medium")
            SessionManager.set('player_combo', 0)
            SessionManager.set('enemy_combo', 0)
            SessionManager.set('player_water_stacks', 0)
            SessionManager.set('player_evasion_boost', False)
            SessionManager.set('player_character', None)
            SessionManager.set('ai_difficulty', 'normal')
            SessionManager.set('win_streak', 0)
            SessionManager.set('player_rage', False)
            SessionManager.set('enemy_rage', False)
            SessionManager.set('player_status_effects', [])
            SessionManager.set('enemy_status_effects', [])
            SessionManager.set('player_next_attack_guaranteed', False)
            logger.info("New game session initialized")
            return True
        return False


# ==================== GAME FUNCTIONS ====================

def calculate_attack_damage(attack_type, attacker, defender):
    """Calculate damage with risk/reward"""
    
    if attack_type == 'light':
        damage = int(attacker.power * random.randint(8, 12))
        accuracy = 0.95
        punish = 0.1
        meter_gain = 5
    elif attack_type == 'heavy':
        damage = int(attacker.power * random.randint(18, 25))
        accuracy = 0.75
        punish = 0.4
        meter_gain = 12
    elif attack_type == 'special':
        if attacker.super_meter < 25:
            return 0, 0, 0, False
        damage = int(attacker.power * random.randint(25, 35))
        accuracy = 0.85
        punish = 0.3
        meter_gain = 0
        attacker.spend_meter(25)
    elif attack_type == 'super':
        if attacker.super_meter < 100:
            return 0, 0, 0, False
        damage = int(attacker.power * random.randint(40, 55))
        accuracy = 0.8
        punish = 0.5
        meter_gain = 0
        attacker.spend_meter(100)
    else:
        return 0, 0, 0, False
    
    # Positioning effect
    if attacker.position == 'Close':
        damage = int(damage * 1.1)
    elif attacker.position == 'Far' and attack_type in ['light', 'heavy']:
        accuracy -= 0.15
        damage = int(damage * 0.8)
    
    # Rage mode bonus
    if attacker.rage_mode_active:
        damage = int(damage * 1.1)
        meter_gain = int(meter_gain * 1.5)
    
    # Apply empower/weaken
    for effect in attacker.status_effects[:]:
        if isinstance(effect, Empower):
            damage = effect.on_hit(attacker, defender, damage)
            attacker.status_effects.remove(effect)
        elif isinstance(effect, Weaken):
            damage = effect.on_hit(attacker, defender, damage)
            attacker.status_effects.remove(effect)
    
    # Guaranteed hit from passive
    if attacker.next_attack_guaranteed:
        accuracy = 1.0
        attacker.next_attack_guaranteed = False
        attacker.add_log(u"✨ GUARANTEED HIT! ✨")
    
    # Hit chance
    if random.random() > accuracy:
        if random.random() < punish:
            counter_damage = int(defender.power * random.randint(5, 10))
            defender.add_log(u"⚠️ PUNISHMENT! {} missed and takes {} counter damage!".format(attacker.name, counter_damage))
            defender.take_damage(counter_damage)
        return 0, 0, 0, True
    
    # Apply trickster advantage
    if isinstance(attacker, MonkeyKing) and attacker.evasion_boost:
        damage = int(damage * 1.5)
        attacker.add_log(u"🎭 TRICKSTER'S ADVANTAGE! +50% damage!")
        attacker.clear_trickster_advantage()
    
    # Apply water stacks
    if isinstance(attacker, PercyJackson):
        water_bonus = attacker.consume_water_stacks()
        if water_bonus > 0:
            damage = int(damage * (1 + water_bonus))
            attacker.add_log(u"💧 WATER EMPOWERED! +{}% damage!".format(int(water_bonus*100)))
    
    # Apply armor
    for effect in defender.status_effects[:]:
        if isinstance(effect, Armor):
            damage = effect.on_take_damage(defender, damage)
            defender.status_effects.remove(effect)
            break
    
    actual_damage = defender.take_damage(damage)
    
    # Add meter for attacker
    attacker.add_meter(meter_gain)
    
    # Update combo
    if actual_damage > 0:
        attacker.combo_count += 1
        finisher_msg = ComboFinisher.check_combo(attacker.combo_count, attacker, defender)
        if finisher_msg:
            attacker.add_log(finisher_msg)
    else:
        attacker.combo_count = 0
    
    return actual_damage, damage, meter_gain, True


# ==================== ROUTES ====================

@app.route('/')
def index():
    SessionManager.ensure()
    
    if SessionManager.get('player_character') is None:
        return redirect(url_for('select_page'))
    
    player_health = max(0, min(SessionManager.get('player_health', 100), SessionManager.get('player_max_health', 100)))
    enemy_health = max(0, min(SessionManager.get('enemy_health', 100), SessionManager.get('enemy_max_health', 100)))
    
    # Check rage mode
    player_rage = player_health < 30
    enemy_rage = enemy_health < 30
    
    return render_template('index.html',
                           player_name="Monkey King" if SessionManager.get('player_character') == 'monkey' else "Percy Jackson",
                           enemy_name="Percy Jackson" if SessionManager.get('player_character') == 'monkey' else "Monkey King",
                           player_health=player_health,
                           player_max_health=SessionManager.get('player_max_health', 100),
                           enemy_health=enemy_health,
                           enemy_max_health=SessionManager.get('enemy_max_health', 100),
                           player_meter=SessionManager.get('player_super_meter', 0),
                           enemy_meter=SessionManager.get('enemy_super_meter', 0),
                           player_position=SessionManager.get('player_position', "Medium"),
                           enemy_position=SessionManager.get('enemy_position', "Medium"),
                           player_combo=SessionManager.get('player_combo', 0),
                           enemy_combo=SessionManager.get('enemy_combo', 0),
                           player_water=SessionManager.get('player_water_stacks', 0),
                           player_effects=SessionManager.get('player_status_effects', []),
                           enemy_effects=SessionManager.get('enemy_status_effects', []),
                           turn=SessionManager.get('turn', 1),
                           game_over=SessionManager.get('game_over', False),
                           winner=SessionManager.get('winner'),
                           message=SessionManager.get('message', 'Battle started!'),
                           heal_cooldown=SessionManager.get('heal_cooldown', 0),
                           win_streak=SessionManager.get('win_streak', 0),
                           ai_difficulty=SessionManager.get('ai_difficulty', 'normal'),
                           player_rage=player_rage,
                           enemy_rage=enemy_rage)


@app.route('/select')
def select_page():
    SessionManager.ensure()
    return render_template('select.html')


@app.route('/select', methods=['POST'])
def select_character():
    SessionManager.ensure()
    
    character = request.form.get('character', 'monkey')
    difficulty = request.form.get('difficulty', 'normal')
    
    if character not in ['monkey', 'percy']:
        character = 'monkey'
    if difficulty not in ['easy', 'normal', 'hard']:
        difficulty = 'normal'
    
    SessionManager.set('player_character', character)
    SessionManager.set('ai_difficulty', difficulty)
    SessionManager.set('win_streak', 0)
    
    # Reset game state
    SessionManager.set('player_health', 100)
    SessionManager.set('player_max_health', 100)
    SessionManager.set('enemy_health', 100)
    SessionManager.set('enemy_max_health', 100)
    SessionManager.set('player_super_meter', 0)
    SessionManager.set('enemy_super_meter', 0)
    SessionManager.set('turn', 1)
    SessionManager.set('game_over', False)
    SessionManager.set('winner', None)
    SessionManager.set('message', get_random_intro_message())
    SessionManager.set('player_position', "Medium")
    SessionManager.set('enemy_position', "Medium")
    SessionManager.set('player_combo', 0)
    SessionManager.set('enemy_combo', 0)
    SessionManager.set('player_water_stacks', 0)
    
    logger.info("Player selected {} against {} AI".format(character, difficulty))
    
    return redirect(url_for('index'))


@app.route('/controls')
def controls_page():
    return render_template('controls.html')


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/action', methods=['POST'])
def action():
    SessionManager.ensure()
    
    if SessionManager.get('player_character') is None:
        return redirect(url_for('select_page'))
    
    if SessionManager.get('game_over', False):
        return redirect(url_for('index'))
    
    action_type = request.form.get('move', '')
    
    # Create fighter objects
    player = MonkeyKing() if SessionManager.get('player_character') == 'monkey' else PercyJackson()
    enemy = PercyJackson() if SessionManager.get('player_character') == 'monkey' else MonkeyKing()
    
    # Load stats
    player.health = SessionManager.get('player_health', 100)
    player.max_health = SessionManager.get('player_max_health', 100)
    player.super_meter = SessionManager.get('player_super_meter', 0)
    player.position = SessionManager.get('player_position', "Medium")
    player.combo_count = SessionManager.get('player_combo', 0)
    player.water_stacks = SessionManager.get('player_water_stacks', 0)
    player.next_attack_guaranteed = SessionManager.get('player_next_attack_guaranteed', False)
    
    enemy.health = SessionManager.get('enemy_health', 100)
    enemy.max_health = SessionManager.get('enemy_max_health', 100)
    enemy.super_meter = SessionManager.get('enemy_super_meter', 0)
    enemy.position = SessionManager.get('enemy_position', "Medium")
    enemy.combo_count = SessionManager.get('enemy_combo', 0)
    
    # Check rage mode
    player.check_rage_mode()
    enemy.check_rage_mode()
    
    message = ""
    
    # Process action
    if action_type in ['light', 'heavy', 'special', 'super']:
        damage, original, meter, success = calculate_attack_damage(action_type, player, enemy)
        if success:
            if damage > 0:
                message = u"⚔️ {} Attack! {} damage!".format(action_type.capitalize(), damage)
                play_sound("hit")
            else:
                message = u"❌ Attack missed!"
        else:
            message = u"❌ Not enough meter for {}!".format(action_type.capitalize())
    
    elif action_type == 'block':
        # Block reduces next hit by 75%
        SessionManager.set('player_blocking', True)
        message = u"🛡️ Block stance ready! Next hit reduced by 75%"
    
    elif action_type == 'heal':
        heal_cooldown = SessionManager.get('heal_cooldown', 0)
        if heal_cooldown > 0:
            message = u"⚠️ Heal on cooldown! Wait {} turns!".format(heal_cooldown)
        else:
            heal_amount = random.randint(15, 25)
            player.heal(heal_amount)
            message = u"💚 You heal {} HP!".format(heal_amount)
            SessionManager.set('heal_cooldown', 3)
            CharacterPassives.apply_percy_passive(player, True)
            play_sound("heal")
    
    elif action_type == 'step_forward':
        if player.position == 'Far':
            player.position = 'Medium'
            message = u"🏃 Step forward to Medium range!"
        elif player.position == 'Medium':
            player.position = 'Close'
            message = u"🏃 Step forward to Close range!"
        else:
            message = u"❌ Already at Close range!"
    
    elif action_type == 'step_back':
        if player.position == 'Close':
            player.position = 'Medium'
            message = u"🏃 Step back to Medium range!"
        elif player.position == 'Medium':
            player.position = 'Far'
            message = u"🏃 Step back to Far range!"
        else:
            message = u"❌ Already at Far range!"
    
    elif action_type == 'dodge':
        if player.super_meter >= 20:
            player.spend_meter(20)
            if random.random() < 0.7:
                message = u"💨 Dodge successful! Avoided attack!"
                CharacterPassives.apply_monkey_king_passive(player, True)
            else:
                message = u"💨 Dodge failed!"
        else:
            message = u"❌ Not enough meter to dodge!"
    
    # Save player state
    SessionManager.set('player_health', player.health)
    SessionManager.set('player_super_meter', player.super_meter)
    SessionManager.set('player_position', player.position)
    SessionManager.set('player_combo', player.combo_count)
    SessionManager.set('player_water_stacks', player.water_stacks)
    SessionManager.set('player_next_attack_guaranteed', player.next_attack_guaranteed)
    SessionManager.set('message', message)
    
    # Check if enemy died
    if enemy.health <= 0:
        SessionManager.set('game_over', True)
        SessionManager.set('winner', 'player')
        win_streak = SessionManager.get('win_streak', 0) + 1
        SessionManager.set('win_streak', win_streak)
        SessionManager.set('message', u"🏆 VICTORY! Win Streak: {}! 🏆".format(win_streak))
        SessionManager.set('enemy_health', 0)
        play_sound("victory")
        return redirect(url_for('index'))
    
    # Enemy turn
    difficulty = SessionManager.get('ai_difficulty', 'normal')
    cpu = CPUOpponent(enemy, difficulty)
    enemy_moves = {
        "1": {"name": "Attack", "type": "normal", "damage": random.randint(15, 25), "cost": 0},
        "2": {"name": "Heavy Attack", "type": "normal", "damage": random.randint(25, 35), "cost": 0},
        "3": {"name": "Special", "type": "special", "damage": random.randint(30, 45), "cost": 25},
        "4": {"name": "Super", "type": "super", "damage": random.randint(45, 60), "cost": 100},
        "B": {"name": "Block", "type": "defense", "effect": "block", "cost": 0},
        "D": {"name": "Dodge", "type": "defense", "effect": "dodge", "cost": 20}
    }
    
    # Simple enemy AI with personality
    enemy_action = None
    if difficulty == 'easy':
        enemy_action = random.choice(['light', 'heavy', 'block'])
    elif difficulty == 'normal':
        if enemy.health < 30:
            enemy_action = 'heal'
        elif enemy.super_meter >= 100 and random.random() < 0
