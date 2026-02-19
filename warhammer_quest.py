#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║     WARHAMMER QUEST: DEPTHS OF THE OLD WORLD                 ║
║     A Terminal Dungeon Crawler                                ║
║     Set in the Warhammer Fantasy Universe                     ║
╚═══════════════════════════════════════════════════════════════╝

Inspired by: Warhammer Quest, Diablo, HeroQuest, Warhammer Quest Card Game

Run with:  python3 warhammer_quest.py
"""

import os, sys, json, random, time, math, shutil
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "wq_save.json"
VERSION = "1.1"

# ═══════════════════════════════════════════════════════════════
#  ANSI COLORS & DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════

class C:
    RST = "\033[0m"; B = "\033[1m"; DIM = "\033[2m"; IT = "\033[3m"
    RED = "\033[31m"; GRN = "\033[32m"; YEL = "\033[33m"; BLU = "\033[34m"
    MAG = "\033[35m"; CYN = "\033[36m"; WHT = "\033[37m"; GRY = "\033[90m"
    BRED = "\033[91m"; BGRN = "\033[92m"; BYEL = "\033[93m"; BBLU = "\033[94m"
    BMAG = "\033[95m"; BCYN = "\033[96m"; BWHT = "\033[97m"

RC = {"Common": C.WHT, "Uncommon": C.GRN, "Rare": C.BBLU, "Epic": C.BMAG, "Legendary": C.BYEL}
RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
RARITY_MULT = {"Common": 1.0, "Uncommon": 1.3, "Rare": 1.6, "Epic": 2.0, "Legendary": 2.5}

W = lambda: min(max(shutil.get_terminal_size().columns, 60), 70)

def clr():
    os.system('clear' if os.name != 'nt' else 'cls')

def co(t, c):
    return f"{c}{t}{C.RST}"

def bo(t):
    return f"{C.B}{t}{C.RST}"

def hdr(text, c=C.BYEL):
    w = W()
    print(co("═" * w, c))
    print(co(text.center(w), c))
    print(co("═" * w, c))

def sep(ch="─", c=C.GRY):
    print(co(ch * W(), c))

def hp_bar(cur, mx, ln=20):
    r = max(0, min(1, cur / mx)) if mx > 0 else 0
    f = int(r * ln)
    bar = "█" * f + "░" * (ln - f)
    c = C.GRN if r > 0.6 else (C.YEL if r > 0.3 else C.RED)
    return f"{c}{bar}{C.RST} {cur}/{mx}"

def mp_bar(cur, mx, ln=20):
    f = int(max(0, min(1, cur / mx)) * ln) if mx > 0 else 0
    bar = "█" * f + "░" * (ln - f)
    return f"{C.BLU}{bar}{C.RST} {cur}/{mx}"

def xp_bar(cur, mx, ln=20):
    f = int(max(0, min(1, cur / mx)) * ln) if mx > 0 else 0
    bar = "█" * f + "░" * (ln - f)
    return f"{C.CYN}{bar}{C.RST} {cur}/{mx}"

def slow_print(text, d=0.018):
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(d)
    print()

def get_choice(options, prompt=""):
    for i, o in enumerate(options, 1):
        print(f"  {co(str(i), C.BYEL)}) {o}")
    while True:
        try:
            r = input(f"\n{co('>', C.BYEL)} ").strip()
            if r.isdigit() and 1 <= int(r) <= len(options):
                return int(r) - 1
            print(co("  Invalid. Try again.", C.RED))
        except (EOFError, KeyboardInterrupt):
            return len(options) - 1

def get_input(prompt=""):
    try:
        return input(f"{co('>', C.BYEL)} {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        return ""

def pause(m="Press Enter to continue..."):
    try:
        input(f"\n{co(m, C.GRY)}")
    except (EOFError, KeyboardInterrupt):
        pass

def wrap(text, c=C.RST, w=None):
    if w is None:
        w = W() - 4
    import textwrap
    for line in textwrap.wrap(text, w):
        print(f"  {c}{line}{C.RST}")

# ═══════════════════════════════════════════════════════════════
#  GAME DATA
# ═══════════════════════════════════════════════════════════════

TITLES = [
    (1, "Novice Adventurer"), (5, "Dungeon Delver"), (10, "Veteran Explorer"),
    (15, "Champion of Ubersreik"), (20, "Hero of the Reikland"),
    (30, "Slayer of Nightmares"), (40, "Bane of Chaos"),
    (50, "Legend of the Old World"), (75, "Chosen of Sigmar"),
    (100, "Immortal of the Ages"),
]

def get_title(depth):
    t = TITLES[0][1]
    for d, name in TITLES:
        if depth >= d:
            t = name
    return t


def get_depth_mood(depth):
    mood = DUNGEON_DEPTH_MOODS[0][1]
    for threshold, text in DUNGEON_DEPTH_MOODS:
        if depth >= threshold:
            mood = text
    return mood


def pick_lore_entry(player, depth):
    undiscovered = [l for l in LORE if l[0] not in player.lore_found]
    if not undiscovered:
        return None

    def weight(entry):
        title = entry[0].lower()
        body = entry[1].lower()
        txt = f"{title} {body}"
        w = 1
        if depth <= 10 and any(k in txt for k in ("skaven", "dwarf", "empire", "ulric", "reik")):
            w += 2
        if depth >= 15 and any(k in txt for k in ("chaos", "daemon", "warp", "morrslieb", "necromancer", "nagash")):
            w += 2
        if depth >= 20 and any(k in txt for k in ("tzeentch", "horned rat", "undead", "beastmen")):
            w += 1
        return w

    weights = [weight(entry) for entry in undiscovered]
    return random.choices(undiscovered, weights=weights, k=1)[0]

# ── CLASSES ──────────────────────────────────────────────────

CLASSES = {
    "Empire Soldier": {
        "desc": "A hardened veteran of the Empire's armies. Well-balanced in offense\nand defense, strengthened by faith in Sigmar.",
        "stats": {"str": 8, "tou": 7, "agi": 5, "int": 3, "wil": 5},
        "hp": 120, "mp": 50,
        "skills": [
            {"name": "Shield Bash", "cost": 15, "desc": "Slam shield into foe. May stun.",
             "type": "damage", "mult": 1.5, "stun": 0.35},
            {"name": "Rally Cry", "cost": 20, "desc": "Battle cry that heals wounds and steels resolve.",
             "type": "heal", "pct": 0.25, "buff": ("Rallied", 3, 0.15)},
            {"name": "Sigmar's Fury", "cost": 30, "desc": "Channel Sigmar's divine wrath.",
             "type": "damage", "mult": 2.8},
        ],
    },
    "Dwarf Ironbreaker": {
        "desc": "An unyielding Dwarf clad in ancient Gromril armour. The toughest\nwarrior, with an ancestral grudge against all evil.",
        "stats": {"str": 7, "tou": 10, "agi": 3, "int": 2, "wil": 6},
        "hp": 150, "mp": 40,
        "skills": [
            {"name": "Grudge Strike", "cost": 15, "desc": "Hit harder the more wounded you are.",
             "type": "grudge", "base_mult": 1.2},
            {"name": "Iron Resolve", "cost": 20, "desc": "Brace behind Gromril shield, reducing damage.",
             "type": "buff_self", "buff": ("Iron Resolve", 3, 0.5)},
            {"name": "Ancestor's Wrath", "cost": 30, "desc": "Call upon ancestor spirits.",
             "type": "damage", "mult": 3.0},
        ],
    },
    "Elf Waywatcher": {
        "desc": "A swift and deadly Elven ranger from Athel Loren. Strikes with\nlightning precision and moves like the wind.",
        "stats": {"str": 5, "tou": 4, "agi": 10, "int": 5, "wil": 4},
        "hp": 90, "mp": 60,
        "skills": [
            {"name": "Aimed Shot", "cost": 15, "desc": "Carefully aimed shot. Always crits.",
             "type": "damage", "mult": 1.3, "auto_crit": True},
            {"name": "Shadowstep", "cost": 20, "desc": "Vanish and strike from shadows. Dodge next hit.",
             "type": "dodge_strike", "mult": 1.4},
            {"name": "Arrow Storm", "cost": 30, "desc": "Unleash a flurry of arrows.",
             "type": "multi", "hits": 3, "mult": 0.8},
        ],
    },
    "Bright Wizard": {
        "desc": "A master of Aqshy, the Wind of Fire. Channels devastating magical\npower, but is fragile in melee.",
        "stats": {"str": 3, "tou": 4, "agi": 5, "int": 10, "wil": 6},
        "hp": 80, "mp": 80,
        "skills": [
            {"name": "Fireball", "cost": 15, "desc": "Hurl a ball of Aqshy fire.",
             "type": "magic", "mult": 1.8},
            {"name": "Flame Shield", "cost": 20, "desc": "Surround yourself with protective flames.",
             "type": "buff_self", "buff": ("Flame Shield", 3, 0.4), "reflect": 8},
            {"name": "Conflagration", "cost": 30, "desc": "Massive inferno of magical fire.",
             "type": "magic", "mult": 3.5},
        ],
    },
}

# ── TALENTS ──────────────────────────────────────────────────

TALENTS = {
    "Empire Soldier": [
        ("Veteran's Resilience", "+{v} Max HP", [12, 25, 40], "hp"),
        ("Shield Mastery", "+{v}% Block Chance", [6, 13, 21], "block"),
        ("Battle Hardened", "+{v} Defense", [3, 7, 12], "defense"),
        ("Fury of Sigmar", "+{v}% Skill 1 Damage", [20, 45, 75], "sk1"),
        ("Inspiring Presence", "+{v}% Skill 2 Healing", [25, 50, 80], "sk2"),
        ("Righteous Smite", "+{v}% Crit Chance", [5, 11, 18], "crit"),
    ],
    "Dwarf Ironbreaker": [
        ("Gromril Toughness", "+{v} Max HP", [15, 35, 55], "hp"),
        ("Ancestral Grudge", "+{v}% Skill 1 Damage", [20, 45, 75], "sk1"),
        ("Stone Wall", "+{v} Defense", [4, 9, 15], "defense"),
        ("Runic Fortitude", "Iron Resolve +{v} Turns", [1, 2, 4], "sk2_turns"),
        ("Grudge Keeper", "+{v}% Dmg per 10% HP Lost", [3, 7, 12], "grudge_pct"),
        ("Dwarfen Resilience", "+{v}% Status Resist", [12, 25, 40], "resist"),
    ],
    "Elf Waywatcher": [
        ("Eagle Eye", "+{v}% Crit Chance", [6, 14, 22], "crit"),
        ("Fleet of Foot", "+{v}% Dodge Chance", [6, 13, 21], "dodge"),
        ("Lethal Precision", "+{v}% Skill 1 Damage", [20, 45, 75], "sk1"),
        ("Shadow Dance", "Shadowstep heals {v}% HP", [6, 13, 22], "sk2_heal"),
        ("Kurnous' Blessing", "+{v} Arrow Storm Hits", [1, 1, 2], "sk3_hits"),
        ("Nature's Grace", "Regen {v} HP/turn", [3, 7, 12], "regen"),
    ],
    "Bright Wizard": [
        ("Aqshy's Power", "+{v} Magic Damage", [5, 10, 16], "magic_dmg"),
        ("Pyromancer", "+{v}% Skill 1 Damage", [20, 45, 75], "sk1"),
        ("Flame Barrier", "Flame Shield reflects {v} dmg", [6, 14, 24], "reflect"),
        ("Inferno", "+{v}% Skill 3 Damage", [20, 45, 75], "sk3"),
        ("Mana Well", "+{v} Max MP", [15, 30, 50], "mp"),
        ("Cauterize", "Fireball heals {v}% of dmg", [8, 18, 30], "lifesteal"),
    ],
}

# ── ENEMIES ──────────────────────────────────────────────────

ENEMIES_BY_TIER = {
    1: [
        {"name": "Skaven Clanrat", "hp": 28, "atk": 7, "dfn": 1, "xp": 18, "gold": (5, 12), "abilities": []},
        {"name": "Night Goblin", "hp": 22, "atk": 6, "dfn": 0, "xp": 14, "gold": (4, 10), "abilities": []},
        {"name": "Shambling Zombie", "hp": 32, "atk": 5, "dfn": 2, "xp": 14, "gold": (3, 8), "abilities": ["slow"]},
        {"name": "Bat Swarm", "hp": 18, "atk": 8, "dfn": 0, "xp": 12, "gold": (2, 6), "abilities": []},
        {"name": "Giant Spider", "hp": 25, "atk": 7, "dfn": 1, "xp": 15, "gold": (4, 9), "abilities": ["poison"]},
    ],
    2: [
        {"name": "Stormvermin", "hp": 45, "atk": 11, "dfn": 4, "xp": 28, "gold": (8, 18), "abilities": ["frenzy"]},
        {"name": "Orc Boy", "hp": 48, "atk": 12, "dfn": 3, "xp": 28, "gold": (10, 18), "abilities": ["heavy"]},
        {"name": "Skeleton Warrior", "hp": 38, "atk": 10, "dfn": 6, "xp": 24, "gold": (7, 14), "abilities": []},
        {"name": "Ungor Raider", "hp": 35, "atk": 9, "dfn": 2, "xp": 22, "gold": (6, 13), "abilities": []},
        {"name": "Crypt Ghoul", "hp": 40, "atk": 11, "dfn": 2, "xp": 25, "gold": (7, 15), "abilities": ["poison"]},
    ],
    3: [
        {"name": "Rat Ogre", "hp": 85, "atk": 17, "dfn": 5, "xp": 55, "gold": (16, 28), "abilities": ["frenzy", "heavy"]},
        {"name": "Black Orc", "hp": 75, "atk": 15, "dfn": 8, "xp": 50, "gold": (14, 25), "abilities": ["heavy"]},
        {"name": "Cairn Wraith", "hp": 55, "atk": 13, "dfn": 8, "xp": 45, "gold": (12, 22), "abilities": ["fear"]},
        {"name": "Gor", "hp": 55, "atk": 14, "dfn": 4, "xp": 42, "gold": (12, 20), "abilities": ["frenzy"]},
        {"name": "Chaos Marauder", "hp": 60, "atk": 14, "dfn": 5, "xp": 45, "gold": (13, 22), "abilities": []},
    ],
    4: [
        {"name": "Chaos Warrior", "hp": 95, "atk": 19, "dfn": 10, "xp": 70, "gold": (22, 38), "abilities": ["frenzy"]},
        {"name": "Bestigor", "hp": 70, "atk": 16, "dfn": 7, "xp": 60, "gold": (18, 30), "abilities": ["frenzy", "heavy"]},
        {"name": "Crypt Horror", "hp": 90, "atk": 17, "dfn": 7, "xp": 65, "gold": (20, 34), "abilities": ["regen"]},
        {"name": "Poison Wind Globadier", "hp": 40, "atk": 22, "dfn": 2, "xp": 55, "gold": (16, 28), "abilities": ["poison"]},
        {"name": "Wight King", "hp": 80, "atk": 18, "dfn": 9, "xp": 68, "gold": (20, 35), "abilities": ["fear"]},
    ],
    5: [
        {"name": "Chaos Chosen", "hp": 130, "atk": 24, "dfn": 13, "xp": 95, "gold": (30, 55), "abilities": ["frenzy", "regen"]},
        {"name": "Minotaur", "hp": 110, "atk": 22, "dfn": 8, "xp": 85, "gold": (28, 45), "abilities": ["frenzy", "heavy"]},
        {"name": "Vampire Thrall", "hp": 90, "atk": 20, "dfn": 10, "xp": 78, "gold": (24, 40), "abilities": ["regen", "fear"]},
        {"name": "Chaos Troll", "hp": 120, "atk": 20, "dfn": 7, "xp": 88, "gold": (26, 42), "abilities": ["regen", "heavy"]},
        {"name": "Hellpit Abomination", "hp": 150, "atk": 25, "dfn": 6, "xp": 100, "gold": (32, 55), "abilities": ["frenzy", "regen"]},
    ],
}

BOSSES = [
    {"name": "Skaven Warlord Gnawlitch", "hp": 160, "atk": 19, "dfn": 8, "xp": 130, "gold": (55, 90),
     "abilities": ["frenzy", "poison"], "taunt": "Yes-yes! You die-die, man-thing!",
     "intro": [
         "Warpstone braziers burn green as Gnawlitch emerges from the smoke.",
         "A horn blast echoes below, answered by frantic chittering in the dark.",
     ]},
    {"name": "Orc Warboss Grimjaw", "hp": 190, "atk": 22, "dfn": 10, "xp": 150, "gold": (65, 100),
     "abilities": ["frenzy", "heavy"], "taunt": "WAAAGH! I'z gonna krump ya good!",
     "intro": [
         "A battered war-drum pounds as Grimjaw slams his axe against his shield.",
         "Trophies of broken helms hang from iron spikes around the chamber.",
     ]},
    {"name": "Necromancer Aldric the Pale", "hp": 110, "atk": 16, "dfn": 6, "xp": 140, "gold": (60, 95),
     "abilities": ["regen", "fear", "poison"], "taunt": "Rise, my servants! Feast upon the living!",
     "intro": [
         "Candles ignite one by one as Aldric raises a blackened staff.",
         "The dead stir in niches along the walls, jaws clattering in hunger.",
     ]},
    {"name": "Chaos Sorcerer Vorath", "hp": 130, "atk": 20, "dfn": 9, "xp": 160, "gold": (70, 110),
     "abilities": ["frenzy", "fear"], "taunt": "The Dark Gods grant me power beyond your comprehension!",
     "intro": [
         "Blue fire dances between Vorath's fingers in impossible geometric patterns.",
         "A circle of runes rotates slowly underfoot, humming with corrupted power.",
     ]},
    {"name": "Vampire Lord Mannfried", "hp": 170, "atk": 24, "dfn": 12, "xp": 190, "gold": (85, 130),
     "abilities": ["regen", "fear", "frenzy"], "taunt": "You dare enter my domain, mortal? Your blood shall be my wine.",
     "intro": [
         "Silk curtains stir though there is no breeze, and Mannfried smiles from a throne of bones.",
         "Crystal goblets filled with dark blood line a banquet table set for no living guests.",
     ]},
    {"name": "Greater Daemon of Tzeentch", "hp": 250, "atk": 28, "dfn": 14, "xp": 250, "gold": (100, 160),
     "abilities": ["frenzy", "regen", "fear", "poison"], "taunt": "All is dust. All is change. You are nothing.",
     "intro": [
         "Reality ripples as feathered limbs unfold from a tear in the air.",
         "Voices speak in reverse around you, each one promising your end.",
     ]},
    {"name": "Vermin Lord Screechak", "hp": 220, "atk": 26, "dfn": 11, "xp": 230, "gold": (95, 150),
     "abilities": ["frenzy", "poison", "fear"], "taunt": "The Horned Rat sees-smells your fear, yes-yes!",
     "intro": [
         "The chamber floor crawls with lesser skaven that scatter before their master.",
         "Screechak towers over you, horns scraping ancient stone.",
     ]},
    {"name": "Wight King Krell", "hp": 200, "atk": 25, "dfn": 15, "xp": 220, "gold": (90, 145),
     "abilities": ["fear", "heavy", "frenzy"], "taunt": "...",
     "intro": [
         "Dust falls from Krell's armour as he rises, sword held in both hands.",
         "The temperature drops; your breath fogs in the dead king's presence.",
     ]},
]

# ── ITEMS ────────────────────────────────────────────────────

WEAPON_TYPES = ["Sword", "Axe", "Hammer", "Spear", "Dagger", "Mace", "Halberd", "Greataxe", "Bow", "Staff"]
ARMOR_TYPES = ["Leather Armour", "Chainmail", "Scale Armour", "Plate Armour", "Brigandine", "Robes"]
ACCESSORY_TYPES = ["Ring", "Amulet", "Talisman", "Charm", "Torc", "Pendant"]

PREFIXES = {
    "Common": ["Iron", "Steel", "Crude", "Simple", "Worn"],
    "Uncommon": ["Fine", "Tempered", "Sturdy", "Keen", "Reinforced"],
    "Rare": ["Runic", "Enchanted", "Blessed", "Masterwork", "Gilded"],
    "Epic": ["Doomforged", "Grimsteel", "Ancient", "Warpforged", "Shadow-touched"],
    "Legendary": ["Sigmarite", "Starmetal", "Mythic", "Runefang", "Ancestor's"],
}

SUFFIXES = ["of Might", "of the Bear", "of Swiftness", "of the Eagle",
            "of the Arcane", "of Warding", "of Slaying", "of Fortune",
            "of the Wolf", "of Resilience", "of Vengeance", "of the Dawn"]

POTION_TYPES = {
    "Health Potion": {"type": "heal", "value": 0.4, "desc": "Restores 40% of max HP", "base_cost": 25},
    "Mana Potion": {"type": "mana", "value": 0.4, "desc": "Restores 40% of max MP", "base_cost": 20},
    "Elixir of Might": {"type": "buff_str", "value": 3, "turns": 5, "desc": "+3 STR for 5 turns", "base_cost": 40},
    "Ironbark Tonic": {"type": "buff_def", "value": 5, "turns": 5, "desc": "+5 DEF for 5 turns", "base_cost": 40},
    "Antidote": {"type": "cure", "desc": "Removes poison", "base_cost": 15},
}

# ── AMBIENT MESSAGES ─────────────────────────────────────────

AMBIENT_TOWN = [
    co("  ~ The sound of rain on cobblestones is strangely comforting.", C.CYN),
    co("  ~ A Town Crier shouts news of Chaos incursions to the north.", C.CYN),
    co("  ~ The smell of fresh bread drifts from a nearby bakery.", C.CYN),
    co("  ~ A patrol of Reikland soldiers marches past, armour clanking.", C.CYN),
    co("  ~ Distant thunder rolls across the Grey Mountains.", C.CYN),
    co("  ~ A drunken Dwarf stumbles from the tavern, cursing in Khazalid.", C.CYN),
    co("  ~ The bells of the Temple of Sigmar toll the evening hour.", C.CYN),
    co("  ~ Ravens circle the town square, an ill omen.", C.CYN),
    co("  ~ The wind carries a faint howl from beyond the town walls.", C.CYN),
    co("  ~ Merchants haggle loudly in the market square.", C.CYN),
    co("  ~ A Witch Hunter eyes you suspiciously from across the street.", C.CYN),
    co("  ~ Children play at being knights, fighting invisible foes.", C.CYN),
    co("  ~ The scent of pipe-weed wafts from a dim alleyway.", C.CYN),
    co("  ~ Flagellants chant doom and gloom near the temple steps.", C.CYN),
    co("  ~ A cold wind from the north carries whispers of war.", C.CYN),
    co("  ~ Torchlight flickers in the evening mist.", C.CYN),
    co("  ~ A bard sings of the defeat at Mordheim in a mournful voice.", C.CYN),
    co("  ~ The old well creaks as a woman draws water.", C.CYN),
    co("  ~ Somewhere, a dog barks at shadows.", C.CYN),
    co("  ~ Heavy grey clouds promise more rain before dawn.", C.CYN),
]

WORLD_TIMES = ["Dawn", "Morning", "Noon", "Dusk", "Night", "Midnight"]
WORLD_WEATHER = [
    "Cold rain lashes the rooftops.",
    "A wet mist clings to the streets.",
    "A biting wind sweeps in from the north.",
    "Clear skies reveal Morrslieb's sickly glow.",
    "Heavy clouds gather over the town walls.",
    "A pale drizzle turns the streets to mud.",
]
WORLD_OMENS = [
    "Temple bells toll without warning.",
    "Ravens gather above the old watchtower.",
    "Witch Hunters inspect wagons at the gate.",
    "Flagellants preach doom by torchlight.",
    "A green-tinted moonlight stains the cobbles.",
    "No omen troubles the town this hour.",
]

AMBIENT_DUNGEON = [
    co("  ~ Water drips from the ceiling in a maddening rhythm.", C.GRY),
    co("  ~ A distant shriek echoes through the darkness.", C.GRY),
    co("  ~ Your torch flickers, casting dancing shadows on the walls.", C.GRY),
    co("  ~ You hear the skittering of tiny claws somewhere ahead.", C.GRY),
    co("  ~ The air is thick with the stench of decay.", C.GRY),
    co("  ~ Ancient runes glow faintly on the stone walls.", C.GRY),
    co("  ~ A cold draught blows from somewhere deeper below.", C.GRY),
    co("  ~ The silence is oppressive, broken only by your footsteps.", C.GRY),
    co("  ~ Mould and fungus grow in grotesque patterns along the walls.", C.GRY),
    co("  ~ You step over old bones — the remains of a past adventurer.", C.GRY),
    co("  ~ A rat squeaks and scurries away from your torchlight.", C.GRY),
    co("  ~ The walls are slick with moisture and something... else.", C.GRY),
    co("  ~ Faded murals depict an ancient battle against a great evil.", C.GRY),
    co("  ~ The floor is uneven — you must watch your step.", C.GRY),
    co("  ~ A strange warmth radiates from the stones beneath your feet.", C.GRY),
    co("  ~ You hear the grinding of stone on stone, far away.", C.GRY),
    co("  ~ Cobwebs thick as curtains hang from the archway ahead.", C.GRY),
    co("  ~ The air tastes of copper and old magic.", C.GRY),
    co("  ~ A faint green glow pulses from cracks in the wall.", C.GRY),
    co("  ~ Your shadow seems to move independently for a heartbeat.", C.GRY),
]

AMBIENT_DEEP = [
    co("  ~ The darkness here feels alive, pressing against your torch.", C.RED),
    co("  ~ Whispers in a language you don't know call from the dark.", C.RED),
    co("  ~ The walls seem to breathe. You tell yourself it's the wind.", C.RED),
    co("  ~ A bestial roar echoes from the depths below.", C.RED),
    co("  ~ Warpstone crystals jut from the walls, their glow sickening.", C.RED),
    co("  ~ Blood stains the floor — fresh. Someone else came this way.", C.RED),
    co("  ~ The air crackles with dark energy. Chaos is strong here.", C.RED),
    co("  ~ You feel eyes upon you from every shadow.", C.RED),
]

DUNGEON_DEPTH_MOODS = [
    (1, "Stale air and old stone. The upper ruins still remember mortal hands."),
    (6, "The masonry grows older. Symbols of lost cults scar the walls."),
    (11, "The dark is thicker here, and every sound travels too far."),
    (16, "Warp-taint clings to the floor like frost. Your torch burns uneasy."),
    (21, "You have entered places that should not exist beneath Ubersreik."),
]

ROOM_AMBIENCE = {
    "Narrow Corridor": [
        "The passage squeezes tight; your shoulders brush damp stone.",
        "Arrow slits in the wall suggest this hall once held a defensive line.",
    ],
    "Vaulted Chamber": [
        "Your footsteps echo up into darkness you cannot see.",
        "A cracked dome overhead bears faded imperial frescoes.",
    ],
    "Ancient Crypt": [
        "Dust-coated sarcophagi line the walls in perfect silence.",
        "Old funerary masks watch you from shattered alcoves.",
    ],
    "Flooded Passage": [
        "Cold black water laps around your boots.",
        "Ripples spread for no reason in the darkness ahead.",
    ],
    "Collapsed Hall": [
        "Broken pillars and fallen stone force a careful route.",
        "You smell old dust and recently shifted rubble.",
    ],
    "Eldritch Library": [
        "Rotted shelves hold books bound in skin and tarnished brass.",
        "Half-burned parchments whisper when the draft catches them.",
    ],
    "Fungal Cavern": [
        "Pale mushrooms pulse faintly, feeding on rot and damp.",
        "Spores drift in the torchlight like ash from a distant pyre.",
    ],
    "Torture Chamber": [
        "Rusty hooks sway gently as if disturbed moments ago.",
        "Iron instruments are laid out with ritual precision.",
    ],
    "Ossuary": [
        "Skulls are stacked in neat walls, each staring sightlessly outward.",
        "The floor crunches with powdered bone underfoot.",
    ],
    "Shrine Room": [
        "An old altar stands cracked, symbols chiselled away in hatred.",
        "Candles burn despite the stale air and lack of attendants.",
    ],
    "Abandoned Mine": [
        "Old rails vanish into a collapsed tunnel mouth.",
        "Pickaxes lie where miners dropped them long ago.",
    ],
    "Sewer Junction": [
        "Filth gathers in stagnant channels cut through the stone.",
        "The stench is overpowering, and something splashes nearby.",
    ],
    "Ritual Circle": [
        "Dried blood marks a circle carved with forbidden sigils.",
        "Wax and ash suggest recent ceremonies were performed here.",
    ],
    "Armoury": [
        "Weapon racks stand empty except for rust and broken hafts.",
        "A cracked shield bears the faded griffon of a long-dead regiment.",
    ],
    "Catacombs": [
        "The tunnel splits into rows of burial niches and sunken vaults.",
        "Grave dust and cold air cling to your lungs.",
    ],
}

# ── LORE ENTRIES ─────────────────────────────────────────────

LORE = [
    ("The Skaven Under-Empire",
     "Beneath the Old World lies a vast network of tunnels and warrens — the Under-Empire of the Skaven. These ratmen worship the Horned Rat and seek the destruction of surface dwellers. Their numbers are beyond counting, and their Warlords scheme endlessly for power. Only the ignorant deny their existence."),
    ("The Great Book of Grudges",
     "The Dammaz Kron, the Great Book of Grudges, is the most sacred artefact of the Dwarf race. Within its ancient pages, every wrong ever done to the Dwarfs is recorded in blood. A grudge is never forgotten, never forgiven. Only when vengeance is taken can an entry be struck out — in the blood of the wrongdoer."),
    ("Sigmar Heldenhammer",
     "Sigmar, first Emperor of Man, united the tribes of men and forged an empire that endures to this day. He wielded the great warhammer Ghal Maraz, gifted to him by the Dwarf King Kurgan Ironbeard. Upon his abdication, he passed east and was never seen again — but his spirit endures as the patron god of the Empire."),
    ("The Chaos Wastes",
     "To the far north lie the Chaos Wastes, where reality itself frays and the Realm of Chaos bleeds through. The four Dark Gods — Khorne, Tzeentch, Nurgle, and Slaanesh — hold dominion there. Warriors who seek their dark blessing travel north, returning as twisted Champions of Chaos... if they return at all."),
    ("The Elves of Ulthuan",
     "The High Elves of Ulthuan are the eldest of the civilised races. Once, their empire spanned the globe. Now they guard their island realm against the Dark Elves of Naggaroth and the ever-present threat of Chaos. Their art of magic is unmatched, and their warriors fight with millennia of experience."),
    ("Morrslieb, the Chaos Moon",
     "The sickly green moon known as Morrslieb is whispered to be a fragment of solidified Warpstone. On nights when Morrslieb is full, madness walks the land — mutants are born, Beastmen grow bold, and Chaos Sorcerers feel their power swell. Wise folk bar their doors on such nights."),
    ("The Winds of Magic",
     "Eight Winds of Magic blow from the north — Aqshy (Fire), Azyr (Heavens), Chamon (Metal), Ghur (Beasts), Ghyran (Life), Hysh (Light), Shyish (Death), and Ulgu (Shadow). Each can be harnessed by trained Wizards, though the risk of daemonic possession is ever-present."),
    ("The Vampire Counts",
     "In the cursed land of Sylvania, the Vampire Counts rule from their crumbling castles. Created by the dark magic of Nagash, vampires are immortal, immensely powerful, and utterly evil. They raise vast armies of the dead and seek dominion over the living."),
    ("Karak Eight Peaks",
     "Once the mightiest Dwarf hold after Karaz-a-Karak, Karak Eight Peaks fell to Skaven and Greenskin invasion centuries ago. Countless expeditions have sought to reclaim it, but the depths are infested. The grudge for its loss burns hot in every Dwarf heart."),
    ("Athel Loren",
     "The enchanted forest of Athel Loren is home to the Wood Elves and the ancient tree-spirits. The forest itself is alive and deeply hostile to outsiders. Those who enter uninvited are never seen again. The Waywatchers of Athel Loren patrol its borders with deadly vigilance."),
    ("The Empire's Colleges of Magic",
     "Following the Great War against Chaos, the High Elf mage Teclis founded the Colleges of Magic in Altdorf. Eight colleges, one for each Wind of Magic, train human wizards. The Bright College harnesses Aqshy and is known for its destructive fire magic."),
    ("Greenskin WAAAGH!",
     "When an Orc Warboss grows powerful enough, he calls a WAAAGH! — a great migration of war that sweeps across the land. Orcs and Goblins flock to the banner, drawn by the promise of fighting. A WAAAGH! can threaten entire nations and has toppled kingdoms."),
    ("The Cult of Ulric",
     "In Middenheim, many still worship Ulric, god of winter, wolves, and battle. Ulricans disdain weakness and prize strength proven in hardship. Though rivalry with Sigmar's church runs deep, both faiths stand against Chaos when the north burns."),
    ("Nagash, Great Necromancer",
     "Nagash, once a priest-king of Nehekhara, mastered death magic so thoroughly that all necromancy bends toward his will. Even in ruin and apparent death, his influence reaches across centuries. Graveyards grow restless where his name is spoken."),
    ("Bretonnian Grail Knights",
     "In Bretonnia, noble knights quest for the blessing of the Lady of the Lake. Those who drink from the Grail return changed: stronger, purer, and touched by divine purpose. Their charge has broken hosts of Orcs, Beastmen, and worse."),
    ("The Black Fire Pass",
     "Black Fire Pass is the blood-stained gate between the Empire and the Worlds Edge Mountains. Dwarfs and men have stood together there against countless invasions. Its stones remember every oath, every betrayal, and every last stand."),
    ("The Drakwald Forest",
     "The Drakwald is an ancient forest where Beastmen tribes gather beneath twisted boughs. Roads vanish, patrols disappear, and moonlit clearings become slaughter grounds. Lumber camps burn as soon as they are built."),
    ("The Orders of Knights Panther",
     "The Knights Panther trace their origin to crusades against Araby. Proud and severe, they uphold chivalric codes in service to the Empire. Their white cloaks have become a symbol of retribution against raiders and cultists alike."),
    ("Skaven Clan Skryre",
     "Clan Skryre thrives on warpstone engineering: doomwheels, poison wind globes, and unstable cannons that are as lethal to allies as enemies. Their warlock engineers care little for casualties so long as destruction is spectacular."),
    ("The Doom of Mordheim",
     "Mordheim, once a prosperous city, was shattered when a twin-tailed comet struck in 1999 IC. Warpstone rained across its streets, and warbands soon descended to claim it. Those who survive the City of the Damned rarely remain sane."),
    ("The Moot and the Halflings",
     "The Mootland is home to the Empire's Halflings, famed for hospitality, archery, and improbable bravery when cornered. Their militias are underestimated at great peril. Even Elector Counts mind their alliances with the Moot."),
    ("The Graue Familie",
     "Wizards of the Grey College practice the subtle arts of Ulgu, the Lore of Shadow. Illusion, misdirection, and careful observation are their tools. In courts and battlefields alike, Grey Wizards wage wars without ever being seen."),
    ("The Beastmen Brayherds",
     "Beastmen gather in brayherds led by brutal Beastlords and foul shamans. They strike from forests and ruins, destroying shrines, farms, and roadwatch towers. Their hatred of civilization is primal and absolute."),
    ("The Karaz Ankor",
     "The Dwarf holds of the Worlds Edge Mountains are collectively known as the Karaz Ankor, the Everlasting Realm. Though diminished from ancient glory, each hold remains a fortress of craft, memory, and grudges waiting to be paid."),
    ("The Reiksguard",
     "The Reiksguard are among the Empire's most elite knights, sworn directly to the Emperor. In gleaming plate and disciplined ranks, they form the steel spine of imperial campaigns. Their standards are never lowered in retreat."),
    ("The Horned Rat",
     "The Skaven worship the Horned Rat, a cruel god of disease, treachery, and ravenous ambition. Its priests spread corruption from the shadows, and its blessings are always double-edged. In Skaven society, betrayal is a form of devotion."),
]

# ── TAVERN RUMORS ────────────────────────────────────────────

RUMORS = [
    "They say the deeper dungeons hold treasures from the age of Sigmar himself...",
    "A merchant caravan was found slaughtered on the Altdorf road. Beastmen, they reckon.",
    "The Witch Hunters have been burning more books than usual. Something's got them spooked.",
    "I heard screaming from beneath the old cemetery last night. Nobody went to check.",
    "A Dwarf Slayer passed through yesterday. Said he was seeking his doom in the depths below.",
    "The Skaven? Pah! Old wives' tales, I say! ...Don't look at me like that.",
    "They found Warpstone in the lower levels. Guard Captain sealed that section off quick.",
    "An Elf was here last week. Asked strange questions about ley lines beneath the town.",
    "The blacksmith says the metal from the dungeon makes finer blades than Empire steel.",
    "The Temple priests have been praying day and night. That can't be a good sign.",
    "Old Karl swears he saw something with too many eyes watching from the tree line.",
    "The river ran red for a day last month. Nobody knows why, and nobody wants to.",
    "A knight of the Blazing Sun rode through — heading north. He looked... frightened.",
    "They say if you listen at the dungeon entrance on a still night, you can hear chanting.",
]

RUMOR_CHAINS = [
    [
        "The watch found strange claw-marks near the granaries last night.",
        "Those claw-marks reached the old well. No tracks led away from it.",
        "Two rat-catchers vanished after going below the old well. Nobody speaks of it now.",
    ],
    [
        "Pilgrims arrived from Middenheim with stories of fires in the Drakwald.",
        "The pilgrims say Beastmen carry crude standards marked with a bleeding moon.",
        "Refugees now sleep in the temple courtyard. The priests are arming acolytes.",
    ],
    [
        "Dorak swears someone sold him ore that hummed in the dark.",
        "That same ore split his anvil face clean in two.",
        "Now Dorak keeps a loaded pistol by the forge and won't say why.",
    ],
    [
        "A noble coach arrived at dusk and left before dawn with no escort.",
        "The coachman wore mourning black and asked for directions to the catacombs.",
        "The graveyard gates were open this morning. They were locked last night.",
    ],
]

ROOM_TYPES = ["Narrow Corridor", "Vaulted Chamber", "Ancient Crypt",
              "Flooded Passage", "Collapsed Hall", "Eldritch Library",
              "Fungal Cavern", "Torture Chamber", "Ossuary", "Shrine Room",
              "Abandoned Mine", "Sewer Junction", "Ritual Circle",
              "Armoury", "Catacombs"]

# ═══════════════════════════════════════════════════════════════
#  ITEM SYSTEM
# ═══════════════════════════════════════════════════════════════

class Item:
    def __init__(self, name, slot, rarity, level, damage=0, defense=0, bonus_stats=None, special=""):
        self.name = name
        self.slot = slot  # weapon, armor, accessory
        self.rarity = rarity
        self.level = level
        self.damage = damage
        self.defense = defense
        self.bonus_stats = bonus_stats or {}
        self.special = special

    def display_name(self):
        c = RC.get(self.rarity, C.WHT)
        return f"{c}{self.name}{C.RST}"

    def stat_line(self):
        parts = []
        if self.damage > 0:
            parts.append(co(f"DMG +{self.damage}", C.RED))
        if self.defense > 0:
            parts.append(co(f"DEF +{self.defense}", C.BLU))
        for s, v in self.bonus_stats.items():
            parts.append(co(f"{s.upper()} +{v}", C.GRN))
        if self.special:
            parts.append(co(self.special, C.CYN))
        return " | ".join(parts) if parts else co("No stats", C.GRY)

    def power_score(self):
        return self.damage * 2 + self.defense * 2 + sum(self.bonus_stats.values()) * 1.5

    def to_dict(self):
        return {"name": self.name, "slot": self.slot, "rarity": self.rarity,
                "level": self.level, "damage": self.damage, "defense": self.defense,
                "bonus_stats": self.bonus_stats, "special": self.special}

    @staticmethod
    def from_dict(d):
        return Item(d["name"], d["slot"], d["rarity"], d["level"],
                    d.get("damage", 0), d.get("defense", 0),
                    d.get("bonus_stats", {}), d.get("special", ""))


def roll_rarity(depth):
    r = random.random()
    db = min(depth * 0.004, 0.12)
    if r < 0.008 + db * 0.15:
        return "Legendary"
    elif r < 0.05 + db * 0.4:
        return "Epic"
    elif r < 0.18 + db:
        return "Rare"
    elif r < 0.48 + db * 0.5:
        return "Uncommon"
    return "Common"


def generate_item(depth, rarity=None, slot=None):
    if rarity is None:
        rarity = roll_rarity(depth)
    if slot is None:
        slot = random.choice(["weapon", "armor", "accessory"])

    rm = RARITY_MULT[rarity]
    prefix = random.choice(PREFIXES[rarity])

    if slot == "weapon":
        base = random.choice(WEAPON_TYPES)
        name = f"{prefix} {base}"
        if rarity in ("Rare", "Epic", "Legendary"):
            name += f" {random.choice(SUFFIXES)}"
        dmg = int((5 + depth * 2.2) * rm * random.uniform(0.85, 1.15))
        dfn = 0
        bonus = {}
        if rarity in ("Uncommon", "Rare", "Epic", "Legendary"):
            s = random.choice(["str", "agi", "int"])
            bonus[s] = int((1 + depth * 0.3) * rm * random.uniform(0.8, 1.2))
        if rarity in ("Epic", "Legendary"):
            s2 = random.choice(["crit", "str", "agi", "int", "wil"])
            bonus[s2] = bonus.get(s2, 0) + int((1 + depth * 0.2) * rm * random.uniform(0.8, 1.2))
        special = ""
        if rarity == "Legendary":
            special = random.choice(["Cleave: +15% DMG", "Lifesteal: 8%", "Sigmar's Light: +10% vs Undead",
                                     "Runic: +5% Crit", "+20% vs Chaos"])
        return Item(name, "weapon", rarity, depth, damage=dmg, bonus_stats=bonus, special=special)

    elif slot == "armor":
        base = random.choice(ARMOR_TYPES)
        name = f"{prefix} {base}"
        if rarity in ("Rare", "Epic", "Legendary"):
            name += f" {random.choice(SUFFIXES)}"
        dfn = int((3 + depth * 1.6) * rm * random.uniform(0.85, 1.15))
        bonus = {}
        if rarity in ("Uncommon", "Rare", "Epic", "Legendary"):
            s = random.choice(["tou", "wil", "str"])
            bonus[s] = int((1 + depth * 0.25) * rm * random.uniform(0.8, 1.2))
        if rarity in ("Epic", "Legendary"):
            s2 = random.choice(["tou", "wil", "hp"])
            bonus[s2] = bonus.get(s2, 0) + int((1 + depth * 0.2) * rm * random.uniform(0.8, 1.2))
        special = ""
        if rarity == "Legendary":
            special = random.choice(["Gromril-forged: +10% Block", "Ward Save: 8%",
                                     "Regeneration: +3 HP/turn", "Thorns: Reflect 5 DMG"])
        return Item(name, "armor", rarity, depth, defense=dfn, bonus_stats=bonus, special=special)

    else:  # accessory
        base = random.choice(ACCESSORY_TYPES)
        name = f"{prefix} {base}"
        if rarity in ("Rare", "Epic", "Legendary"):
            name += f" {random.choice(SUFFIXES)}"
        bonus = {}
        stats_pool = ["str", "tou", "agi", "int", "wil"]
        n_stats = {"Common": 1, "Uncommon": 1, "Rare": 2, "Epic": 2, "Legendary": 3}[rarity]
        for _ in range(n_stats):
            s = random.choice(stats_pool)
            bonus[s] = bonus.get(s, 0) + int((1 + depth * 0.35) * rm * random.uniform(0.8, 1.2))
        special = ""
        if rarity == "Legendary":
            special = random.choice(["+10% XP Gain", "+15% Gold Find", "Lucky: +8% Item Rarity",
                                     "+5% All Resists", "Swift: +10% Dodge"])
        dmg = int((1 + depth * 0.5) * rm * random.uniform(0.8, 1.2)) if rarity in ("Epic", "Legendary") else 0
        dfn = int((1 + depth * 0.3) * rm * random.uniform(0.8, 1.2)) if rarity in ("Rare", "Epic", "Legendary") else 0
        return Item(name, "accessory", rarity, depth, damage=dmg, defense=dfn, bonus_stats=bonus, special=special)


# ═══════════════════════════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════════════════════════

class Player:
    def __init__(self, name, cls):
        cd = CLASSES[cls]
        self.name = name
        self.cls = cls
        self.level = 1
        self.xp = 0
        self.gold = 50
        self.stats = dict(cd["stats"])
        self.base_hp = cd["hp"]
        self.base_mp = cd["mp"]
        self.talent_points = 0
        self.talents = {t[0]: 0 for t in TALENTS[cls]}
        self.equipment = {"weapon": None, "armor": None, "accessory": None}
        self.inventory = []  # list of Item
        self.potions = {"Health Potion": 3, "Mana Potion": 2}
        self.max_depth_cleared = 0
        self.total_kills = 0
        self.total_gold_earned = 0
        self.lore_found = []
        self.paragon = 0
        self.world_day = 1
        self.world_time_index = random.randrange(len(WORLD_TIMES))
        self.world_weather = random.choice(WORLD_WEATHER)
        self.world_omen = random.choice(WORLD_OMENS)
        self.story_flags = []
        self.rumor_progress = {}
        self.last_expedition = {}
        # Combat transient state
        self.status_effects = []
        self.defending = False
        self.dodge_next = False
        # Set HP/MP after all dependencies are initialized
        self.hp = self.max_hp
        self.mp = self.max_mp

    # ── Derived stats ─────────────────────────────────────────
    @property
    def max_hp(self):
        base = self.base_hp + self.stats["tou"] * 5 + (self.level - 1) * 8
        talent_bonus = self._talent_val("hp")
        equip_bonus = sum(it.bonus_stats.get("hp", 0) for it in self.equipment.values() if it)
        return base + talent_bonus + equip_bonus + self.paragon * 3

    @property
    def max_mp(self):
        base = self.base_mp + self.stats["wil"] * 3 + (self.level - 1) * 4
        talent_bonus = self._talent_val("mp")
        return base + talent_bonus + self.paragon * 2

    @property
    def attack_power(self):
        base = self.stats["str"] * 2 + self.level
        weapon = self.equipment["weapon"]
        w_dmg = weapon.damage if weapon else 0
        equip_str = sum(it.bonus_stats.get("str", 0) for it in self.equipment.values() if it)
        talent_magic = self._talent_val("magic_dmg")
        return base + w_dmg + equip_str * 2 + talent_magic

    @property
    def magic_power(self):
        base = self.stats["int"] * 3 + self.level
        weapon = self.equipment["weapon"]
        w_dmg = weapon.damage if weapon else 0
        equip_int = sum(it.bonus_stats.get("int", 0) for it in self.equipment.values() if it)
        talent_magic = self._talent_val("magic_dmg")
        return base + w_dmg + equip_int * 2 + talent_magic

    @property
    def defense(self):
        base = self.stats["tou"]
        armor = self.equipment["armor"]
        a_def = armor.defense if armor else 0
        equip_tou = sum(it.bonus_stats.get("tou", 0) for it in self.equipment.values() if it)
        talent_def = self._talent_val("defense")
        acc_def = sum(it.defense for it in self.equipment.values() if it and it.slot == "accessory")
        return base + a_def + equip_tou + talent_def + acc_def

    @property
    def crit_chance(self):
        base = 5 + self.stats["agi"] * 0.8
        talent = self._talent_val("crit")
        equip = sum(it.bonus_stats.get("crit", 0) for it in self.equipment.values() if it)
        return min(base + talent + equip, 75)

    @property
    def dodge_chance(self):
        base = self.stats["agi"] * 0.5
        talent = self._talent_val("dodge")
        return min(base + talent, 60)

    @property
    def block_chance(self):
        return min(self._talent_val("block"), 50)

    def _talent_val(self, stat_key):
        for t in TALENTS[self.cls]:
            if t[3] == stat_key:
                rank = self.talents.get(t[0], 0)
                return t[2][rank - 1] if rank > 0 else 0
        return 0

    # ── Talent helpers ────────────────────────────────────────
    def get_talent_bonus(self, key):
        """Get total talent bonus for given key."""
        total = 0
        for t in TALENTS[self.cls]:
            if t[3] == key:
                rank = self.talents.get(t[0], 0)
                if rank > 0:
                    total += t[2][rank - 1]
        return total

    # ── XP & Level ────────────────────────────────────────────
    @property
    def xp_to_level(self):
        if self.level >= 25:
            return int(200 * (self.level * 1.5))
        return int(80 * self.level * (1.12 ** self.level))

    def gain_xp(self, amount):
        xp_bonus = 0
        for it in self.equipment.values():
            if it and "+10% XP Gain" in (it.special or ""):
                xp_bonus += 10
        amount = int(amount * (1 + xp_bonus / 100))
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            leveled = True
            if self.level <= 25:
                self.talent_points += 1
            else:
                self.paragon += 1
        if leveled:
            self.hp = self.max_hp
            self.mp = self.max_mp
        return leveled

    # ── Combat methods ────────────────────────────────────────
    def take_damage(self, raw_dmg):
        red = self.defense / (self.defense + 50)
        if self.defending:
            red = min(red + 0.5, 0.85)
        for e in self.status_effects:
            if e["name"] == "Iron Resolve":
                red = min(red + e.get("value", 0.5), 0.85)
            if e["name"] == "Flame Shield":
                red = min(red + e.get("value", 0.4), 0.85)
        if self.dodge_next:
            self.dodge_next = False
            return 0, "dodged"
        if random.random() * 100 < self.dodge_chance:
            return 0, "dodged"
        if random.random() * 100 < self.block_chance:
            return 0, "blocked"
        actual = max(1, int(raw_dmg * (1 - red)))
        self.hp = max(0, self.hp - actual)
        # Check flame shield reflect
        reflected = 0
        for e in self.status_effects:
            if e["name"] == "Flame Shield":
                reflected += self.get_talent_bonus("reflect") + 8
        return actual, reflected

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + int(amount))

    def restore_mp(self, amount):
        self.mp = min(self.max_mp, self.mp + int(amount))

    def calc_damage(self, mult=1.0, is_magic=False, auto_crit=False, skill_key=None):
        base = self.magic_power if is_magic else self.attack_power
        bonus_pct = 0
        if skill_key:
            bonus_pct = self.get_talent_bonus(skill_key)
        dmg = base * mult * (1 + bonus_pct / 100)
        crit = False
        if auto_crit or random.random() * 100 < self.crit_chance:
            dmg *= 1.8
            crit = True
        dmg *= random.uniform(0.9, 1.1)
        # Grudge damage bonus for Ironbreaker
        grudge_pct = self.get_talent_bonus("grudge_pct")
        if grudge_pct > 0 and self.max_hp > 0:
            missing_pct = (1 - self.hp / self.max_hp) * 100
            dmg *= (1 + (missing_pct / 10) * grudge_pct / 100)
        return max(1, int(dmg)), crit

    def apply_status_tick(self):
        msgs = []
        regen = self.get_talent_bonus("regen")
        if regen > 0:
            self.heal(regen)
            msgs.append(co(f"  Nature's Grace restores {regen} HP.", C.GRN))
        new_effects = []
        for e in self.status_effects:
            if e.get("dot"):
                r = self.get_talent_bonus("resist")
                if random.random() * 100 < r:
                    msgs.append(co(f"  You resist the {e['name']} effect!", C.BGRN))
                else:
                    self.hp = max(0, self.hp - e["dot"])
                    msgs.append(co(f"  {e['name']} deals {e['dot']} damage!", C.RED))
            e["turns"] -= 1
            if e["turns"] > 0:
                new_effects.append(e)
            else:
                msgs.append(co(f"  {e['name']} fades.", C.GRY))
        self.status_effects = new_effects
        self.defending = False
        return msgs

    def is_alive(self):
        return self.hp > 0

    def full_heal(self):
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.status_effects = []
        self.defending = False
        self.dodge_next = False

    @property
    def world_time(self):
        return WORLD_TIMES[self.world_time_index % len(WORLD_TIMES)]

    def advance_world(self, steps=1):
        for _ in range(max(1, steps)):
            self.world_time_index = (self.world_time_index + 1) % len(WORLD_TIMES)
            if self.world_time_index == 0:
                self.world_day += 1
                self.world_weather = random.choice(WORLD_WEATHER)
                if random.random() < 0.6:
                    self.world_omen = random.choice(WORLD_OMENS)
            elif random.random() < 0.25:
                self.world_omen = random.choice(WORLD_OMENS)

    def set_story_flag(self, flag):
        if flag and flag not in self.story_flags:
            self.story_flags.append(flag)

    # ── Equipment ─────────────────────────────────────────────
    def equip(self, item):
        old = self.equipment[item.slot]
        self.equipment[item.slot] = item
        if item in self.inventory:
            self.inventory.remove(item)
        if old:
            self.inventory.append(old)
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)
        return old

    # ── Serialization ─────────────────────────────────────────
    def to_dict(self):
        equip = {}
        for slot, it in self.equipment.items():
            equip[slot] = it.to_dict() if it else None
        return {
            "name": self.name, "cls": self.cls, "level": self.level,
            "xp": self.xp, "gold": self.gold, "stats": self.stats,
            "base_hp": self.base_hp, "base_mp": self.base_mp,
            "hp": self.hp, "mp": self.mp,
            "talent_points": self.talent_points, "talents": self.talents,
            "equipment": equip,
            "inventory": [it.to_dict() for it in self.inventory],
            "potions": self.potions,
            "max_depth_cleared": self.max_depth_cleared,
            "total_kills": self.total_kills,
            "total_gold_earned": self.total_gold_earned,
            "lore_found": self.lore_found,
            "paragon": self.paragon,
            "world_day": self.world_day,
            "world_time_index": self.world_time_index,
            "world_weather": self.world_weather,
            "world_omen": self.world_omen,
            "story_flags": self.story_flags,
            "rumor_progress": self.rumor_progress,
            "last_expedition": self.last_expedition,
            "version": VERSION,
        }

    @staticmethod
    def from_dict(d):
        p = Player.__new__(Player)
        p.name = d["name"]; p.cls = d["cls"]; p.level = d["level"]
        p.xp = d["xp"]; p.gold = d["gold"]; p.stats = d["stats"]
        p.base_hp = d["base_hp"]; p.base_mp = d["base_mp"]
        p.talent_points = d.get("talent_points", 0)
        p.talents = d.get("talents", {t[0]: 0 for t in TALENTS[d["cls"]]})
        p.equipment = {}
        for slot in ("weapon", "armor", "accessory"):
            ed = d["equipment"].get(slot)
            p.equipment[slot] = Item.from_dict(ed) if ed else None
        p.inventory = [Item.from_dict(x) for x in d.get("inventory", [])]
        p.potions = d.get("potions", {"Health Potion": 3, "Mana Potion": 2})
        p.max_depth_cleared = d.get("max_depth_cleared", 0)
        p.total_kills = d.get("total_kills", 0)
        p.total_gold_earned = d.get("total_gold_earned", 0)
        p.lore_found = d.get("lore_found", [])
        p.paragon = d.get("paragon", 0)
        p.world_day = d.get("world_day", 1)
        p.world_time_index = d.get("world_time_index", random.randrange(len(WORLD_TIMES)))
        p.world_weather = d.get("world_weather", random.choice(WORLD_WEATHER))
        p.world_omen = d.get("world_omen", random.choice(WORLD_OMENS))
        p.story_flags = d.get("story_flags", [])
        p.rumor_progress = d.get("rumor_progress", {})
        p.last_expedition = d.get("last_expedition", {})
        p.hp = min(d.get("hp", p.max_hp), p.max_hp)
        p.mp = min(d.get("mp", p.max_mp), p.max_mp)
        p.status_effects = []; p.defending = False; p.dodge_next = False
        return p


# ═══════════════════════════════════════════════════════════════
#  ENEMY
# ═══════════════════════════════════════════════════════════════

class Enemy:
    def __init__(self, name, hp, atk, dfn, xp, gold, abilities, depth, is_boss=False, taunt="", intro=None):
        s = 1 + (depth - 1) * 0.18
        self.name = name
        self.max_hp = int(hp * s)
        self.hp = self.max_hp
        self.atk = int(atk * s)
        self.dfn = int(dfn * s * 0.7)
        self.base_xp = int(xp * s)
        self.gold_range = (int(gold[0] * s), int(gold[1] * s))
        self.abilities = abilities
        self.is_boss = is_boss
        self.taunt = taunt
        self.intro = intro or []
        self.status_effects = []
        self.frenzy_active = False
        self.depth = depth

    def take_damage(self, raw):
        red = self.dfn / (self.dfn + 40)
        actual = max(1, int(raw * (1 - red)))
        self.hp = max(0, self.hp - actual)
        return actual

    def is_alive(self):
        return self.hp > 0

    def get_attack_damage(self):
        base = self.atk
        if "frenzy" in self.abilities and self.hp < self.max_hp * 0.3:
            if not self.frenzy_active:
                self.frenzy_active = True
            base = int(base * 1.5)
        if "heavy" in self.abilities and random.random() < 0.25:
            return int(base * 1.8), "heavy"
        return base + random.randint(-2, 2), "normal"

    def get_special(self):
        """Return a special ability to use, or None."""
        if "poison" in self.abilities and random.random() < 0.25:
            return "poison"
        if "fear" in self.abilities and random.random() < 0.2:
            return "fear"
        if "regen" in self.abilities:
            heal_amt = int(self.max_hp * 0.05)
            self.hp = min(self.max_hp, self.hp + heal_amt)
            return ("regen", heal_amt)
        return None

    def apply_status_tick(self):
        msgs = []
        new = []
        for e in self.status_effects:
            if e.get("dot"):
                self.hp = max(0, self.hp - e["dot"])
                msgs.append(co(f"  {self.name} takes {e['dot']} {e['name']} damage!", C.BRED))
            e["turns"] -= 1
            if e["turns"] > 0:
                new.append(e)
        self.status_effects = new
        return msgs

    def drop_gold(self):
        g = random.randint(self.gold_range[0], self.gold_range[1])
        return g


def make_enemy(depth):
    if depth <= 3:
        tier = 1
    elif depth <= 7:
        tier = random.choices([1, 2], weights=[30, 70])[0]
    elif depth <= 12:
        tier = random.choices([1, 2, 3], weights=[10, 50, 40])[0]
    elif depth <= 18:
        tier = random.choices([2, 3, 4], weights=[15, 50, 35])[0]
    elif depth <= 25:
        tier = random.choices([2, 3, 4, 5], weights=[5, 25, 45, 25])[0]
    else:
        tier = random.choices([3, 4, 5], weights=[15, 40, 45])[0]
    template = random.choice(ENEMIES_BY_TIER[tier])
    return Enemy(template["name"], template["hp"], template["atk"], template["dfn"],
                 template["xp"], template["gold"], list(template["abilities"]), depth)


def make_boss(depth):
    idx = ((depth // 5) - 1) % len(BOSSES)
    b = BOSSES[idx]
    extra_scale = 1 + max(0, (depth // 5) - len(BOSSES)) * 0.25
    return Enemy(b["name"], int(b["hp"] * extra_scale), int(b["atk"] * extra_scale),
                 b["dfn"], int(b["xp"] * extra_scale), b["gold"],
                 list(b["abilities"]), depth, is_boss=True, taunt=b["taunt"], intro=b.get("intro", []))


# ═══════════════════════════════════════════════════════════════
#  COMBAT ENGINE
# ═══════════════════════════════════════════════════════════════

class Combat:
    def __init__(self, player, enemy):
        self.p = player
        self.e = enemy
        self.turn = 0
        self.log = []
        self.fled = False

    def display(self):
        clr()
        w = W()
        hdr("⚔  COMBAT  ⚔", C.BRED)
        # Enemy info
        boss_tag = co(" [BOSS]", C.BYEL) if self.e.is_boss else ""
        frenzy_tag = co(" [FRENZIED!]", C.BRED) if self.e.frenzy_active else ""
        print(f"\n  {co(self.e.name, C.BRED)}{boss_tag}{frenzy_tag}")
        print(f"  HP: {hp_bar(self.e.hp, self.e.max_hp)}")
        if self.e.status_effects:
            effs = ", ".join(co(e["name"], C.MAG) for e in self.e.status_effects)
            print(f"  Effects: {effs}")
        sep()
        # Player info
        print(f"  {co(self.p.name, C.BGRN)} — {self.p.cls} (Lvl {self.p.level})")
        print(f"  HP: {hp_bar(self.p.hp, self.p.max_hp)}")
        print(f"  MP: {mp_bar(self.p.mp, self.p.max_mp)}")
        if self.p.status_effects:
            effs = ", ".join(co(e["name"], C.MAG) for e in self.p.status_effects)
            print(f"  Effects: {effs}")
        sep()
        # Combat log (last 4)
        for msg in self.log[-4:]:
            print(msg)
        print()

    def player_turn(self):
        skills = CLASSES[self.p.cls]["skills"]
        opts = ["Attack"]
        for sk in skills:
            cost_color = C.GRN if self.p.mp >= sk["cost"] else C.RED
            sk_cost = sk["cost"]
            sk_name = sk["name"]
            opts.append(f'{sk_name} ({co(str(sk_cost) + " MP", cost_color)})')
        opts.append("Use Potion")
        opts.append("Defend")
        if not self.e.is_boss:
            opts.append(co("Flee", C.YEL))

        ch = get_choice(opts)

        if ch == 0:  # Attack
            dmg, crit = self.p.calc_damage()
            actual = self.e.take_damage(dmg)
            crit_txt = co(" CRITICAL!", C.BYEL) if crit else ""
            self.log.append(f"  You strike for {co(str(actual), C.BGRN)} damage!{crit_txt}")

        elif 1 <= ch <= 3:  # Skills
            sk = skills[ch - 1]
            if self.p.mp < sk["cost"]:
                self.log.append(co("  Not enough mana!", C.RED))
                return self.player_turn()
            self.p.mp -= sk["cost"]
            self._execute_skill(sk)

        elif ch == len(opts) - 3 + (0 if self.e.is_boss else 0):
            # This is "Use Potion" — position varies
            if ch == 4:
                self._use_potion()
                return
            # else fallthrough detect
            if opts[ch].startswith("Use"):
                self._use_potion()
                return
            elif opts[ch].startswith("Defend") or "Defend" in opts[ch]:
                self.p.defending = True
                self.log.append(co("  You raise your guard, bracing for impact!", C.BLU))
            else:
                self._handle_action(opts, ch)
                return
        else:
            self._handle_action(opts, ch)
            return

    def _handle_action(self, opts, ch):
        label = opts[ch] if ch < len(opts) else ""
        if isinstance(label, str) and "Flee" in label:
            if random.random() < 0.6:
                self.log.append(co("  You disengage and flee!", C.YEL))
                self.fled = True
            else:
                self.log.append(co("  You fail to escape!", C.RED))
        elif "Defend" in str(label):
            self.p.defending = True
            self.log.append(co("  You raise your guard, bracing for impact!", C.BLU))
        elif "Potion" in str(label) or "Use" in str(label):
            self._use_potion()

    def _execute_skill(self, sk):
        t = sk["type"]
        if t == "damage":
            mult = sk["mult"]
            ac = sk.get("auto_crit", False)
            dmg, crit = self.p.calc_damage(mult=mult, auto_crit=ac, skill_key="sk1" if sk == CLASSES[self.p.cls]["skills"][0] else ("sk3" if sk == CLASSES[self.p.cls]["skills"][2] else None))
            actual = self.e.take_damage(dmg)
            crit_txt = co(" CRITICAL!", C.BYEL) if crit else ""
            self.log.append(f"  {co(sk['name'], C.CYN)} deals {co(str(actual), C.BGRN)} damage!{crit_txt}")
            if sk.get("stun") and random.random() < sk["stun"]:
                self.e.status_effects.append({"name": "Stunned", "turns": 2})
                self.log.append(co(f"  {self.e.name} is STUNNED!", C.BYEL))

        elif t == "magic":
            mult = sk["mult"]
            sk_key = "sk1" if sk == CLASSES[self.p.cls]["skills"][0] else ("sk3" if sk == CLASSES[self.p.cls]["skills"][2] else None)
            dmg, crit = self.p.calc_damage(mult=mult, is_magic=True, skill_key=sk_key)
            actual = self.e.take_damage(dmg)
            crit_txt = co(" CRITICAL!", C.BYEL) if crit else ""
            self.log.append(f"  {co(sk['name'], C.CYN)} incinerates for {co(str(actual), C.BGRN)} damage!{crit_txt}")
            # Cauterize lifesteal
            ls = self.p.get_talent_bonus("lifesteal")
            if ls > 0 and sk == CLASSES[self.p.cls]["skills"][0]:
                heal_amt = int(actual * ls / 100)
                self.p.heal(heal_amt)
                self.log.append(co(f"  Cauterize heals you for {heal_amt} HP!", C.GRN))

        elif t == "heal":
            pct = sk["pct"]
            sk2_bonus = self.p.get_talent_bonus("sk2")
            heal = int(self.p.max_hp * pct * (1 + sk2_bonus / 100))
            self.p.heal(heal)
            self.log.append(co(f"  {sk['name']} restores {heal} HP!", C.GRN))
            if sk.get("buff"):
                b = sk["buff"]
                self.p.status_effects.append({"name": b[0], "turns": b[1], "damage_bonus": b[2]})
                self.log.append(co(f"  You are {b[0]}! (+{int(b[2]*100)}% damage for {b[1]} turns)", C.CYN))

        elif t == "grudge":
            hp_pct = 1 - (self.p.hp / self.p.max_hp) if self.p.max_hp > 0 else 0
            mult = sk["base_mult"] + hp_pct * 1.5
            dmg, crit = self.p.calc_damage(mult=mult, skill_key="sk1")
            actual = self.e.take_damage(dmg)
            crit_txt = co(" CRITICAL!", C.BYEL) if crit else ""
            self.log.append(f"  {co(sk['name'], C.CYN)} strikes for {co(str(actual), C.BGRN)} damage!{crit_txt}")

        elif t == "buff_self":
            b = sk["buff"]
            extra_turns = self.p.get_talent_bonus("sk2_turns") if "sk2_turns" in [t[3] for t in TALENTS[self.p.cls]] else 0
            turns = b[1] + extra_turns
            self.p.status_effects.append({"name": b[0], "turns": turns, "value": b[2]})
            self.log.append(co(f"  {b[0]} activated for {turns} turns!", C.CYN))
            if sk.get("reflect"):
                self.log.append(co(f"  Enemies that strike you take fire damage!", C.RED))

        elif t == "dodge_strike":
            self.p.dodge_next = True
            dmg, crit = self.p.calc_damage(mult=sk["mult"])
            actual = self.e.take_damage(dmg)
            self.log.append(f"  {co(sk['name'], C.CYN)} strikes for {co(str(actual), C.BGRN)} damage!")
            self.log.append(co("  You melt into shadow — dodging the next attack!", C.CYN))
            sk2_heal = self.p.get_talent_bonus("sk2_heal")
            if sk2_heal > 0:
                h = int(self.p.max_hp * sk2_heal / 100)
                self.p.heal(h)
                self.log.append(co(f"  Shadow Dance heals {h} HP!", C.GRN))

        elif t == "multi":
            total = 0
            hits = sk["hits"] + self.p.get_talent_bonus("sk3_hits")
            for i in range(hits):
                dmg, crit = self.p.calc_damage(mult=sk["mult"])
                actual = self.e.take_damage(dmg)
                total += actual
            self.log.append(f"  {co(sk['name'], C.CYN)}: {hits} arrows for {co(str(total), C.BGRN)} total damage!")

    def _use_potion(self):
        available = {k: v for k, v in self.p.potions.items() if v > 0}
        if not available:
            self.log.append(co("  No potions available!", C.RED))
            return
        print(f"\n  {co('Potions:', C.YEL)}")
        pot_list = list(available.keys())
        opts = [f"{name} (x{available[name]}) - {POTION_TYPES[name]['desc']}" for name in pot_list]
        opts.append("Cancel")
        ch = get_choice(opts)
        if ch >= len(pot_list):
            return
        pname = pot_list[ch]
        pt = POTION_TYPES[pname]
        self.p.potions[pname] -= 1
        if pt["type"] == "heal":
            heal = int(self.p.max_hp * pt["value"])
            self.p.heal(heal)
            self.log.append(co(f"  Drank {pname}! Restored {heal} HP.", C.GRN))
        elif pt["type"] == "mana":
            amt = int(self.p.max_mp * pt["value"])
            self.p.restore_mp(amt)
            self.log.append(co(f"  Drank {pname}! Restored {amt} MP.", C.BLU))
        elif pt["type"] == "cure":
            self.p.status_effects = [e for e in self.p.status_effects if e["name"] != "Poison"]
            self.log.append(co(f"  Antidote neutralises the poison!", C.GRN))
        elif pt["type"] == "buff_str":
            self.p.status_effects.append({"name": "Might", "turns": pt["turns"], "damage_bonus": 0.2})
            self.log.append(co(f"  Elixir of Might! +STR for {pt['turns']} turns.", C.YEL))
        elif pt["type"] == "buff_def":
            self.p.status_effects.append({"name": "Ironbark", "turns": pt["turns"], "value": 0.2})
            self.log.append(co(f"  Ironbark Tonic! +DEF for {pt['turns']} turns.", C.BLU))

    def enemy_turn(self):
        if not self.e.is_alive():
            return
        # Check stun
        stunned = False
        for e in self.e.status_effects:
            if e["name"] == "Stunned":
                self.log.append(co(f"  {self.e.name} is stunned and cannot act!", C.BYEL))
                stunned = True
                break
        if stunned:
            return

        # Check frenzy notification
        if self.e.frenzy_active and self.turn == 0:
            pass  # already shown
        if "frenzy" in self.e.abilities and self.e.hp < self.e.max_hp * 0.3 and not self.e.frenzy_active:
            self.e.frenzy_active = True
            self.log.append(co(f"  {self.e.name} flies into a FRENZY!", C.BRED))

        # Special abilities
        spec = self.e.get_special()
        if spec == "poison":
            dmg, _ = self.e.get_attack_damage()
            actual, result = self.p.take_damage(dmg)
            if result == "dodged":
                self.log.append(co(f"  {self.e.name}'s poisoned attack misses! You dodged!", C.BGRN))
            elif result == "blocked":
                self.log.append(co(f"  You block {self.e.name}'s poisoned attack!", C.BGRN))
            else:
                self.log.append(f"  {co(self.e.name, C.RED)} poisons you for {co(str(actual), C.RED)} damage!")
                if not any(e["name"] == "Poison" for e in self.p.status_effects):
                    dot = max(2, int(self.e.atk * 0.15))
                    self.p.status_effects.append({"name": "Poison", "turns": 3, "dot": dot})
                    self.log.append(co(f"  You are POISONED! ({dot} dmg/turn for 3 turns)", C.MAG))
                if isinstance(result, int) and result > 0:
                    self.log.append(co(f"  Flame Shield reflects {result} damage!", C.RED))
                    self.e.hp = max(0, self.e.hp - result)
        elif spec == "fear":
            self.log.append(co(f"  {self.e.name}'s terrifying presence chills your blood!", C.MAG))
            r = self.p.get_talent_bonus("resist")
            if random.random() * 100 >= r:
                self.p.status_effects.append({"name": "Fear", "turns": 2, "damage_bonus": -0.15})
                self.log.append(co("  You are gripped by FEAR! (-15% damage for 2 turns)", C.MAG))
            else:
                self.log.append(co("  But you resist the fear!", C.BGRN))
        elif isinstance(spec, tuple) and spec[0] == "regen":
            self.log.append(co(f"  {self.e.name} regenerates {spec[1]} HP!", C.MAG))
            # Still attacks
            dmg, hit_type = self.e.get_attack_damage()
            actual, result = self.p.take_damage(dmg)
            if result == "dodged":
                self.log.append(co(f"  {self.e.name} attacks but you dodge!", C.BGRN))
            elif result == "blocked":
                self.log.append(co(f"  You block {self.e.name}'s attack!", C.BGRN))
            else:
                ht = co(" HEAVY BLOW!", C.BYEL) if hit_type == "heavy" else ""
                self.log.append(f"  {co(self.e.name, C.RED)} strikes for {co(str(actual), C.RED)} damage!{ht}")
                if isinstance(result, int) and result > 0:
                    self.log.append(co(f"  Flame Shield reflects {result} damage!", C.RED))
                    self.e.hp = max(0, self.e.hp - result)
        else:
            # Normal attack
            dmg, hit_type = self.e.get_attack_damage()
            actual, result = self.p.take_damage(dmg)
            if result == "dodged":
                self.log.append(co(f"  {self.e.name} attacks but you dodge!", C.BGRN))
            elif result == "blocked":
                self.log.append(co(f"  You block {self.e.name}'s attack with your shield!", C.BGRN))
            else:
                ht = co(" HEAVY BLOW!", C.BYEL) if hit_type == "heavy" else ""
                self.log.append(f"  {co(self.e.name, C.RED)} strikes for {co(str(actual), C.RED)} damage!{ht}")
                if isinstance(result, int) and result > 0:
                    self.log.append(co(f"  Flame Shield reflects {result} damage!", C.RED))
                    self.e.hp = max(0, self.e.hp - result)

    def run(self):
        if self.e.taunt:
            self.log.append(co(f'  "{self.e.taunt}"', C.BRED))
        while self.p.is_alive() and self.e.is_alive() and not self.fled:
            self.display()
            # Player turn
            self.player_turn()
            if self.fled:
                break
            if not self.e.is_alive():
                break
            # Enemy turn
            self.enemy_turn()
            # Status ticks
            msgs = self.p.apply_status_tick()
            self.log.extend(msgs)
            msgs = self.e.apply_status_tick()
            self.log.extend(msgs)
            # Damage bonus from status effects
            self.turn += 1

        self.display()
        if self.fled:
            return "fled"
        elif not self.p.is_alive():
            return "defeat"
        else:
            return "victory"


# ═══════════════════════════════════════════════════════════════
#  DUNGEON
# ═══════════════════════════════════════════════════════════════

class Dungeon:
    def __init__(self, player, depth):
        self.p = player
        self.depth = depth
        self.rooms = self._generate_rooms()
        self.current_room = 0
        self.kills = 0
        self.gold_found = 0
        self.items_found = []
        self.lore_found_this_run = []

    def _generate_rooms(self):
        n = random.randint(4, 6)
        rooms = []
        for i in range(n):
            rtype = random.choice(ROOM_TYPES)
            weights = [40, 15, 15, 10, 10, 10]
            events = ["combat", "treasure", "trap", "shrine", "event", "empty"]
            event = random.choices(events, weights=weights)[0]
            rooms.append({"type": rtype, "event": event, "index": i + 1})
        # Boss room
        is_boss_depth = (self.depth % 5 == 0)
        boss_event = "boss" if is_boss_depth else "miniboss"
        rooms.append({"type": "Boss Chamber", "event": boss_event, "index": n + 1})
        return rooms

    def _show_dungeon_status(self, room_type=""):
        print(f"  {co(self.p.name, C.BGRN)} — Lvl {self.p.level}  |  {co(f'Depth {self.depth}', C.BYEL)}  |  Room {self.current_room + 1}/{len(self.rooms)}")
        print(f"  HP: {hp_bar(self.p.hp, self.p.max_hp)}")
        print(f"  MP: {mp_bar(self.p.mp, self.p.max_mp)}")
        print(f"  {co('Depth Mood:', C.BRED)} {co(get_depth_mood(self.depth), C.GRY)}")
        print(f"  {co('Time Below:', C.CYN)} {co(f'Day {self.p.world_day}, {self.p.world_time}', C.GRY)}")
        sep()
        room_lines = ROOM_AMBIENCE.get(room_type, [])
        if room_lines:
            print(co(f"  ~ {random.choice(room_lines)}", C.GRY))
        else:
            print(co("  ~ The stone remembers old blood and older oaths.", C.GRY))
        if self.depth >= 15:
            print(random.choice(AMBIENT_DEEP))
        else:
            print(random.choice(AMBIENT_DUNGEON))
        sep()

    def run(self):
        clr()
        hdr(f"ENTERING THE DEPTHS — LEVEL {self.depth}", C.BRED)
        print()
        if self.depth >= 15:
            wrap("The air grows thick with dread as you descend into the deeper levels. "
                 "Chaos energy crackles in the stones. Even the bravest warriors think twice before venturing this far.", C.RED)
        else:
            wrap("You light your torch and descend into the darkness below Ubersreik. "
                 "The entrance gives way to ancient passages carved long before the Empire. Stay alert.", C.GRY)
        pause()

        for i, room in enumerate(self.rooms):
            self.current_room = i
            clr()
            hdr(f"DEPTH {self.depth} — {room['type'].upper()}", C.BRED)
            print()
            self._show_dungeon_status(room["type"])
            print()
            wrap(f"You enter a {room['type'].lower()}...", C.WHT)
            print()

            result = self._run_room(room)
            if result == "dead":
                return self._end_run(False)
            elif result == "flee_dungeon":
                print(co("\n  You retreat back to the surface.", C.YEL))
                pause()
                return self._end_run(False, fled=True)
            elif result == "fled_room":
                # Fled from combat, skip rest of room
                continue

            if not self.p.is_alive():
                return self._end_run(False)

            if i < len(self.rooms) - 1:
                print(f"\n  {co('Continue deeper or retreat to town?', C.YEL)}")
                ch = get_choice(["Continue deeper", "Retreat to town"])
                if ch == 1:
                    print(co("\n  You retreat back to the surface.", C.YEL))
                    pause()
                    return self._end_run(False, fled=True)

        # Cleared all rooms
        return self._end_run(True)

    def _run_room(self, room):
        ev = room["event"]
        if ev == "combat":
            return self._combat()
        elif ev == "boss":
            return self._boss()
        elif ev == "miniboss":
            return self._miniboss()
        elif ev == "treasure":
            return self._treasure()
        elif ev == "trap":
            return self._trap()
        elif ev == "shrine":
            return self._shrine()
        elif ev == "event":
            return self._event()
        else:
            return self._empty()

    def _combat(self):
        enemy = make_enemy(self.depth)
        wrap(f"A {enemy.name} emerges from the shadows!", C.RED)
        pause("Press Enter to fight...")
        result = Combat(self.p, enemy).run()
        if result == "victory":
            return self._victory_rewards(enemy)
        elif result == "fled":
            return "fled_room"
        else:
            return "dead"

    def _boss(self):
        boss = make_boss(self.depth)
        clr()
        hdr(f"⚔  BOSS: {boss.name.upper()}  ⚔", C.BYEL)
        print()
        wrap(f"A massive presence fills the chamber. {boss.name} bars your path!", C.BRED)
        if boss.intro:
            wrap(random.choice(boss.intro), C.MAG)
        if self.depth >= 20:
            wrap("The stones tremble with distant chanting as if the dungeon itself is watching.", C.RED)
        print()
        pause("Press Enter to face the boss...")
        result = Combat(self.p, boss).run()
        if result == "victory":
            return self._victory_rewards(boss, is_boss=True)
        else:
            return "dead"

    def _miniboss(self):
        # Stronger-than-normal enemy
        enemy = make_enemy(self.depth)
        enemy.max_hp = int(enemy.max_hp * 1.6)
        enemy.hp = enemy.max_hp
        enemy.atk = int(enemy.atk * 1.3)
        enemy.base_xp = int(enemy.base_xp * 1.5)
        enemy.gold_range = (int(enemy.gold_range[0] * 1.4), int(enemy.gold_range[1] * 1.4))
        enemy.name = f"Champion {enemy.name}"
        wrap(f"A powerful {enemy.name} stands guard at the end of this level!", C.RED)
        pause("Press Enter to fight...")
        result = Combat(self.p, enemy).run()
        if result == "victory":
            return self._victory_rewards(enemy, is_boss=True)
        elif result == "fled":
            return "flee_dungeon"
        else:
            return "dead"

    def _victory_rewards(self, enemy, is_boss=False):
        gold = enemy.drop_gold()
        gold_bonus = 0
        for it in self.p.equipment.values():
            if it and "+15% Gold Find" in (it.special or ""):
                gold_bonus += 15
        gold = int(gold * (1 + gold_bonus / 100))
        self.p.gold += gold
        self.p.total_gold_earned += gold
        self.p.total_kills += 1
        self.kills += 1
        self.gold_found += gold

        leveled = self.p.gain_xp(enemy.base_xp)

        print(f"\n  {co('VICTORY!', C.BGRN)}")
        print(f"  +{co(str(enemy.base_xp), C.CYN)} XP  |  +{co(str(gold), C.YEL)} Gold")
        if leveled:
            print(f"\n  {co('★ LEVEL UP! ★', C.BYEL)} You are now level {self.p.level}!")
            if self.p.level <= 25:
                print(co(f"  +1 Talent Point available!", C.CYN))
            else:
                print(co(f"  Paragon +1! ({self.p.paragon} total)", C.BYEL))

        # Item drop
        drop_chance = 0.35 if not is_boss else 0.85
        rarity_bonus = 0
        for it in self.p.equipment.values():
            if it and "Lucky" in (it.special or ""):
                rarity_bonus += 8
        if random.random() < drop_chance:
            item = generate_item(self.depth)
            print(f"\n  {co('Item dropped:', C.YEL)} {item.display_name()}")
            print(f"    {item.stat_line()}")
            ch = get_choice(["Pick up", "Leave it"])
            if ch == 0:
                if len(self.p.inventory) < 20:
                    self.p.inventory.append(item)
                    self.items_found.append(item)
                    print(co("  Added to inventory.", C.GRN))
                else:
                    print(co("  Inventory full! Item left behind.", C.RED))

        # Boss bonus drop
        if is_boss:
            bonus_item = generate_item(self.depth, rarity=random.choice(["Rare", "Epic", "Legendary"]))
            print(f"\n  {co('Boss Bonus Drop:', C.BYEL)} {bonus_item.display_name()}")
            print(f"    {bonus_item.stat_line()}")
            ch = get_choice(["Pick up", "Leave it"])
            if ch == 0:
                if len(self.p.inventory) < 20:
                    self.p.inventory.append(bonus_item)
                    self.items_found.append(bonus_item)
                    print(co("  Added to inventory.", C.GRN))
                else:
                    print(co("  Inventory full!", C.RED))

        # Lore drop
        if random.random() < 0.15:
            entry = pick_lore_entry(self.p, self.depth)
            if entry:
                self.p.lore_found.append(entry[0])
                self.lore_found_this_run.append(entry)
                print(f"\n  {co('📜 Lore Discovered:', C.BCYN)} {co(entry[0], C.CYN)}")
                wrap(entry[1], C.CYN)

        # Kill milestone messages
        k = self.p.total_kills
        milestones = {10: "You're getting the hang of this.",
                      50: "The creatures of the dark fear your name.",
                      100: "You are a seasoned warrior of the depths.",
                      250: "Songs are sung of your deeds in taverns across the Reikland.",
                      500: "Even the Chaos Gods take notice of your prowess.",
                      1000: "You are a living legend. The Old World trembles."}
        if k in milestones:
            print(f"\n  {co('★', C.BYEL)} {co(milestones[k], C.BYEL)}")

        pause()
        return "continue"

    def _treasure(self):
        wrap("You discover a hidden cache!", C.YEL)
        gold = random.randint(10, 25) + int(self.depth * 3.5)
        self.p.gold += gold
        self.p.total_gold_earned += gold
        self.gold_found += gold
        print(f"  +{co(str(gold), C.YEL)} Gold")

        if random.random() < 0.5:
            item = generate_item(self.depth)
            print(f"  {co('You find:', C.YEL)} {item.display_name()}")
            print(f"    {item.stat_line()}")
            ch = get_choice(["Take it", "Leave it"])
            if ch == 0 and len(self.p.inventory) < 20:
                self.p.inventory.append(item)
                self.items_found.append(item)
            elif ch == 0:
                print(co("  Inventory full!", C.RED))

        if random.random() < 0.3:
            potion = random.choice(["Health Potion", "Mana Potion"])
            self.p.potions[potion] = self.p.potions.get(potion, 0) + 1
            print(f"  Found a {co(potion, C.GRN)}!")

        pause()
        return "continue"

    def _trap(self):
        traps = [
            ("A hidden spike trap springs from the floor!", "agi"),
            ("Poison darts fire from the walls!", "agi"),
            ("The ceiling begins to collapse!", "tou"),
            ("A Warpstone cage crackles with dark energy!", "wil"),
            ("An ancient glyph explodes as you step on it!", "int"),
        ]
        trap = random.choice(traps)
        wrap(trap[0], C.RED)
        stat = trap[1]
        val = self.p.stats[stat]
        dc = 4 + self.depth
        roll = random.randint(1, 12) + val

        if roll >= dc:
            print(co(f"  Your {stat.upper()} saves you! You avoid the trap.", C.BGRN))
        else:
            dmg = random.randint(8, 15) + self.depth * 2
            self.p.hp = max(1, self.p.hp - dmg)
            print(co(f"  You take {dmg} damage from the trap!", C.RED))
            if "Poison" in trap[0] or "Warpstone" in trap[0]:
                self.p.status_effects.append({"name": "Poison", "turns": 3, "dot": max(2, self.depth)})
                print(co("  You are poisoned!", C.MAG))
        pause()
        return "continue"

    def _shrine(self):
        shrines = [
            ("A shrine to Sigmar radiates golden light.",
             "Sigmar's Blessing: +20% damage for 5 turns",
             {"name": "Sigmar's Blessing", "turns": 8, "damage_bonus": 0.2}),
            ("A Dwarfen rune stone hums with ancient power.",
             "Ancestral Ward: +30% damage reduction for 5 turns",
             {"name": "Ancestral Ward", "turns": 8, "value": 0.3}),
            ("A pool of luminous water glows softly.",
             "Waters of Life: Fully restores HP",
             "full_heal_hp"),
            ("Ancient Elven waystone resonates with natural energy.",
             "Nature's Gift: Restores all MP",
             "full_heal_mp"),
            ("A statue of Morr, god of the dead, watches silently.",
             "Morr's Protection: Immune to fear for this depth",
             {"name": "Morr's Shield", "turns": 20}),
        ]
        shrine = random.choice(shrines)
        wrap(shrine[0], C.CYN)
        print(f"\n  {co(shrine[1], C.BCYN)}")
        ch = get_choice(["Accept the blessing", "Move on"])
        if ch == 0:
            if shrine[2] == "full_heal_hp":
                self.p.hp = self.p.max_hp
                print(co("  Your wounds close and strength returns!", C.GRN))
            elif shrine[2] == "full_heal_mp":
                self.p.mp = self.p.max_mp
                print(co("  Magical energy floods through you!", C.BLU))
            else:
                self.p.status_effects.append(dict(shrine[2]))
                print(co("  You feel the blessing take hold!", C.CYN))
        pause()
        return "continue"

    def _event(self):
        events = [
            self._event_merchant,
            self._event_wounded_soldier,
            self._event_lore_stone,
            self._event_mysterious_chest,
            self._event_lost_traveller,
        ]
        return random.choice(events)()

    def _event_merchant(self):
        wrap("A hooded figure sits by a small fire. 'Psst! Want to buy something, friend?'", C.YEL)
        items = [generate_item(self.depth) for _ in range(3)]
        costs = [max(15, int(it.power_score() * 2.5 + 10)) for it in items]
        while True:
            opts = []
            for it, cost in zip(items, costs):
                status = f" {co(f'[{cost}g]', C.YEL)}" if cost <= self.p.gold else f" {co(f'[{cost}g]', C.RED)}"
                opts.append(f"{it.display_name()}{status} — {it.stat_line()}")
            opts.append("Leave")
            print(f"\n  Your gold: {co(str(self.p.gold), C.YEL)}")
            ch = get_choice(opts)
            if ch >= len(items):
                break
            if costs[ch] > self.p.gold:
                print(co("  Not enough gold!", C.RED))
                continue
            if len(self.p.inventory) >= 20:
                print(co("  Inventory full!", C.RED))
                continue
            self.p.gold -= costs[ch]
            self.p.inventory.append(items[ch])
            print(co(f"  Purchased {items[ch].name}!", C.GRN))
            items.pop(ch)
            costs.pop(ch)
            if not items:
                break
        return "continue"

    def _event_wounded_soldier(self):
        wrap("You find a wounded Empire soldier slumped against the wall. "
             "'Please... water...' he gasps.", C.YEL)
        ch = get_choice(["Help him (Spend 1 Health Potion)", "Leave him"])
        if ch == 0:
            if self.p.potions.get("Health Potion", 0) > 0:
                self.p.potions["Health Potion"] -= 1
                reward = random.choice(["gold", "info", "item"])
                if reward == "gold":
                    g = 20 + self.depth * 5
                    self.p.gold += g
                    print(co(f"  'Thank you, friend. Take this.' (+{g} gold)", C.GRN))
                elif reward == "info":
                    print(co("  'The boss ahead is weak to... persistent attacks. Don't give up.'", C.CYN))
                    self.p.status_effects.append({"name": "Soldier's Insight", "turns": 15, "damage_bonus": 0.1})
                    print(co("  +10% damage for this depth!", C.CYN))
                    self.p.set_story_flag("heard_soldier_warning")
                else:
                    item = generate_item(self.depth, rarity="Uncommon")
                    print(f"  'Take my {item.display_name()}. I won't need it where I'm going.'")
                    if len(self.p.inventory) < 20:
                        self.p.inventory.append(item)
                self.p.set_story_flag("helped_wounded_soldier")
            else:
                print(co("  You have no potions to spare.", C.RED))
        else:
            print(co("  You leave the soldier behind. His eyes follow you into the dark.", C.GRY))
            self.p.set_story_flag("left_wounded_soldier")
        pause()
        return "continue"

    def _event_lore_stone(self):
        entry = pick_lore_entry(self.p, self.depth)
        if entry:
            self.p.lore_found.append(entry[0])
            self.lore_found_this_run.append(entry)
            wrap("You discover ancient text carved into a standing stone...", C.CYN)
            print(f"\n  {co('📜 ' + entry[0], C.BCYN)}")
            wrap(entry[1], C.CYN)
        else:
            wrap("You find a standing stone, but you've read these runes before. "
                 "You press on.", C.GRY)
        pause()
        return "continue"

    def _event_mysterious_chest(self):
        wrap("A heavy iron chest sits in the center of the room. "
             "It might be trapped... or it might hold treasure.", C.YEL)
        ch = get_choice(["Open it", "Leave it"])
        if ch == 0:
            if random.random() < 0.6:
                item = generate_item(self.depth, rarity=random.choice(["Uncommon", "Rare", "Epic"]))
                print(f"\n  {co('Treasure!', C.BYEL)} {item.display_name()}")
                print(f"    {item.stat_line()}")
                if len(self.p.inventory) < 20:
                    self.p.inventory.append(item)
                    self.items_found.append(item)
                else:
                    print(co("  Inventory full!", C.RED))
            else:
                dmg = random.randint(10, 20) + self.depth
                self.p.hp = max(1, self.p.hp - dmg)
                print(co(f"  It was trapped! You take {dmg} damage!", C.RED))
        pause()
        return "continue"

    def _event_lost_traveller(self):
        wrap("A frightened merchant cowers in the corner. 'Please, help me find the way out!'", C.YEL)
        ch = get_choice(["Escort him (+Gold reward)", "Point him to the exit", "Ignore him"])
        if ch == 0:
            g = 30 + self.depth * 4
            self.p.gold += g
            self.p.total_gold_earned += g
            print(co(f"  'Bless you! Here, take this!' (+{g} gold)", C.GRN))
            self.p.set_story_flag("escorted_lost_traveller")
        elif ch == 1:
            print(co("  'Thank you, stranger. May Sigmar protect you.'", C.GRY))
            # Small chance of a bonus
            if random.random() < 0.3:
                print(co("  He leaves behind a small pouch of coins.", C.YEL))
                self.p.gold += 15
            self.p.set_story_flag("guided_lost_traveller")
        else:
            print(co("  You walk past. His sobbing fades behind you.", C.GRY))
            self.p.set_story_flag("ignored_lost_traveller")
        pause()
        return "continue"

    def _empty(self):
        descs = [
            "The room is empty save for rubble and shadows.",
            "Nothing here but dust and the echoes of your footsteps.",
            "Old cobwebs drape the ceiling. Nothing of interest.",
            "The room holds only silence and the scent of damp stone.",
            "Broken furniture and shattered pottery litter the floor.",
        ]
        wrap(random.choice(descs), C.GRY)
        if random.random() < 0.3:
            gold = random.randint(3, 10) + self.depth
            self.p.gold += gold
            self.p.total_gold_earned += gold
            self.gold_found += gold
            print(co(f"  You find {gold} gold in a hidden corner.", C.YEL))
        pause()
        return "continue"

    def _end_run(self, cleared, fled=False):
        clr()
        if not self.p.is_alive():
            hdr("DEFEAT", C.RED)
            print()
            wrap("Darkness takes you... You awaken at the tavern in Ubersreik. "
                 "The barkeep shakes his head sadly.", C.RED)
            lost = self.p.gold // 3
            self.p.gold -= lost
            self.p.full_heal()
            print(co(f"\n  Lost {lost} gold.", C.RED))
        elif cleared:
            hdr("DEPTH CLEARED!", C.BGRN)
            print()
            if self.depth > self.p.max_depth_cleared:
                self.p.max_depth_cleared = self.depth
                print(co(f"  New record! Max depth: {self.depth}", C.BYEL))
            print(co(f"  Title: {get_title(self.p.max_depth_cleared)}", C.BYEL))
        else:
            hdr("RETREAT", C.YEL)

        sep()
        print(f"  Enemies slain:  {co(str(self.kills), C.RED)}")
        print(f"  Gold found:     {co(str(self.gold_found), C.YEL)}")
        print(f"  Items found:    {co(str(len(self.items_found)), C.GRN)}")
        if self.lore_found_this_run:
            print(f"  Lore discovered: {co(str(len(self.lore_found_this_run)), C.CYN)}")
        sep()
        self.p.last_expedition = {
            "depth": self.depth,
            "outcome": "Cleared" if cleared else ("Defeat" if not self.p.is_alive() else "Retreated"),
            "kills": self.kills,
            "gold": self.gold_found,
            "items": len(self.items_found),
            "lore": len(self.lore_found_this_run),
        }
        pause()
        self.p.status_effects = []
        self.p.defending = False
        self.p.dodge_next = False
        return cleared


# ═══════════════════════════════════════════════════════════════
#  TOWN HUB
# ═══════════════════════════════════════════════════════════════

class Town:
    def __init__(self, player):
        self.p = player

    def _town_notices(self):
        notices = []
        if "helped_wounded_soldier" in self.p.story_flags:
            notices.append("A recovered soldier is seen lighting a candle for you at the temple.")
        if "left_wounded_soldier" in self.p.story_flags:
            notices.append("Whispers in the tavern speak of a dying soldier in the lower halls.")
        if "escorted_lost_traveller" in self.p.story_flags:
            notices.append("A merchant has posted your description with a note of thanks in the market.")
        if "ignored_lost_traveller" in self.p.story_flags:
            notices.append("Gatewardens mutter about another traveller missing in the underways.")
        return notices

    def _town_ambient_line(self):
        pool = list(AMBIENT_TOWN)
        notices = self._town_notices()
        if notices:
            pool.append(co(f"  ~ {random.choice(notices)}", C.CYN))
        return random.choice(pool)

    def _next_rumor(self):
        if RUMOR_CHAINS and random.random() < 0.45:
            idx = random.randrange(len(RUMOR_CHAINS))
            key = str(idx)
            stage = int(self.p.rumor_progress.get(key, 0))
            chain = RUMOR_CHAINS[idx]
            rumor = chain[min(stage, len(chain) - 1)]
            if stage < len(chain) - 1:
                self.p.rumor_progress[key] = stage + 1
            return rumor
        return random.choice(RUMORS)

    def run(self):
        while True:
            clr()
            hdr("⛫  UBERSREIK  ⛫", C.BYEL)
            print()
            print(f"  {co(self.p.name, C.BGRN)} — {self.p.cls} (Lvl {self.p.level})")
            if self.p.paragon > 0:
                print(f"  {co(f'Paragon {self.p.paragon}', C.BYEL)}")
            print(f"  {co(get_title(self.p.max_depth_cleared), C.CYN)}")
            print(f"  HP: {hp_bar(self.p.hp, self.p.max_hp)}  MP: {mp_bar(self.p.mp, self.p.max_mp)}")
            print(f"  Gold: {co(str(self.p.gold), C.YEL)}  |  Max Depth: {co(str(self.p.max_depth_cleared), C.BRED)}")
            if self.p.level < 25:
                print(f"  XP: {xp_bar(self.p.xp, self.p.xp_to_level)}")
            print(f"  {co('Town Status:', C.BYEL)} Day {self.p.world_day}, {self.p.world_time} | {self.p.world_weather}")
            print(f"  {co('Omen:', C.MAG)} {self.p.world_omen}")
            if self.p.last_expedition:
                le = self.p.last_expedition
                print(f"  {co('Last Expedition:', C.CYN)} Depth {le.get('depth', '?')} | {le.get('outcome', 'Unknown')} | "
                      f"Kills {le.get('kills', 0)} | Lore {le.get('lore', 0)}")
            sep()
            print(self._town_ambient_line())
            sep()
            print()

            tp_note = co(f" [{self.p.talent_points} points!]", C.BYEL) if self.p.talent_points > 0 else ""

            opts = [
                co("Enter the Dungeon", C.BRED),
                "The Thunderwater Tavern",
                "Dorak's Forge (Blacksmith)",
                "Temple of Sigmar",
                "The Market",
                f"Character Sheet{tp_note}",
                "Manage Inventory",
                "Lore Journal",
                co("Save Game", C.GRN),
                co("Quit", C.GRY),
            ]
            ch = get_choice(opts)

            if ch == 0:
                return "dungeon"
            elif ch == 1:
                self.tavern()
            elif ch == 2:
                self.blacksmith()
            elif ch == 3:
                self.temple()
            elif ch == 4:
                self.market()
            elif ch == 5:
                self.character_sheet()
            elif ch == 6:
                self.manage_inventory()
            elif ch == 7:
                self.lore_journal()
            elif ch == 8:
                return "save"
            elif ch == 9:
                return "quit"

    def tavern(self):
        clr()
        hdr("🍺  THE THUNDERWATER TAVERN  🍺", C.YEL)
        print()
        wrap("The warmth of the hearth and the smell of ale greet you. "
             "The barkeep, a burly man named Otto, polishes a tankard.", C.YEL)
        print()

        while True:
            cost = max(10, 5 + self.p.level * 2)
            opts = [
                f"Rest and Heal ({co(f'{cost}g', C.YEL)})",
                "Listen to Rumours (Free)",
                f"Buy a Round for the House ({co('25g', C.YEL)}) — May hear great tales",
                "Leave",
            ]
            ch = get_choice(opts)
            if ch == 0:
                if self.p.gold >= cost:
                    self.p.gold -= cost
                    self.p.full_heal()
                    self.p.advance_world(1)
                    print(co("\n  You rest by the fire. Wounds mend. Strength returns.", C.GRN))
                    print(co("  Fully healed!", C.BGRN))
                else:
                    print(co("\n  'No coin, no bed!' Otto growls.", C.RED))
            elif ch == 1:
                rumor = self._next_rumor()
                print(f"\n  {co('Otto leans in:', C.YEL)} \"{co(rumor, C.CYN)}\"")
            elif ch == 2:
                if self.p.gold >= 25:
                    self.p.gold -= 25
                    self.p.advance_world(1)
                    print(co("\n  The tavern erupts in cheers! A grateful patron shares a tale...", C.YEL))
                    entry = pick_lore_entry(self.p, max(1, self.p.max_depth_cleared))
                    if entry:
                        self.p.lore_found.append(entry[0])
                        print(f"\n  {co('📜 ' + entry[0], C.BCYN)}")
                        wrap(entry[1], C.CYN)
                    else:
                        print(co("  But you've heard all the tales before.", C.GRY))
                else:
                    print(co("\n  You can't afford a round.", C.RED))
            else:
                break
            pause()

    def blacksmith(self):
        clr()
        hdr("🔨  DORAK'S FORGE  🔨", C.RED)
        print()
        wrap("The heat of the forge hits you as you enter. Dorak, a grizzled Dwarf, "
             "looks up from his anvil. 'What d'ye need, manling?'", C.RED)
        print()

        while True:
            items = [generate_item(max(1, self.p.max_depth_cleared), slot=s)
                     for s in ["weapon", "armor", "accessory"]]
            # Add one guaranteed better item
            items.append(generate_item(max(1, self.p.max_depth_cleared + 2),
                                       rarity=random.choice(["Rare", "Epic"])))
            costs = [max(20, int(it.power_score() * 3 + 15)) for it in items]

            opts = []
            for it, cost in zip(items, costs):
                c = C.YEL if cost <= self.p.gold else C.RED
                opts.append(f"{it.display_name()} — {it.stat_line()} {co(f'[{cost}g]', c)}")
            opts.append("Leave")
            print(f"\n  Your gold: {co(str(self.p.gold), C.YEL)}")
            ch = get_choice(opts)
            if ch >= len(items):
                break
            if costs[ch] > self.p.gold:
                print(co("  'Ye can't afford that, lad!'", C.RED))
            elif len(self.p.inventory) >= 20:
                print(co("  Inventory full!", C.RED))
            else:
                self.p.gold -= costs[ch]
                self.p.inventory.append(items[ch])
                print(co(f"  'Fine choice! That'll serve ye well.' — Dorak", C.GRN))
            pause()

    def temple(self):
        clr()
        hdr("✟  TEMPLE OF SIGMAR  ✟", C.BYEL)
        print()
        wrap("The grand temple radiates warmth and golden light. A priest of Sigmar "
             "approaches with open arms. 'Welcome, child of the Empire.'", C.BYEL)
        print()

        while True:
            bless_cost = max(30, 15 + self.p.level * 3)
            purify_cost = 15
            opts = [
                f"Receive Sigmar's Blessing ({co(f'{bless_cost}g', C.YEL)}) — +15% DMG buff for next dungeon",
                f"Purification ({co(f'{purify_cost}g', C.YEL)}) — Remove all ailments",
                "Pray (Free) — Small chance of divine favour",
                "Leave",
            ]
            ch = get_choice(opts)
            if ch == 0:
                if self.p.gold >= bless_cost:
                    self.p.gold -= bless_cost
                    self.p.status_effects.append({"name": "Sigmar's Blessing", "turns": 30, "damage_bonus": 0.15})
                    print(co("\n  Golden light washes over you. Sigmar protects!", C.BYEL))
                else:
                    print(co("\n  'Faith alone won't pay for candles, child.'", C.RED))
            elif ch == 1:
                if self.p.gold >= purify_cost:
                    self.p.gold -= purify_cost
                    self.p.status_effects = [e for e in self.p.status_effects if e.get("damage_bonus", 0) > 0]
                    print(co("\n  Your body is cleansed of all impurities.", C.GRN))
                else:
                    print(co("\n  Not enough gold.", C.RED))
            elif ch == 2:
                if random.random() < 0.2:
                    bonus = random.choice(["hp", "mp"])
                    if bonus == "hp":
                        self.p.heal(int(self.p.max_hp * 0.3))
                        print(co("\n  Sigmar answers your prayer! You feel invigorated. (+30% HP)", C.BYEL))
                    else:
                        self.p.restore_mp(int(self.p.max_mp * 0.3))
                        print(co("\n  Divine energy flows through you! (+30% MP)", C.BYEL))
                else:
                    prayers = [
                        "You pray in silence. The candles flicker. You feel... watched over.",
                        "The stone is cold beneath your knees. Your faith gives you strength.",
                        "You hear nothing. But the silence itself feels like an answer.",
                        "A sense of calm washes over you. Perhaps that is enough.",
                    ]
                    print(co(f"\n  {random.choice(prayers)}", C.CYN))
            else:
                break
            pause()

    def market(self):
        clr()
        hdr("🏪  THE MARKET  🏪", C.YEL)
        print()
        wrap("Stalls line the busy square. Merchants hawk all manner of wares. "
             "A Halfling potion-seller waves you over.", C.YEL)
        print()

        while True:
            opts = []
            pot_list = list(POTION_TYPES.keys())
            for name in pot_list:
                pt = POTION_TYPES[name]
                cost = pt["base_cost"] + self.p.level
                count = self.p.potions.get(name, 0)
                c = C.YEL if cost <= self.p.gold else C.RED
                opts.append(f"{name} (own: {count}) — {pt['desc']} {co(f'[{cost}g]', c)}")
            opts.append(f"Sell Items ({co(str(len(self.p.inventory)), C.GRN)} in inventory)")
            opts.append("Leave")
            print(f"\n  Your gold: {co(str(self.p.gold), C.YEL)}")
            ch = get_choice(opts)

            if ch < len(pot_list):
                name = pot_list[ch]
                cost = POTION_TYPES[name]["base_cost"] + self.p.level
                if self.p.gold >= cost:
                    self.p.gold -= cost
                    self.p.potions[name] = self.p.potions.get(name, 0) + 1
                    print(co(f"  Bought {name}!", C.GRN))
                else:
                    print(co("  Not enough gold!", C.RED))
            elif ch == len(pot_list):
                self._sell_items()
            else:
                break
            pause()

    def _sell_items(self):
        if not self.p.inventory:
            print(co("\n  Nothing to sell.", C.GRY))
            return
        while self.p.inventory:
            print(f"\n  Your gold: {co(str(self.p.gold), C.YEL)}")
            opts = []
            for it in self.p.inventory:
                value = max(5, int(it.power_score() * 1.2 + 3))
                opts.append(f"{it.display_name()} — {it.stat_line()} {co(f'[Sell: {value}g]', C.YEL)}")
            opts.append("Sell All Junk (Common+Uncommon)")
            opts.append("Done")
            ch = get_choice(opts)
            if ch < len(self.p.inventory):
                it = self.p.inventory[ch]
                value = max(5, int(it.power_score() * 1.2 + 3))
                self.p.gold += value
                self.p.inventory.remove(it)
                print(co(f"  Sold for {value} gold!", C.YEL))
            elif ch == len(self.p.inventory):
                junk = [it for it in self.p.inventory if it.rarity in ("Common", "Uncommon")]
                total = 0
                for it in junk:
                    value = max(5, int(it.power_score() * 1.2 + 3))
                    total += value
                    self.p.inventory.remove(it)
                self.p.gold += total
                print(co(f"  Sold {len(junk)} items for {total} gold!", C.YEL))
            else:
                break

    def character_sheet(self):
        while True:
            clr()
            hdr("CHARACTER SHEET", C.CYN)
            p = self.p
            print(f"\n  {co(p.name, C.BGRN)} — {p.cls}")
            print(f"  Level: {p.level}  |  Paragon: {p.paragon}")
            print(f"  Title: {co(get_title(p.max_depth_cleared), C.BYEL)}")
            print(f"  Max Depth Cleared: {co(str(p.max_depth_cleared), C.BRED)}")
            print(f"  Total Kills: {co(str(p.total_kills), C.RED)}")
            print(f"  Gold Earned: {co(str(p.total_gold_earned), C.YEL)}")
            sep()
            print(f"  HP: {hp_bar(p.hp, p.max_hp)}")
            print(f"  MP: {mp_bar(p.mp, p.max_mp)}")
            if p.level < 25:
                print(f"  XP: {xp_bar(p.xp, p.xp_to_level)}")
            print(f"  Gold: {co(str(p.gold), C.YEL)}")
            sep()
            print(co("  STATS:", C.BYEL))
            for stat, val in p.stats.items():
                label = {"str": "Strength", "tou": "Toughness", "agi": "Agility",
                         "int": "Intelligence", "wil": "Willpower"}[stat]
                print(f"    {label:15s} {co(str(val), C.BGRN)}")
            sep()
            print(co("  DERIVED:", C.BYEL))
            print(f"    Attack Power:  {co(str(p.attack_power), C.RED)}")
            print(f"    Magic Power:   {co(str(p.magic_power), C.BLU)}")
            print(f"    Defense:       {co(str(p.defense), C.CYN)}")
            print(f"    Crit Chance:   {co(f'{p.crit_chance:.1f}%', C.YEL)}")
            print(f"    Dodge Chance:  {co(f'{p.dodge_chance:.1f}%', C.GRN)}")
            print(f"    Block Chance:  {co(f'{p.block_chance:.1f}%', C.BLU)}")
            sep()
            print(co("  EQUIPMENT:", C.BYEL))
            for slot in ("weapon", "armor", "accessory"):
                it = p.equipment[slot]
                if it:
                    print(f"    {slot.capitalize():12s} {it.display_name()} — {it.stat_line()}")
                else:
                    print(f"    {slot.capitalize():12s} {co('(empty)', C.GRY)}")
            sep()

            opts = ["View Talents", "View Skills", "Back"]
            if p.talent_points > 0:
                opts[0] = co(f"View Talents [{p.talent_points} points!]", C.BYEL)
            ch = get_choice(opts)
            if ch == 0:
                self._talent_screen()
            elif ch == 1:
                self._skills_screen()
            else:
                break

    def _talent_screen(self):
        while True:
            clr()
            hdr("TALENTS", C.CYN)
            p = self.p
            print(f"\n  Talent Points: {co(str(p.talent_points), C.BYEL)}")
            sep()
            talent_list = TALENTS[p.cls]
            opts = []
            for t in talent_list:
                name, desc_tmpl, values, key = t
                rank = p.talents.get(name, 0)
                max_rank = len(values)
                if rank > 0:
                    cur_val = values[rank - 1]
                    desc = desc_tmpl.format(v=cur_val)
                else:
                    desc = desc_tmpl.format(v=values[0])
                rank_text = f"[{rank}/{max_rank}]"
                if rank >= max_rank:
                    opts.append(f"{co(name, C.BGRN)} {co(rank_text, C.GRN)} — {desc} {co('(MAXED)', C.GRN)}")
                elif p.talent_points > 0:
                    next_val = values[rank]
                    next_desc = desc_tmpl.format(v=next_val)
                    opts.append(f"{co(name, C.BYEL)} {rank_text} — Next: {co(next_desc, C.YEL)}")
                else:
                    opts.append(f"{name} {rank_text} — {desc}")
            opts.append("Back")
            ch = get_choice(opts)
            if ch >= len(talent_list):
                break
            t = talent_list[ch]
            name = t[0]
            rank = p.talents.get(name, 0)
            if rank >= len(t[2]):
                print(co("  Already maxed!", C.GRY))
                pause()
            elif p.talent_points <= 0:
                print(co("  No talent points available.", C.RED))
                pause()
            else:
                p.talents[name] = rank + 1
                p.talent_points -= 1
                new_val = t[2][rank]
                print(co(f"  {name} upgraded to rank {rank + 1}! ({t[1].format(v=new_val)})", C.BGRN))
                # Recompute HP/MP if needed
                p.hp = min(p.hp, p.max_hp)
                p.mp = min(p.mp, p.max_mp)
                pause()

    def _skills_screen(self):
        clr()
        hdr("SKILLS", C.CYN)
        skills = CLASSES[self.p.cls]["skills"]
        for i, sk in enumerate(skills):
            sk_name = sk['name']
            sk_cost = sk['cost']
            sk_desc = sk['desc']
            print(f"\n  {co(f'Skill {i+1}:', C.BYEL)} {co(sk_name, C.BCYN)}")
            print(f"    Cost: {co(str(sk_cost) + ' MP', C.BLU)}")
            wrap(f"    {sk_desc}", C.WHT)
        pause()

    def manage_inventory(self):
        while True:
            clr()
            hdr("INVENTORY", C.YEL)
            p = self.p
            print(f"\n  Items: {len(p.inventory)}/20")
            sep()
            print(co("  EQUIPPED:", C.BYEL))
            for slot in ("weapon", "armor", "accessory"):
                it = p.equipment[slot]
                if it:
                    print(f"    [{slot.upper()}] {it.display_name()} — {it.stat_line()}")
                else:
                    print(f"    [{slot.upper()}] {co('(empty)', C.GRY)}")
            sep()

            if not p.inventory:
                print(co("\n  Inventory is empty.", C.GRY))
                pause()
                break

            opts = []
            for it in p.inventory:
                equipped_same_slot = p.equipment.get(it.slot)
                compare = ""
                if equipped_same_slot:
                    ps_diff = it.power_score() - equipped_same_slot.power_score()
                    if ps_diff > 0:
                        compare = co(f" [UPGRADE ↑]", C.BGRN)
                    elif ps_diff < 0:
                        compare = co(f" [DOWNGRADE ↓]", C.RED)
                opts.append(f"{it.display_name()} [{it.slot}] — {it.stat_line()}{compare}")
            opts.append("Back")

            ch = get_choice(opts)
            if ch >= len(p.inventory):
                break

            item = p.inventory[ch]
            print(f"\n  {item.display_name()}")
            print(f"  {item.stat_line()}")
            print(f"  Rarity: {co(item.rarity, RC[item.rarity])}  |  Level: {item.level}")

            sub_opts = ["Equip", "Drop", "Cancel"]
            sch = get_choice(sub_opts)
            if sch == 0:
                old = p.equip(item)
                print(co(f"  Equipped {item.name}!", C.GRN))
                if old:
                    print(co(f"  Unequipped {old.name} (moved to inventory).", C.GRY))
                pause()
            elif sch == 1:
                p.inventory.remove(item)
                print(co(f"  Dropped {item.name}.", C.RED))
                pause()

    def lore_journal(self):
        clr()
        hdr("📜  LORE JOURNAL  📜", C.CYN)
        p = self.p
        if not p.lore_found:
            print(co("\n  No lore entries discovered yet. Explore the dungeon!", C.GRY))
        else:
            print(f"\n  Entries found: {co(f'{len(p.lore_found)}/{len(LORE)}', C.CYN)}")
            sep()
            opts = [co(name, C.BCYN) for name in p.lore_found] + ["Back"]
            ch = get_choice(opts)
            if ch < len(p.lore_found):
                entry = next(l for l in LORE if l[0] == p.lore_found[ch])
                print(f"\n  {co(entry[0], C.BCYN)}")
                sep()
                wrap(entry[1], C.CYN)
        pause()


# ═══════════════════════════════════════════════════════════════
#  GAME CONTROLLER
# ═══════════════════════════════════════════════════════════════

class Game:
    def __init__(self):
        self.player = None

    def title_screen(self):
        clr()
        print(co(r"""
  ╔════════════════════════════════════════════╗
  ║                                            ║
  ║  █   █ █▀▀█ █▀▀█ █  █ █▀▀█ █▀█▀█ █▀█▀█  ║
  ║  █ █ █ █▀▀█ █▀▀▄ █▀▀█ █▀▀█ █ █ █ █ █ █  ║
  ║  █▄▀▄█ ▀  ▀ ▀  ▀ ▀  ▀ ▀  ▀ ▀ ▀ ▀ ▀▀▀▀▀  ║
  ║                                            ║
  ║   Q U E S T :  D E P T H S  O F  T H E    ║
  ║          O L D   W O R L D                 ║
  ║                                            ║
  ╚════════════════════════════════════════════╝
