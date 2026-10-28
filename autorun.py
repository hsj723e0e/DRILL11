"""소년의 자동 무적 런 상태 동작."""


class AutoRun:
    SPEED = 400.0
    SCALE = 2.0
    DURATION = 5.0
    SPRITE_SIZE = 100
    CANVAS_WIDTH = 800

    def enter(self, boy, now):
        self.started_at = now
        boy.frame = 0
        boy.last_updated_at = now
        boy.invincible = True

    def exit(self, boy):
        boy.invincible = False

    def update(self, boy, elapsed, now):
        boy.x += boy.face_dir * self.SPEED * elapsed
        boy.frame = (boy.frame + 1) % 8
