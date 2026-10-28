"""그래픽 창 없이 실제 상태 머신으로 자동 런 동작을 검증한다."""

import unittest
from unittest.mock import Mock, patch

from boy import Boy


class AutoRunTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.clock = patch('boy.monotonic', side_effect=lambda: self.now)
        self.images = patch('boy.load_image', return_value=Mock())
        self.clock.start()
        self.images.start()
        self.addCleanup(self.clock.stop)
        self.addCleanup(self.images.stop)
        self.boy = Boy()

    def advance(self, seconds):
        self.now += seconds
        self.boy.update()

    def test_only_idle_can_enter_and_repeated_activation_does_not_extend_time(self):
        self.assertTrue(self.boy.start_autorun())
        self.assertTrue(self.boy.invincible)
        self.advance(4)
        self.assertFalse(self.boy.start_autorun())
        self.advance(1)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertFalse(self.boy.invincible)
        self.boy.press_direction(1)
        self.assertFalse(self.boy.start_autorun())
        self.boy.release_direction(1)
        self.advance(5)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.assertFalse(self.boy.start_autorun())

    def test_automatic_speed_is_twice_normal_run_in_both_directions(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.boy = Boy()
                self.boy.face_dir = direction
                self.boy.start_autorun()
                self.advance(0.25)
                self.assertAlmostEqual(self.boy.x, 400 + direction * 100)
                self.assertEqual(self.boy.pressed_directions, [])

    def test_bounces_at_both_edges_and_preserves_overshoot(self):
        self.boy.start_autorun()
        self.advance(0.75)
        self.assertEqual((self.boy.x, self.boy.face_dir), (700, -1))
        self.advance(1.5)
        self.assertEqual((self.boy.x, self.boy.face_dir), (100, 1))
        self.advance(1.75)
        self.assertEqual((self.boy.x, self.boy.face_dir), (600, -1))

    def test_long_frame_can_cross_multiple_edges(self):
        self.boy.start_autorun()
        self.advance(4)
        self.assertEqual((self.boy.x, self.boy.face_dir), (600, -1))

    def test_entry_at_normal_run_edges_keeps_enlarged_sprite_inside(self):
        for x, expected in ((25, 100), (775, 700)):
            with self.subTest(x=x):
                self.boy = Boy()
                self.boy.x = x
                self.boy.start_autorun()
                self.assertEqual(self.boy.x, expected)

    def test_timeout_at_five_seconds_starts_fresh_idle_timer(self):
        self.advance(4)
        self.boy.start_autorun()
        self.advance(4.999)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.advance(0.001)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertFalse(self.boy.invincible)
        self.advance(4.999)
        self.assertEqual(self.boy.state, 'IDLE')
        self.advance(0.001)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_timeout_after_delayed_frame_and_reentry(self):
        self.boy.start_autorun()
        self.advance(8)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertTrue(self.boy.start_autorun())
        self.advance(4)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.advance(1)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_direction_key_cancels_and_restores_normal_speed(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.boy = Boy()
                self.boy.start_autorun()
                self.advance(0.25)
                self.boy.press_direction(direction)
                self.assertEqual(self.boy.state, 'RUN')
                self.assertFalse(self.boy.invincible)
                x = self.boy.x
                self.advance(0.25)
                self.assertAlmostEqual(self.boy.x, x + direction * 50)
                self.boy.release_direction(direction)
                self.assertEqual(self.boy.state, 'IDLE')

    def test_render_size_ground_height_and_direction_restore(self):
        for direction, row in ((-1, 0), (1, 100)):
            with self.subTest(direction=direction):
                self.boy = Boy()
                self.boy.face_dir = direction
                self.boy.start_autorun()
                self.boy.draw()
                self.boy.image.clip_draw.assert_called_with(
                    0, row, 100, 100, 400, 140, 200, 200,
                )
                self.boy.press_direction(direction)
                self.boy.draw()
                self.boy.image.clip_draw.assert_called_with(
                    0, row, 100, 100, 400, 90,
                )
                self.boy.release_direction(direction)
                self.boy.start_autorun()
                self.advance(5)
                self.boy.draw()
                idle_row = 300 if direction == 1 else 200
                self.boy.image.clip_draw.assert_called_with(
                    0, idle_row, 100, 100, 400, 90,
                )


if __name__ == '__main__':
    unittest.main()
