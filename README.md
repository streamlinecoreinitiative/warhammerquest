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

## Endless depth zones

Progression has one gate: clear the current depth to unlock the next. There is no final floor, chapter selection, or separate campaign. Lore describes the zone and its guardian within the normal descent.

| First appearance | Zone | Guardian's guaranteed set drop |
| --- | --- | --- |
| 1–5 | Vermin Warrens | Thornstalker |
| 6–10 | Broken Forges | Ironwarden |
| 11–15 | Sepulchral Halls | Blood Reaver |
| 16–20 | Rootbound Deeps | Thornstalker |
| 21–25 | Warpfire Sanctum | Ember Covenant |
| 26–30 | The Black Abyss | Blood Reaver |

The zones recur every 30 depths, with increasing corruption, additional enemy abilities, rotating conditions and depth-scaled enemies and equipment. Some guardians alternate on later circuits. Corruption's stat multiplier approaches 2× rather than growing without limit on top of depth scaling. Ordinary armor mitigation caps at 75% for both sides; defensive actions and wards can reach 85%, keeping damage relevant in deep play.

There are 24 new enemy templates alongside the original roster. Soul drain attacks consume mana, rending attacks cause bleeding, and armour breakers temporarily reduce defense. These attacks are announced and defending prevents their added effect. From depth 11, enemies can roll one of four elite variants with extra abilities and better rewards.

### Conditions

The first five floors have no additional hazard. Later five-floor bands rotate:

- **Blood Moon:** enemies deal 15% more damage and yield 20% more gold.
- **Warp Surge:** skills cost 20% less mana, while enemies deal 10% more damage.
- **Sapping Cold:** meditation at camp restores 25% mana instead of 40%; enemies yield 20% more XP.

Check the depth menu before entering. `Choose another unlocked depth` lets you return to an easier zone or farm a specific guardian. Uncleared depths beyond your next one remain locked.

## Equipment sets

Each set contains a weapon, armor and accessory: 12 named pieces total. Only **equipped** pieces count; the character sheet shows your active bonuses. Set pieces keep scaling with their drop depth, so a deeper version can replace an older one without changing your build.

| Set | Two pieces | Three pieces (also keeps the two-piece bonus) |
| --- | --- | --- |
| Ironwarden | +8% block chance | Defending heals 3% maximum HP |
| Ember Covenant | Skills cost 3 less MP | +25% skill damage |
| Thornstalker | +8% dodge chance | Basic attacks cause two ticks of bleeding at 12% attack power per tick; reapplying refreshes it |
| Blood Reaver | +8% critical chance | Direct damage heals 6% of actual enemy HP removed, excluding overkill |

At depth 5 and beyond, Rare/Epic/Legendary items have a 35% chance to become a random set piece. Every fifth-depth guardian additionally drops one guaranteed piece from its zone's set; the slot and rarity vary. There is no requirement to finish a story or collect a full set to descend.

## Tactical combat and relics

Read the enemy's **intent before choosing your action**. Heavy attackers recover after their blow, taking 50% extra damage and skipping their attack. Guarding enemies take half damage and do not attack. Defending restores up to 3 MP and prevents new poison from a poison strike. Stuns and dodges provide alternative counters. Cancelling a potion or selecting a skill without enough mana does not consume a turn.

Choose a free accessory after your first successful depth; it can be deferred until another successful expedition. More relics can appear in Rare or better accessory loot, so the initial choice does not permanently lock your playstyle.

| Relic | Effect |
| --- | --- |
| Bloodglass Pendant | Spend 5% maximum HP for two basic strikes at 70% damage each; use a normal attack if too wounded to pay safely |
| Waystone Focus | Basic attacks restore up to 6 MP |
| Oathkeeper's Seal | A damaging enemy strike while defending triggers a counterattack at 60% attack power, before enemy mitigation |
| Headsman's Token | +25% direct damage against an enemy already below 30% HP |
| Purity Medallion | Defending removes poison and bleeding |

Rare and Epic equipment can now carry special effects too. Existing legendary damage, leech, block, regeneration, reflection, dodge and ward effects apply in combat. Lucky equipment provides its stated percentage chance for a successful ordinary combat drop to receive Rare-or-better rarity.

## Existing saves

Your level, depth record, equipment, inventory and relics remain valid. Former campaign progress is retained as legacy save data but does not control access or rewards. Any previously earned courier camping benefit remains available. New characters need no campaign to obtain relics or explore zones.

Run `python3 -B -m unittest discover -s tests -v`. Tests cover set bonuses, old saves, enemy actions, guardian drops, conditions, depth selection and deep generation, plus combat regressions. Automated checks do not replace human testing of difficulty and pacing.
