from pico2d import load_image
from transitions import Machine
from math import pi
from time import monotonic
from autorun import AutoRun

class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = []
        self.invincible = False
        self.autorun = AutoRun()
        self.image = load_image('animation_sheet.png')
        self.idle_started_at = monotonic()
        self.idle_elapsed = 0.0
        self.last_updated_at = self.idle_started_at
        self.machine = Machine(
            model=self,
            states=[
                'IDLE', 'RUN', 'SLEEP',
                {'name': 'AUTORUN', 'on_enter': 'enter_autorun',
                 'on_exit': 'exit_autorun'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )
        # IDLE 상태를 유지하면서 매 프레임 대기 애니메이션을 갱신한다.
        self.machine.add_transition(
            trigger='animate',
            source='IDLE',
            dest=None,
            after='update_idle',
        )
        self.machine.add_transition('sleep', 'IDLE', 'SLEEP')
        self.machine.add_transition(
            'start_run', 'IDLE', 'RUN', before='pause_idle_timer',
        )
        self.machine.add_transition(
            'start_run', 'SLEEP', 'RUN', before='reset_idle',
        )
        self.machine.add_transition(
            'stop_run', 'RUN', 'IDLE', after='resume_idle_timer',
        )
        self.machine.add_transition(
            'wake_up', 'SLEEP', 'IDLE', after='reset_idle',
        )
        self.machine.add_transition('begin_autorun', ['IDLE', 'RUN'], 'AUTORUN')
        self.machine.add_transition(
            'finish_autorun', 'AUTORUN', 'IDLE',
            after=['clear_directions', 'reset_idle'],
        )
        self.machine.add_transition(
            'cancel_autorun', 'AUTORUN', 'RUN', after='reset_idle',
        )

    def start_autorun(self):
        if self.state not in ('IDLE', 'RUN'):
            return False
        self.begin_autorun()
        return True

    def enter_autorun(self):
        self.autorun.enter(self, monotonic())

    def exit_autorun(self):
        self.autorun.exit(self)

    def clear_directions(self):
        self.pressed_directions.clear()

    def update(self):
        now = monotonic()
        elapsed = now - self.last_updated_at
        self.last_updated_at = now
        if self.state == 'IDLE':
            if self.idle_elapsed + now - self.idle_started_at >= 5.0:
                self.sleep()
            else:
                self.animate()
        elif self.state == 'RUN':
            self.x = max(25, min(775, self.x + self.face_dir * 200 * elapsed))
            self.frame = (self.frame + 1) % 8
        elif self.state == 'AUTORUN':
            self.autorun.update(self, elapsed, now)

    def press_direction(self, direction):
        if direction in self.pressed_directions:
            return
        self.pressed_directions.append(direction)
        self.face_dir = direction
        if self.state == 'AUTORUN':
            self.cancel_autorun()
        elif self.state in ('IDLE', 'SLEEP'):
            self.start_run()

    def release_direction(self, direction):
        if direction in self.pressed_directions:
            self.pressed_directions.remove(direction)
        if self.state == 'RUN':
            if self.pressed_directions:
                self.face_dir = self.pressed_directions[-1]
            else:
                self.stop_run()

    def pause_idle_timer(self):
        now = monotonic()
        self.idle_elapsed += now - self.idle_started_at
        self.last_updated_at = now
        self.frame = 0

    def resume_idle_timer(self):
        self.idle_started_at = monotonic()
        self.frame = 0

    def reset_idle(self):
        self.frame = 0
        self.idle_elapsed = 0.0
        self.idle_started_at = monotonic()
        self.last_updated_at = self.idle_started_at

    def update_idle(self):
        self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.state == 'AUTORUN':
            self.autorun.draw(self)
        elif self.state == 'SLEEP':
            row = 300 if self.face_dir == 1 else 200
            angle = (pi / 2) * self.face_dir
            self.image.clip_composite_draw(
                0, row, 100, 100, angle, '', self.x, self.y - 25,
                100, 100,
            )
        elif self.state == 'RUN':
            row = 100 if self.face_dir == 1 else 0
            self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
        elif self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
