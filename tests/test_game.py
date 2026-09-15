import contextlib
import io
import json
import random
import unittest
from unittest.mock import patch
import warhammer_quest as game


class GameTests(unittest.TestCase):
    def setUp(self):
        self.p = game.Player('Tester', next(iter(game.CLASSES)))

    def damage(self):
        with patch.object(game.random, 'random', return_value=1), patch.object(game.random, 'uniform', return_value=1):
            return self.p.calc_damage()[0]

    def test_damage_effects(self):
        base = self.damage()
        for bonus in (0.15, 0.2, -0.15):
            self.p.status_effects = [{'name': 'Effect', 'turns': 3, 'damage_bonus': bonus}]
            self.assertEqual(self.damage(), int(base * (1 + bonus)))

    def test_defensive_effects(self):
        with patch.object(game.random, 'random', return_value=1):
            base = self.p.take_damage(100)[0]
            self.p.status_effects = [{'name': 'Ironbark', 'turns': 5, 'defense_bonus': 5}]
            self.assertLess(self.p.take_damage(100)[0], base)
            self.p.status_effects = [{'name': 'Ancestral Ward', 'turns': 5, 'value': .3}]
            self.assertLess(self.p.take_damage(100)[0], base)

    def test_morr_blocks_fear(self):
        self.p.status_effects = [{'name': "Morr's Shield", 'turns': 20, 'expedition': True}]
        enemy = game.make_enemy(1)
        with patch.object(enemy, 'get_special', return_value='fear'), patch.object(game.random, 'random', return_value=1):
            game.Combat(self.p, enemy).enemy_turn()
        self.assertFalse(any(e['name'] == 'Fear' for e in self.p.status_effects))
        for _ in range(40):
            self.p.apply_status_tick()
        self.assertEqual(len(self.p.status_effects), 1)

    def finish(self, dungeon, cleared):
        with patch.object(game, 'clr'), patch.object(game, 'pause'), contextlib.redirect_stdout(io.StringIO()):
            return dungeon._end_run(cleared)

    def test_defeat_is_recorded_after_revival(self):
        self.p.hp = 0
        self.finish(game.Dungeon(self.p, 1), False)
        self.assertTrue(self.p.is_alive())
        self.assertEqual(self.p.last_expedition['outcome'], 'Defeat')

    def test_contract_requires_clear(self):
        for cleared in (False, True):
            dungeon = game.Dungeon(self.p, 1)
            dungeon.contract = 'explorer'
            dungeon.contract_progress = 3
            before = self.p.gold
            self.finish(dungeon, cleared)
            self.assertEqual(self.p.gold - before, 40 if cleared else 0)

    def test_trap_displays_damage_before_pause(self):
        dungeon = game.Dungeon(self.p, 1)
        self.p.base_hp += 200
        self.p.hp = 200
        output = io.StringIO()
        def paused():
            self.assertIn('187/', output.getvalue())
            self.assertIn('HP:', output.getvalue())
        with patch.object(game.random, 'choice', return_value=('An ancient glyph explodes!', 'int')), patch.object(game.random, 'randint', side_effect=[-100, 11]), patch.object(game, 'pause', side_effect=paused), contextlib.redirect_stdout(output):
            dungeon._trap()
        self.assertEqual(self.p.hp, 187)

    def test_routes_keep_final_guardian(self):
        for depth in (1, 5, 20):
            dungeon = game.Dungeon(self.p, depth)
            for room in dungeon.rooms[:-1]:
                self.assertNotEqual(room['event'], room['alternative'])
            self.assertEqual(dungeon.rooms[-1]['event'], 'boss' if depth % 5 == 0 else 'miniboss')

    def test_camp_only_once(self):
        dungeon = game.Dungeon(self.p, 1)
        self.p.hp = 1
        with patch.object(game, 'get_choice', return_value=0), patch.object(game, 'pause'), contextlib.redirect_stdout(io.StringIO()):
            dungeon._camp()
            healed = self.p.hp
            dungeon._camp()
        self.assertGreater(healed, 1)
        self.assertEqual(self.p.hp, healed)

    def test_roundtrip_all_classes_and_existing_save(self):
        for cls in game.CLASSES:
            player = game.Player('Tester', cls)
            data = json.loads(json.dumps(player.to_dict()))
            self.assertEqual(game.Player.from_dict(data).to_dict(), data)
        if game.SAVE_FILE.exists():
            game.Player.from_dict(json.loads(game.SAVE_FILE.read_text()))

    def test_expedition_flow(self):
        dungeon = game.Dungeon(self.p, 1)
        dungeon.contract = 'explorer'
        dungeon.rooms = [{'type': 'Hall', 'event': 'empty', 'alternative': 'trap'} for _ in range(3)] + [{'type': 'Boss Chamber', 'event': 'miniboss'}]
        with patch.object(game, 'get_choice', return_value=0), patch.object(game, 'pause'), patch.object(game, 'clr'), patch.object(dungeon, '_run_room', return_value='continue'), contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(dungeon.run())
        self.assertEqual(dungeon.contract_progress, 3)
        self.assertEqual(self.p.max_depth_cleared, 1)
        self.assertEqual(self.p.gold, 90)


if __name__ == '__main__':
    unittest.main()
