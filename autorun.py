"""소년의 자동 무적 런 상태 동작."""


class AutoRun:
    SPEED = 400.0
    SCALE = 2.0
    DURATION = 5.0
    SPRITE_SIZE = 100
    CANVAS_WIDTH = 800

    @property
    def left_edge(self):
        return self.SPRITE_SIZE * self.SCALE / 2

    @property
    def right_edge(self):
        return self.CANVAS_WIDTH - self.left_edge

    def enter(self, boy, now):
        self.started_at = now
        boy.frame = 0
        boy.last_updated_at = now
        boy.invincible = True
        boy.x = max(self.left_edge, min(self.right_edge, boy.x))

    def exit(self, boy):
        boy.invincible = False

    def update(self, boy, elapsed, now):
        if now - self.started_at >= self.DURATION:
            boy.finish_autorun()
            return
        # 왕복 경로를 펼쳐 계산해 긴 프레임에서도 이동 거리와 경계를 보존한다.
        span = self.right_edge - self.left_edge
        offset = boy.x - self.left_edge
        phase = offset if boy.face_dir == 1 else 2 * span - offset
        phase = (phase + self.SPEED * elapsed) % (2 * span)
        if phase < span:
            boy.x = self.left_edge + phase
            boy.face_dir = 1
        else:
            boy.x = self.right_edge - (phase - span)
            boy.face_dir = -1
        boy.frame = (boy.frame + 1) % 8

    def draw(self, boy):
        row = 100 if boy.face_dir == 1 else 0
        size = self.SPRITE_SIZE * self.SCALE
        # 확대해도 기존 스프라이트의 발 위치가 유지되도록 중심을 올린다.
        y = boy.y + (size - self.SPRITE_SIZE) / 2
        boy.image.clip_draw(
            boy.frame * self.SPRITE_SIZE, row,
            self.SPRITE_SIZE, self.SPRITE_SIZE,
            boy.x, y, size, size,
        )
