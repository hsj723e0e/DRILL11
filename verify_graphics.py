"""프로젝트 폴더에서 실행: python verify_graphics.py (짧게 창이 열린다)."""

from unittest.mock import patch

import pico2d
import pico2d.pico2d as backend

import main


def verify_graphics():
    now = [100.0]
    render_copy = backend.SDL_RenderCopy

    def checked_render_copy(*args):
        result = render_copy(*args)
        if result != 0:
            raise RuntimeError('SDL 이미지 그리기에 실패했습니다.')
        return result

    pico2d.open_canvas(800, 600)
    try:
        assert bool(backend.renderer), 'SDL 렌더러 생성 실패'
        with patch('boy.monotonic', side_effect=lambda: now[0]), patch(
            'pico2d.pico2d.SDL_RenderCopy', side_effect=checked_render_copy,
        ):
            main.reset_world()
            main.render_world()
            assert main.boy.start_autorun()
            main.render_world()
            for frame in range(1, 500):
                now[0] = 100.0 + frame / 100
                main.update_world()
                main.render_world()
                assert 100 <= main.boy.x <= 700
            now[0] = 105.0
            main.update_world()
            main.render_world()
            assert main.boy.state == 'IDLE'
            assert not main.boy.invincible
            main.boy.start_autorun()
            main.boy.press_direction(-1)
            now[0] += 0.1
            main.update_world()
            main.render_world()
            assert main.boy.state == 'RUN'
            assert not main.boy.invincible
        print('PASS: SDL rendering, real images, 503 frames, timeout and cancel')
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    verify_graphics()
