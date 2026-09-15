import contextlib
import io
import json
import random
import unittest
from unittest.mock import patch

import warhammer_quest as game


class EndlessTests(unittest.TestCase):
    def setUp(self):
        self.player = game.Player('Tester', 'Empire Soldier')
        self.enemy = game.Enemy('Dummy', 1000, 20, 0, 1, (1, 2), [], 1)
        self.combat = game.Combat(self.player, self.enemy)

    def equip_set(self, key, count=3):
        self.player.equipment = {'weapon': None, 'armor': None, 'accessory': None}
        for slot in list(self.player.equipment)[:count]:
            self.player.equipment[slot] = game.Item(slot, slot, 'Rare', 5, set_id=key)

    def test_zones_repeat_with_higher_stats_and_no_final_depth(self):
        for depth in (1, 5, 16, 30, 301, 3001):
            random.seed(10)
            first = game.make_enemy(depth)
            random.seed(10)
            later = game.make_enemy(depth + 30)
            self.assertEqual(game.zone_for_depth(depth), game.zone_for_depth(depth + 30))
            self.assertGreater(later.max_hp, first.max_hp)
            self.assertGreater(later.atk / game.condition_for_depth(depth + 30)["attack"], first.atk / game.condition_for_depth(depth)["attack"])
            self.assertGreater(later.base_xp / game.condition_for_depth(depth + 30)["xp"], first.base_xp / game.condition_for_depth(depth)["xp"])
            self.assertEqual(game.Dungeon(self.player, depth).rooms[-1]['event'], 'boss' if depth % 5 == 0 else 'miniboss')
        for depth in (5, 35, 305, 3005):
            boss = game.make_boss(depth)
            self.assertTrue(boss.is_boss)
            self.assertGreater(boss.max_hp, 0)

    def test_guardians_drop_zone_set_piece(self):
        for depth in (5, 10, 15, 20, 25, 30, 35):
            self.player.inventory = []
            dungeon = game.Dungeon(self.player, depth)
            with patch.object(game.random, 'random', return_value=1), patch.object(game, 'get_choice', return_value=0), patch.object(game, 'pause'), contextlib.redirect_stdout(io.StringIO()):
                dungeon._victory_rewards(game.make_boss(depth), is_boss=True)
            self.assertEqual(len(self.player.inventory), 1)
            item = self.player.inventory[0]
            self.assertEqual(item.set_id, game.zone_for_depth(depth)['set'])
            self.assertEqual(item.level, depth)

    def test_all_set_pieces_generate_and_roundtrip(self):
        for key in game.EQUIPMENT_SETS:
            for slot in ('weapon', 'armor', 'accessory'):
                item = game.generate_item(50, slot=slot, set_id=key)
                self.assertEqual(item.set_id, key)
                self.assertIn('2 pieces', item.stat_line())
                self.assertEqual(game.Item.from_dict(item.to_dict()).to_dict(), item.to_dict())
        legacy = game.Item('Old sword', 'weapon', 'Common', 1).to_dict()
        legacy.pop('set_id')
        self.assertEqual(game.Item.from_dict(legacy).set_id, '')

    def test_set_thresholds_and_unequip(self):
        base_block = self.player.block_chance
        self.equip_set('ironwarden', 1)
        self.assertEqual(self.player.block_chance, base_block)
        self.equip_set('ironwarden', 2)
        self.assertEqual(self.player.block_chance, base_block + 8)
        self.player.equip(game.Item('Plain', 'armor', 'Common', 1))
        self.assertEqual(self.player.block_chance, base_block)
        self.equip_set('thorn', 2)
        self.assertEqual(self.player.dodge_chance, self.player.stats['agi'] * .5 + 8)
        self.equip_set('reaver', 2)
        self.assertEqual(self.player.crit_chance, 5 + self.player.stats['agi'] * .8 + 8)

    def test_ironwarden_heals_only_with_three_pieces(self):
        self.equip_set('ironwarden', 2)
        self.player.hp = 10
        with patch.object(game, 'get_choice', return_value=5):
            self.combat.player_turn()
            self.assertEqual(self.player.hp, 10)
            self.equip_set('ironwarden', 3)
            self.combat.player_turn()
        self.assertEqual(self.player.hp, 10 + int(self.player.max_hp * .03))

    def test_ember_cost_and_damage(self):
        skill = game.CLASSES[self.player.cls]['skills'][0]
        self.equip_set('ember', 2)
        self.assertEqual(self.combat._skill_cost(skill), 12)
        with patch.object(game.random, 'random', return_value=1), patch.object(game.random, 'uniform', return_value=1):
            base = self.player.calc_damage(is_skill=True)[0]
            self.equip_set('ember', 3)
            self.assertEqual(self.player.calc_damage(is_skill=True)[0], int(base * 1.25))
            self.assertEqual(self.player.calc_damage()[0], base)
        self.enemy.depth = 11  # Warp Surge
        self.assertEqual(self.combat._skill_cost(skill), 9)
        before = self.player.mp
        with patch.object(game, 'get_choice', return_value=1):
            self.combat.player_turn()
        self.assertEqual(before - self.player.mp, 9)

    def test_thorn_bleed_does_not_stack_and_reaver_ignores_overkill(self):
        self.equip_set('thorn')
        with patch.object(game, 'get_choice', return_value=0):
            self.combat.player_turn()
            self.combat.player_turn()
        effects = [e for e in self.enemy.status_effects if e['name'] == 'Briar Bleed']
        self.assertEqual(len(effects), 1)
        before = self.enemy.hp
        self.enemy.apply_status_tick()
        self.assertEqual(before - self.enemy.hp, max(1, int(self.player.attack_power * .12)))
        self.equip_set('reaver')
        self.player.hp = 10
        self.enemy.hp = 50
        self.assertEqual(self.combat._deal_damage(1000), 50)
        self.assertEqual(self.player.hp, 13)

    def test_new_special_strikes_and_defend_counters(self):
        with patch.object(game.random, 'random', return_value=1):
            for intent in ('drain', 'bleed', 'sunder'):
                self.player.full_heal()
                self.enemy.intent = intent
                before_mp = self.player.mp
                self.combat.enemy_turn()
                if intent == 'drain':
                    self.assertLess(self.player.mp, before_mp)
                else:
                    self.assertTrue(self.player.status_effects)
                self.player.full_heal()
                self.player.defending = True
                self.combat.enemy_turn()
                self.assertEqual(self.player.mp, self.player.max_mp)
                self.assertFalse(self.player.status_effects)

    def test_all_new_enemies_intents_execute(self):
        for zone_index, zone in enumerate(game.ZONES):
            depth = zone_index * 5 + 1
            for name, hp, atk, defense, abilities in zone['mobs']:
                enemy = game.Enemy(name, hp, atk, defense, 1, (1, 2), list(abilities), depth)
                combat = game.Combat(self.player, enemy)
                for turn in range(9):
                    self.player.full_heal()
                    enemy.hp = enemy.max_hp
                    combat.turn = turn
                    combat._plan_intent()
                    with patch.object(game, 'clr'), contextlib.redirect_stdout(io.StringIO()):
                        combat.display()
                        combat.enemy_turn()
                    self.assertGreaterEqual(self.player.hp, 0)

    def test_conditions_change_camp_and_resources(self):
        dungeon = game.Dungeon(self.player, 16)  # Sapping Cold
        self.player.mp = 0
        with patch.object(game, 'get_choice', return_value=1), patch.object(game, 'pause'), contextlib.redirect_stdout(io.StringIO()):
            dungeon._camp()
        self.assertEqual(self.player.mp, int(self.player.max_mp * .25))
        base = game.Enemy('A', 30, 20, 1, 100, (100, 200), [], 6)
        old_attack, old_gold = base.atk, base.gold_range[0]
        game._apply_depth_traits(base, 6)
        self.assertEqual(base.atk, int(old_attack * 1.15))
        self.assertEqual(base.gold_range[0], int(old_gold * 1.2))

    def test_legacy_save_no_story_gating_and_farming_validates_depth(self):
        self.player.campaign_stage = 4
        self.player.max_depth_cleared = 20
        self.player = game.Player.from_dict(json.loads(json.dumps(self.player.to_dict())))
        app = game.Game()
        app.player = self.player
        output = io.StringIO()
        with patch.object(game, 'get_choice', return_value=5), patch.object(game, 'get_input', side_effect=['99', '5']), patch.object(game, 'clr'), patch.object(game, 'Dungeon') as dungeon, patch.object(app, 'save_game'), contextlib.redirect_stdout(output):
            app._enter_dungeon()
            self.assertEqual(dungeon.call_args.args[1], 5)
        self.assertNotIn('[STORY]', output.getvalue())
        self.assertIn('Choose an unlocked depth', output.getvalue())
        self.assertEqual(self.player.max_depth_cleared, 20)

    def test_character_sheet_displays_sets_and_exits(self):
        self.equip_set('ember')
        output = io.StringIO()
        with patch.object(game, 'get_choice', return_value=2), patch.object(game, 'clr'), contextlib.redirect_stdout(output):
            game.Town(self.player).character_sheet()
        self.assertIn('Ember Covenant 3/3', output.getvalue())
        self.assertIn('+25% skill damage', output.getvalue())

    def test_relics_and_sets_survive_player_save(self):
        self.equip_set('reaver')
        self.player.inventory.append(game.Item('Old relic', 'accessory', 'Rare', 1, special=game.RELICS[0][1]))
        data = json.loads(json.dumps(self.player.to_dict()))
        loaded = game.Player.from_dict(data)
        self.assertEqual(loaded.set_count('reaver'), 3)
        self.assertEqual(loaded.to_dict(), data)

    def test_new_relics(self):
        self.player.equip(game.Item('Token', 'accessory', 'Rare', 1, special=game.RELICS[3][1]))
        self.enemy.hp = 100
        self.assertEqual(self.combat._deal_damage(20), 25)
        self.player.equip(game.Item('Medallion', 'accessory', 'Rare', 1, special=game.RELICS[4][1]))
        self.player.status_effects = [{'name': 'Poison', 'turns': 3, 'dot': 3}, {'name': 'Rallied', 'turns': 2, 'damage_bonus': .15}]
        with patch.object(game, 'get_choice', return_value=5):
            self.combat.player_turn()
        self.assertEqual([e['name'] for e in self.player.status_effects], ['Rallied'])


if __name__ == '__main__':
    unittest.main()
