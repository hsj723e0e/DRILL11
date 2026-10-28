"""게임 입력 전달과 기존 수동 조작을 함께 검증한다."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main


class InputTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        for target, options in (
            ('boy.monotonic', {'side_effect': lambda: self.now}),
            ('boy.load_image', {'return_value': Mock()}),
            ('grass.load_image', {'return_value': Mock()}),
        ):
            patcher = patch(target, **options)
            patcher.start()
            self.addCleanup(patcher.stop)
        main.running = True
        main.reset_world()

    def send(self, *events):
        with patch('main.get_events', return_value=[
            SimpleNamespace(type=event_type, key=key)
            for event_type, key in events
        ]):
            main.handle_events()

    def advance(self, seconds):
        self.now += seconds
        main.update_world()

    def test_a_key_release_and_repeat_do_not_interrupt_or_extend_autorun(self):
        self.send((main.SDL_KEYDOWN, main.SDLK_a))
        self.send((main.SDL_KEYUP, main.SDLK_a))
        self.advance(4)
        self.assertEqual(main.boy.state, 'AUTORUN')
        self.send((main.SDL_KEYDOWN, main.SDLK_a))
        self.advance(1)
        self.assertEqual(main.boy.state, 'IDLE')

    def test_arrow_cancels_autorun_in_both_directions(self):
        for key, direction in ((main.SDLK_LEFT, -1), (main.SDLK_RIGHT, 1)):
            with self.subTest(key=key):
                self.send((main.SDL_KEYDOWN, main.SDLK_a))
                self.send((main.SDL_KEYDOWN, key))
                self.assertEqual(main.boy.state, 'RUN')
                self.assertEqual(main.boy.face_dir, direction)
                self.assertFalse(main.boy.invincible)
                self.send((main.SDL_KEYUP, key))
                self.assertEqual(main.boy.state, 'IDLE')

    def test_a_activates_while_running_but_is_ignored_while_sleeping(self):
        self.send((main.SDL_KEYDOWN, main.SDLK_RIGHT))
        self.send((main.SDL_KEYDOWN, main.SDLK_a))
        self.assertEqual(main.boy.state, 'AUTORUN')
        self.send((main.SDL_KEYUP, main.SDLK_RIGHT))
        self.advance(5)
        self.advance(5)
        self.send((main.SDL_KEYDOWN, main.SDLK_a))
        self.assertEqual(main.boy.state, 'SLEEP')

    def test_held_arrow_repeat_and_release_do_not_cancel_activation_from_run(self):
        for key, direction in ((main.SDLK_LEFT, -1), (main.SDLK_RIGHT, 1)):
            with self.subTest(key=key):
                main.reset_world()
                self.send((main.SDL_KEYDOWN, key), (main.SDL_KEYDOWN, main.SDLK_a))
                self.send((main.SDL_KEYDOWN, key))  # 계속 누른 키의 반복 입력
                self.assertEqual(main.boy.state, 'AUTORUN')
                self.assertTrue(main.boy.invincible)
                self.assertEqual(main.boy.face_dir, direction)
                self.send((main.SDL_KEYUP, key))
                x = main.boy.x
                self.advance(0.25)
                self.assertAlmostEqual(main.boy.x, x + direction * 100)
                self.assertEqual(main.boy.state, 'AUTORUN')
                self.send((main.SDL_KEYDOWN, key))  # 놓았다 다시 누르면 취소
                self.assertEqual(main.boy.state, 'RUN')
                self.assertFalse(main.boy.invincible)

    def test_opposite_arrow_cancels_activation_from_run(self):
        self.send(
            (main.SDL_KEYDOWN, main.SDLK_LEFT),
            (main.SDL_KEYDOWN, main.SDLK_a),
            (main.SDL_KEYDOWN, main.SDLK_RIGHT),
        )
        self.assertEqual(main.boy.state, 'RUN')
        self.assertEqual(main.boy.face_dir, 1)
        self.send((main.SDL_KEYUP, main.SDLK_RIGHT))
        self.assertEqual(main.boy.face_dir, -1)
        self.send((main.SDL_KEYUP, main.SDLK_LEFT))
        self.assertEqual(main.boy.state, 'IDLE')

    def test_timeout_clears_previously_held_direction(self):
        self.send((main.SDL_KEYDOWN, main.SDLK_LEFT), (main.SDL_KEYDOWN, main.SDLK_a))
        self.advance(5)
        self.assertEqual(main.boy.state, 'IDLE')
        self.assertEqual(main.boy.pressed_directions, [])
        self.send((main.SDL_KEYDOWN, main.SDLK_LEFT))
        self.assertEqual(main.boy.state, 'RUN')
        self.send((main.SDL_KEYUP, main.SDLK_LEFT))
        self.assertEqual(main.boy.state, 'IDLE')

    def test_repeated_arrow_and_overlapping_directions_after_cancel(self):
        self.send(
            (main.SDL_KEYDOWN, main.SDLK_a),
            (main.SDL_KEYDOWN, main.SDLK_LEFT),
            (main.SDL_KEYDOWN, main.SDLK_LEFT),
            (main.SDL_KEYDOWN, main.SDLK_RIGHT),
        )
        self.assertEqual(main.boy.pressed_directions, [-1, 1])
        self.assertEqual(main.boy.face_dir, 1)
        self.send((main.SDL_KEYUP, main.SDLK_RIGHT))
        self.assertEqual(main.boy.face_dir, -1)
        self.assertEqual(main.boy.state, 'RUN')
        self.send((main.SDL_KEYUP, main.SDLK_LEFT))
        self.assertEqual(main.boy.state, 'IDLE')

    def test_normal_run_keeps_speed_and_screen_limits(self):
        self.send((main.SDL_KEYDOWN, main.SDLK_RIGHT))
        self.advance(0.25)
        self.assertAlmostEqual(main.boy.x, 450)
        self.advance(10)
        self.assertEqual(main.boy.x, 775)
        self.send((main.SDL_KEYDOWN, main.SDLK_LEFT))
        self.advance(10)
        self.assertEqual(main.boy.x, 25)

    def test_sleep_wake_and_direction_wake_still_work(self):
        self.advance(5)
        self.assertEqual(main.boy.state, 'SLEEP')
        self.send((main.SDL_KEYDOWN, main.SDLK_SPACE))
        self.assertEqual(main.boy.state, 'IDLE')
        self.advance(5)
        self.send((main.SDL_KEYDOWN, main.SDLK_LEFT))
        self.assertEqual(main.boy.state, 'RUN')
        self.assertEqual(main.boy.face_dir, -1)

    def test_idle_timer_resumes_after_run_but_resets_after_autorun_cancel(self):
        self.advance(4)
        self.send((main.SDL_KEYDOWN, main.SDLK_RIGHT))
        self.advance(1)
        self.send((main.SDL_KEYUP, main.SDLK_RIGHT))
        self.advance(1)
        self.assertEqual(main.boy.state, 'SLEEP')
        self.send((main.SDL_KEYDOWN, main.SDLK_SPACE))
        self.advance(4)
        self.send((main.SDL_KEYDOWN, main.SDLK_a))
        self.send((main.SDL_KEYDOWN, main.SDLK_LEFT))
        self.send((main.SDL_KEYUP, main.SDLK_LEFT))
        self.advance(1)
        self.assertEqual(main.boy.state, 'IDLE')

    def test_quit_and_escape_remain_available_during_autorun(self):
        for event in ((main.SDL_QUIT, None), (main.SDL_KEYDOWN, main.SDLK_ESCAPE)):
            with self.subTest(event=event):
                main.running = True
                main.boy.start_autorun()
                self.send(event)
                self.assertFalse(main.running)


if __name__ == '__main__':
    unittest.main()