""", C.BRED))
        print(co("   A dungeon crawler in the Warhammer Fantasy world", C.CYN))
        print(co("   Inspired by Warhammer Quest, Diablo, HeroQuest", C.GRY))
        print()

    def run(self):
        try:
            self._run()
        except (KeyboardInterrupt, EOFError):
            if self.player:
                self.save_game()
                print(co("\n\n  Game auto-saved. Farewell, adventurer.", C.YEL))
            print()
            sys.exit(0)

    def _run(self):
        while True:
            self.title_screen()
            has_save = SAVE_FILE.exists()
            opts = ["New Game"]
            if has_save:
                opts.append("Continue")
            opts.append("Quit")
            ch = get_choice(opts)

            if ch == 0:
                self.new_game()
                self.game_loop()
            elif ch == 1 and has_save:
                if self.load_game():
                    self.game_loop()
                else:
                    print(co("  Failed to load save!", C.RED))
                    pause()
            else:
                print(co("\n  May Sigmar protect you. Farewell.", C.YEL))
                break

    def new_game(self):
        clr()
        hdr("CREATE YOUR HERO", C.BYEL)
        print()

        # Name
        print(co("  What is your name, adventurer?", C.CYN))
        name = ""
        while not name:
            name = get_input()
            if not name:
                print(co("  Enter a name.", C.RED))
        name = name[:20]

        # Class
        print(co(f"\n  Welcome, {name}. Choose your calling:\n", C.CYN))
        cls_names = list(CLASSES.keys())
        for i, cname in enumerate(cls_names):
            cd = CLASSES[cname]
            print(f"  {co(str(i+1), C.BYEL)}) {co(cname, C.BGRN)}")
            for line in cd["desc"].split("\n"):
                print(f"     {co(line.strip(), C.GRY)}")
            stats_str = " | ".join(f"{k.upper()}: {v}" for k, v in cd["stats"].items())
            print(f"     {co(stats_str, C.CYN)}")
            print(f"     HP: {cd['hp']}  MP: {cd['mp']}")
            print()
        while True:
            r = get_input("Choose (1-4): ")
            if r.isdigit() and 1 <= int(r) <= len(cls_names):
                cls = cls_names[int(r) - 1]
                break
            print(co("  Invalid choice.", C.RED))

        self.player = Player(name, cls)

        # Stat allocation
        clr()
        hdr("ALLOCATE BONUS STATS", C.CYN)
        print(f"\n  Base stats for {co(cls, C.BGRN)}:")
        for s, v in self.player.stats.items():
            label = {"str": "Strength", "tou": "Toughness", "agi": "Agility",
                     "int": "Intelligence", "wil": "Willpower"}[s]
            print(f"    {label:15s} {v}")
        print(co(f"\n  You have {bo('5')} bonus points to distribute.", C.BYEL))
        points = 5
        stat_names = list(self.player.stats.keys())
        labels = {"str": "Strength", "tou": "Toughness", "agi": "Agility",
                  "int": "Intelligence", "wil": "Willpower"}
        while points > 0:
            print(f"\n  Points remaining: {co(str(points), C.BYEL)}")
            opts = [f"{labels[s]}: {self.player.stats[s]}" for s in stat_names]
            opts.append("Done (save remaining for later)" if points > 0 else "Done")
            ch = get_choice(opts)
            if ch < len(stat_names):
                self.player.stats[stat_names[ch]] += 1
                points -= 1
            else:
                break
        self.player.hp = self.player.max_hp
        self.player.mp = self.player.max_mp

        # Give starting equipment
        starter_weapons = {
            "Empire Soldier": ("Iron Sword", 8),
            "Dwarf Ironbreaker": ("Iron Axe", 9),
            "Elf Waywatcher": ("Simple Bow", 7),
            "Bright Wizard": ("Worn Staff", 6),
        }
        w_name, w_dmg = starter_weapons[cls]
        starter_weapon = Item(w_name, "weapon", "Common", 1, damage=w_dmg)
        starter_armor = Item("Worn Leather Armour", "armor", "Common", 1, defense=4)
        self.player.equipment["weapon"] = starter_weapon
        self.player.equipment["armor"] = starter_armor

        # Intro text
        clr()
        hdr("THE ADVENTURE BEGINS", C.BYEL)
        print()
        slow_print(co(f"  {name}, {cls} of the Old World...", C.CYN), 0.03)
        time.sleep(0.5)
        print()
        intro_text = (
            "The town of Ubersreik clings to the edge of civilisation. "
            "Beyond its ancient walls, darkness gathers. Below the town, "
            "labyrinthine dungeons stretch into the earth — remnants of "
            "Dwarf holds, Skaven warrens, and far older things.\n\n"
            "Adventurers come seeking glory and gold. Most never return. "
            "But the depths must be plunged, for the evil below grows "
            "stronger with each passing day. Someone must descend.\n\n"
            "That someone is you."
        )
        for para in intro_text.split("\n\n"):
            wrap(para, C.CYN)
            print()
            time.sleep(0.3)
        pause()

    def game_loop(self):
        while True:
            town = Town(self.player)
            result = town.run()

            if result == "dungeon":
                self._enter_dungeon()
            elif result == "save":
                self.save_game()
                print(co("\n  Game saved!", C.BGRN))
                pause()
            elif result == "quit":
                self.save_game()
                print(co("\n  Game saved. Until next time, adventurer.", C.YEL))
                pause()
                break

    def _enter_dungeon(self):
        clr()
        max_available = self.player.max_depth_cleared + 1
        hdr("CHOOSE YOUR DEPTH", C.BRED)
        print()
        print(f"  Deepest cleared: {co(str(self.player.max_depth_cleared), C.BYEL)}")
        print(f"  Available: Depths 1 to {co(str(max_available), C.BRED)}")
        print()
        wrap("Higher depths have tougher enemies but better rewards. "
             "Every 5th depth features a powerful Boss.", C.GRY)
        print()

        opts = []
        for d in range(max(1, max_available - 4), max_available + 1):
            boss_tag = co(" [BOSS]", C.BYEL) if d % 5 == 0 else ""
            new_tag = co(" [NEW]", C.BRED) if d > self.player.max_depth_cleared else ""
            opts.append(f"Depth {d}{boss_tag}{new_tag}")
        opts.append("Back to town")
        ch = get_choice(opts)

        if ch >= len(opts) - 1:
            return

        depth = max(1, max_available - 4) + ch
        dungeon = Dungeon(self.player, depth)
        dungeon.run()
        self.player.advance_world(1)

        # Auto-save after dungeon
        self.save_game()

    def save_game(self):
        if not self.player:
            return
        try:
            data = self.player.to_dict()
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(co(f"  Save error: {e}", C.RED))

    def load_game(self):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.player = Player.from_dict(data)
            return True
        except Exception as e:
            print(co(f"  Load error: {e}", C.RED))
            return False


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Check terminal supports colors
    if sys.platform == "win32":
        os.system("color")
    game = Game()
    game.run()
