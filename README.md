# WARHAMMER QUEST: DEPTHS OF THE OLD WORLD

A text-based terminal dungeon crawler set in the Warhammer Fantasy universe.  
Inspired by *Warhammer Quest*, *Diablo*, *HeroQuest*, and *Warhammer Quest: The Card Game*.

## How to Run

```bash
python3 warhammer_quest.py
```

> **Note:** Requires Python 3.6+. macOS may need you to install Python 3 via:
> ```bash
> xcode-select --install    # installs Python 3 via Command Line Tools
> ```
> Or download from https://www.python.org/downloads/ (do this while you have internet!)

## Features

- **4 Classes** — Empire Soldier, Dwarf Ironbreaker, Elf Waywatcher, Bright Wizard
- **Infinite Progression** — Endless dungeon depths that scale in difficulty, like Diablo 3 Greater Rifts
- **Town Hub (Ubersreik)** — Tavern, Blacksmith, Temple of Sigmar, Market
- **6 Talents per class** — 3 ranks each, unlocked with talent points on level up
- **3 Active Skills per class** — Enhanced by your talent choices
- **Equipment System** — Weapons, Armor, Accessories with 5 rarity tiers (Common → Legendary)
- **Character Customization** — Name, class, stat allocation, talent builds
- **Combat** — Turn-based with skills, potions, defense, flee, status effects
- **Boss Fights** — Every 5th depth features a boss encounter
- **Lore Journal** — Discover Warhammer Fantasy lore entries throughout the dungeon
- **Ambient Text** — Atmospheric messages in town and dungeon for immersion
- **Paragon System** — Continue progressing after max level (25) with incremental bonuses
- **Color-coded Text** — Full ANSI color support for terminal
- **Save/Load** — Auto-saves after each dungeon run, manual save from town
- **No Internet Required** — Completely offline, single-file, no dependencies

## Controls

All input is number-based menus. Just type the number of your choice and press Enter.

## Tips

- **Heal at the Tavern** before entering the dungeon
- **Buy potions** at the Market — they save lives in deep runs
- **Sell junk items** to afford better gear at the Blacksmith  
- **Sigmar's Blessing** from the Temple gives +15% damage for a full dungeon run
- **Push deeper** for better loot — but know when to retreat
- **Farm lower depths** if the next depth is too hard
- **Buy rounds at the Tavern** to discover lore entries
- The game **auto-saves** when you exit a dungeon or press Ctrl+C

## Classes

| Class | Style | Strengths |
|---|---|---|
| Empire Soldier | Balanced melee | Good HP, shield bash stun, Rally healing |
| Dwarf Ironbreaker | Tank | Highest HP, scaling grudge damage, Iron Resolve |
| Elf Waywatcher | Agile DPS | High crit/dodge, multi-hit arrows, evasion |
| Bright Wizard | Glass cannon | Devastating magic, flame shield, lifesteal |

## Save File

Your save is stored as `wq_save.json` in the same folder as the game.  
Back it up if you want to preserve progress!

## Expedition choices

- Before each ordinary room, choose between two paths with visible encounter types: combat, treasure, traps, shrines, events, or quiet passages. The final guardian remains mandatory.
- Between rooms, make camp once per expedition: restore 30% HP or 40% MP.
- Each expedition offers a contract: defeat three enemies or explore three non-combat rooms. Complete the objective **and clear the depth** to earn `30 + depth × 10` bonus gold. Retreating does not pay the contract.
- Damage buffs and fear now affect damage. Ironbark grants its advertised +5 defense, Ancestral Ward reduces damage, and Morr's Shield prevents fear.
- The temple's Sigmar blessing and Morr's Shield last until the expedition ends; shrine damage/ward blessings last five combat turns.

## Verification

Run `python3 -B -m unittest discover -s tests -v` for combat effects, expedition routes, contracts, camping, defeat reporting, and save compatibility. Tests do not write to your save file.
