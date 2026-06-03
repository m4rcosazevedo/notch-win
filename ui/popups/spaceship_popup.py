import math
import random

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPolygonF, QFont,
    QRadialGradient,
)

from ui.popups.base_popup import BasePopup

# ── Constants ─────────────────────────────────────────────────────────────────

GW = 460
GH = 380
SHIP_SPEED    = 6.0
BULLET_SPEED  = 10.0
FIRE_INTERVAL = 300
SPAWN_BASE    = 1700
AST_SPEED     = 1.6
MAX_SECS      = 180   # 3 minutes

# Milestones (ms) → target shot level
_POWERUP_MILESTONES = {60_000: 2, 120_000: 3}

_IDLE     = 0
_PLAYING  = 1
_GAMEOVER = 2
_WIN      = 3


# ── Game objects ──────────────────────────────────────────────────────────────

class _Star:
    def __init__(self, y: float = -1):
        self.x        = random.uniform(0, GW)
        self.y        = random.uniform(0, GH) if y < 0 else y
        self.size     = random.uniform(0.5, 1.8)
        self.alpha    = random.randint(70, 200)
        self.base_spd = random.uniform(0.25, 1.0)

    def update(self, level: int):
        self.y += self.base_spd * (1.0 + (level - 1) * 0.12)
        if self.y > GH + 2:
            self.x     = random.uniform(0, GW)
            self.y     = -2
            self.size  = random.uniform(0.5, 1.8)
            self.alpha = random.randint(70, 200)


class _Bullet:
    def __init__(self, x: float, y: float, vx: float = 0.0):
        self.x  = x
        self.y  = y
        self.vx = vx
        # vy mantém a magnitude total igual a BULLET_SPEED
        self.vy = -math.sqrt(max(0.0, BULLET_SPEED ** 2 - vx ** 2))
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.y < -12 or self.x < -12 or self.x > GW + 12:
            self.alive = False


class _Asteroid:
    def __init__(self, smult: float):
        self.x       = random.uniform(30, GW - 30)
        self.y       = -28.0
        self.r       = random.uniform(11, 27)
        spd          = AST_SPEED * smult * random.uniform(0.75, 1.4)
        drift        = math.radians(random.uniform(-22, 22))
        self.vx      = math.sin(drift) * spd
        self.vy      = max(0.5, math.cos(drift) * spd)
        self.rot     = 0.0
        self.rot_spd = random.uniform(-2.8, 2.8)
        self.alive   = True
        n            = random.randint(6, 10)
        self.pts     = [
            (math.cos(2 * math.pi * i / n) * self.r * random.uniform(0.58, 1.0),
             math.sin(2 * math.pi * i / n) * self.r * random.uniform(0.58, 1.0))
            for i in range(n)
        ]

    def update(self):
        self.x += self.vx; self.y += self.vy; self.rot += self.rot_spd
        if self.y > GH + 40 or self.x < -60 or self.x > GW + 60:
            self.alive = False


class _Particle:
    def __init__(self, x: float, y: float, color: QColor | None = None):
        angle      = random.uniform(0, 2 * math.pi)
        spd        = random.uniform(1.5, 5.0)
        self.x     = x; self.y = y
        self.vx    = math.cos(angle) * spd
        self.vy    = math.sin(angle) * spd
        self.life  = random.randint(14, 26)
        self.max_life = self.life
        self.r     = random.uniform(1.2, 3.0)
        self.color = color or QColor(200, 160, 80)
        self.alive = True

    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.12
        self.life -= 1
        if self.life <= 0:
            self.alive = False


class _PowerUp:
    """Bonus de tiro que cai do topo a cada 2 minutos."""

    def __init__(self, level: int):
        self.x     = random.uniform(60, GW - 60)
        self.y     = -24.0
        self.r     = 14.0
        self.vy    = 1.1
        self.rot   = 0.0
        self.level = level   # 2 → duplo, 3 → triplo
        self.alive = True

    @property
    def color(self) -> QColor:
        return QColor(255, 210, 30) if self.level == 2 else QColor(185, 70, 255)

    @property
    def glow_color(self) -> QColor:
        return QColor(255, 200, 0, 90) if self.level == 2 else QColor(170, 50, 255, 90)

    @property
    def label(self) -> str:
        return "x2" if self.level == 2 else "x3"

    def update(self):
        self.y   += self.vy
        self.rot += 2.2
        if self.y > GH + 24:
            self.alive = False


# ── Game canvas ───────────────────────────────────────────────────────────────

class _GameCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(GW, GH)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._stars     = [_Star() for _ in range(90)]
        self._bullets:  list[_Bullet]   = []
        self._asteroids: list[_Asteroid] = []
        self._particles: list[_Particle] = []
        self._powerups:  list[_PowerUp]  = []

        self._state      = _IDLE
        self._score      = 0
        self._ms         = 0
        self._level      = 1
        self._smult      = 1.0
        self._shot_level = 1       # 1 / 2 / 3 tiros por disparo
        self._spawned_pu: set[int] = set()  # milestones já gerados

        self._flash_msg  = ""      # mensagem breve ao coletar powerup
        self._flash_ms   = 0

        self._sx  = GW / 2.0
        self._sy  = GH - 60.0
        self._sr  = 13.0
        self._inv = 0

        self._mx    = GW / 2.0
        self._my    = GH / 2.0
        self._mdown = False

        self._loop   = QTimer(self); self._loop.setInterval(16)
        self._loop.timeout.connect(self._tick)
        self._ftimer = QTimer(self); self._ftimer.timeout.connect(self._fire)
        self._atimer = QTimer(self); self._atimer.timeout.connect(self._spawn)

    # ── Public ────────────────────────────────────────────────────────────────

    def restart(self):
        self._bullets.clear(); self._asteroids.clear()
        self._particles.clear(); self._powerups.clear()
        self._score = 0; self._ms = 0; self._level = 1; self._smult = 1.0
        self._shot_level = 1; self._spawned_pu.clear()
        self._flash_msg = ""; self._flash_ms = 0
        self._sx = GW / 2.0; self._sy = GH - 60.0; self._inv = 0
        self._state = _PLAYING
        self._loop.start()
        self._ftimer.setInterval(FIRE_INTERVAL); self._ftimer.start()
        self._atimer.setInterval(SPAWN_BASE);    self._atimer.start()

    def stop(self):
        self._loop.stop(); self._ftimer.stop(); self._atimer.stop()
        self._powerups.clear()
        self._state = _IDLE

    # ── Timers ────────────────────────────────────────────────────────────────

    def _tick(self):
        self._ms += 16
        secs = self._ms / 1000.0
        self._level = int(secs / 30) + 1
        self._smult = 1.0 + (self._level - 1) * 0.20

        fi = max(100, FIRE_INTERVAL - (self._level - 1) * 16)
        if self._ftimer.interval() != fi:
            self._ftimer.setInterval(fi)
        si = max(350, SPAWN_BASE - (self._level - 1) * 150)
        if self._atimer.interval() != si:
            self._atimer.setInterval(si)

        if secs >= MAX_SECS:
            self._state = _WIN; self._stop_all(); self.update(); return

        # Powerup milestone spawn
        for ms_mark, target_lvl in _POWERUP_MILESTONES.items():
            if self._ms >= ms_mark and ms_mark not in self._spawned_pu:
                self._spawned_pu.add(ms_mark)
                self._powerups.append(_PowerUp(target_lvl))

        for s in self._stars: s.update(self._level)

        # Ship movement
        if self._mdown:
            dx = self._mx - self._sx; dy = self._my - self._sy
            d  = math.hypot(dx, dy)
            if d > 3:
                mv = min(SHIP_SPEED, d)
                self._sx += (dx / d) * mv; self._sy += (dy / d) * mv
        self._sx = max(self._sr, min(GW - self._sr, self._sx))
        self._sy = max(self._sr, min(GH - self._sr, self._sy))
        if self._inv > 0:
            self._inv -= 1

        for b in self._bullets:   b.update()
        for a in self._asteroids: a.update()
        for pt in self._particles: pt.update()
        for pu in self._powerups:  pu.update()
        self._bullets   = [b  for b  in self._bullets   if b.alive]
        self._asteroids = [a  for a  in self._asteroids if a.alive]
        self._particles = [pt for pt in self._particles if pt.alive]
        self._powerups  = [pu for pu in self._powerups  if pu.alive]

        # Bullet ↔ asteroid
        for b in self._bullets:
            for a in self._asteroids:
                if b.alive and a.alive and math.hypot(b.x - a.x, b.y - a.y) < a.r + 4:
                    b.alive = a.alive = False
                    self._score += max(1, int(a.r / 7))
                    for _ in range(random.randint(4, 9)):
                        self._particles.append(_Particle(a.x, a.y))

        # Ship ↔ powerup
        for pu in self._powerups:
            if pu.alive and math.hypot(self._sx - pu.x, self._sy - pu.y) < self._sr + pu.r:
                pu.alive = False
                self._shot_level = pu.level
                self._flash_msg  = f"TIRO DUPLO!" if pu.level == 2 else "TIRO TRIPLO!"
                self._flash_ms   = 1800
                for _ in range(18):
                    self._particles.append(_Particle(pu.x, pu.y, pu.color))

        if self._flash_ms > 0:
            self._flash_ms = max(0, self._flash_ms - 16)

        # Ship ↔ asteroid
        if self._inv == 0:
            for a in self._asteroids:
                if a.alive and math.hypot(self._sx - a.x, self._sy - a.y) < self._sr + a.r * 0.6:
                    self._state = _GAMEOVER; self._stop_all(); self.update(); return

        self.update()

    def _fire(self):
        if self._state != _PLAYING:
            return
        bx, by = self._sx, self._sy - self._sr - 2
        if self._shot_level == 1:
            self._bullets.append(_Bullet(bx, by))
        elif self._shot_level == 2:
            self._bullets.append(_Bullet(bx - 5, by))
            self._bullets.append(_Bullet(bx + 5, by))
        else:
            sv = BULLET_SPEED * math.sin(math.radians(15))   # ≈ 2.59 px/frame
            self._bullets.append(_Bullet(bx, by, -sv))  # -15° (esquerda)
            self._bullets.append(_Bullet(bx, by,  0.0)) #   0° (centro)
            self._bullets.append(_Bullet(bx, by, +sv))  # +15° (direita)

    def _spawn(self):
        if self._state == _PLAYING:
            n = 1 + (self._level - 1) // 3
            for _ in range(min(n, 5)):
                self._asteroids.append(_Asteroid(self._smult))

    def _stop_all(self):
        self._loop.stop(); self._ftimer.stop(); self._atimer.stop()

    # ── Events ────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        self._mx = event.position().x()
        self._my = event.position().y()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._state in (_IDLE, _GAMEOVER, _WIN):
            self.restart()
        self._mdown = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mdown = False

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(0, 0, GW, GH, QColor(4, 4, 16))
        self._paint_stars(p)

        if self._state == _IDLE:
            self._paint_idle(p); p.end(); return

        self._paint_particles(p)
        self._paint_powerups(p)
        self._paint_bullets(p)
        self._paint_asteroids(p)
        self._paint_ship(p)
        self._paint_hud(p)
        self._paint_flash(p)

        if self._state == _GAMEOVER:
            secs = self._ms // 1000
            self._paint_overlay(
                p, "GAME OVER", QColor(255, 70, 70),
                f"Sobreviveu  {secs // 60:02d}:{secs % 60:02d}  ·  {self._score} pts",
                "Clique para jogar novamente",
            )
        elif self._state == _WIN:
            self._paint_overlay(
                p, "VOCÊ SOBREVIVEU! 🏆", QColor(80, 255, 130),
                "5 minutos completos!",
                f"Pontuação final: {self._score} pts  —  Clique para jogar novamente",
            )
        p.end()

    def _paint_stars(self, p: QPainter):
        p.setPen(Qt.PenStyle.NoPen)
        for s in self._stars:
            p.setBrush(QBrush(QColor(200, 215, 255, s.alpha)))
            p.drawEllipse(QPointF(s.x, s.y), s.size, s.size)

    def _paint_particles(self, p: QPainter):
        p.setPen(Qt.PenStyle.NoPen)
        for pt in self._particles:
            alpha = int(210 * pt.life / pt.max_life)
            c = QColor(pt.color); c.setAlpha(alpha)
            p.setBrush(QBrush(c))
            p.drawEllipse(QPointF(pt.x, pt.y), pt.r, pt.r)

    def _paint_powerups(self, p: QPainter):
        pulse = 0.88 + 0.12 * math.sin(self._ms / 180)
        for pu in self._powerups:
            # Outer glow
            glow = QRadialGradient(pu.x, pu.y, pu.r * 2.4 * pulse)
            gc = QColor(pu.glow_color)
            glow.setColorAt(0.0, gc)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(pu.x, pu.y), pu.r * 2.4 * pulse, pu.r * 2.4 * pulse)

            # 5-pointed star body
            p.save()
            p.translate(pu.x, pu.y)
            p.rotate(pu.rot)
            star_pts = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                r     = pu.r if i % 2 == 0 else pu.r * 0.42
                star_pts.append(QPointF(math.cos(angle) * r, math.sin(angle) * r))
            p.setBrush(QBrush(pu.color))
            p.setPen(QPen(QColor(255, 255, 255, 160), 1.0))
            p.drawPolygon(QPolygonF(star_pts))
            p.restore()

            # Label below the star
            lc = QColor(255, 240, 120) if pu.level == 2 else QColor(220, 150, 255)
            p.setPen(QPen(lc))
            p.setFont(QFont("SF Pro Text", 8, QFont.Weight.Bold))
            p.drawText(QRectF(pu.x - 12, pu.y + pu.r + 3, 24, 13),
                       Qt.AlignmentFlag.AlignCenter, pu.label)

    def _paint_bullets(self, p: QPainter):
        p.setPen(Qt.PenStyle.NoPen)
        for b in self._bullets:
            angle = math.degrees(math.atan2(b.vx, -b.vy))  # ângulo em relação ao "cima"
            grad = QRadialGradient(b.x, b.y, 6)
            grad.setColorAt(0, QColor(170, 245, 255, 240))
            grad.setColorAt(1, QColor(60, 160, 255, 0))
            p.save()
            p.translate(b.x, b.y)
            p.rotate(angle)
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(0, 0), 3.5, 7)
            p.restore()

    def _paint_asteroids(self, p: QPainter):
        for a in self._asteroids:
            p.save()
            p.translate(a.x, a.y); p.rotate(a.rot)
            p.setBrush(QBrush(QColor(118, 120, 140)))
            p.setPen(QPen(QColor(195, 198, 215, 190), 1.1))
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in a.pts]))
            p.restore()

    def _paint_ship(self, p: QPainter):
        x, y, r = self._sx, self._sy, self._sr

        # Engine glow — color shifts with shot level
        if self._shot_level == 3:
            ec = QColor(160, 30, 255, 150)
        elif self._shot_level == 2:
            ec = QColor(255, 180, 0, 130)
        else:
            ec = QColor(30, 100, 255, 150)
        eg = QRadialGradient(x, y + r + 3, r * 2.2)
        eg.setColorAt(0.0, ec); eg.setColorAt(0.5, QColor(0, 0, 0, 50)); eg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(eg)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(x, y + r + 3), r * 2.2, r * 1.4)

        if self._inv > 0 and (self._inv // 4) % 2 == 1:
            return

        # Body — hull color reflects power level
        if self._shot_level == 3:
            hull = QColor(190, 80, 255); rim = QColor(220, 160, 255)
        elif self._shot_level == 2:
            hull = QColor(255, 195, 20); rim = QColor(255, 235, 120)
        else:
            hull = QColor(65, 185, 255); rim = QColor(155, 225, 255)

        body = QPolygonF([
            QPointF(x,            y - r),
            QPointF(x + r * 0.72, y + r * 0.72),
            QPointF(x,            y + r * 0.32),
            QPointF(x - r * 0.72, y + r * 0.72),
        ])
        p.setBrush(QBrush(hull)); p.setPen(QPen(rim, 1.4))
        p.drawPolygon(body)

        # Cockpit
        p.setBrush(QBrush(QColor(10, 30, 70, 210))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(x, y - r * 0.14), r * 0.27, r * 0.32)

        # Thruster flame
        fl_h = r * 0.5 + (self._ms % 200) / 200 * r * 0.3
        flame = QPolygonF([
            QPointF(x - r * 0.28, y + r * 0.5),
            QPointF(x,             y + r * 0.7 + fl_h),
            QPointF(x + r * 0.28, y + r * 0.5),
        ])
        p.setBrush(QBrush(QColor(80, 160, 255, 180))); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(flame)

    def _paint_hud(self, p: QPainter):
        remaining_ms = max(0, MAX_SECS * 1000 - self._ms)
        mins = remaining_ms // 60000
        secs = (remaining_ms // 1000) % 60

        p.setBrush(QBrush(QColor(0, 0, 20, 160)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, GW, 30), 0, 0)

        p.setPen(QPen(QColor(185, 215, 255, 215)))
        p.setFont(QFont("SF Pro Text", 10, QFont.Weight.Bold))
        p.drawText(10, 18, f"⏱ {mins:02d}:{secs:02d}")

        p.setPen(QPen(QColor(160, 195, 255, 200)))
        p.setFont(QFont("SF Pro Text", 10))
        p.drawText(0, 18, GW, 0, Qt.AlignmentFlag.AlignHCenter, f"Nível {self._level}")
        p.drawText(GW - 90, 18, f"🎯 {self._score} pts")

        # Shot-level indicator (dots below score)
        if self._shot_level > 1:
            dot_color = QColor(255, 218, 50) if self._shot_level == 2 else QColor(200, 100, 255)
            dots = "● ●" if self._shot_level == 2 else "● ● ●"
            p.setPen(QPen(dot_color))
            p.setFont(QFont("SF Pro Text", 8, QFont.Weight.Bold))
            p.drawText(QRectF(GW - 88, 20, 80, 11), Qt.AlignmentFlag.AlignRight, dots)

        # Speed bar
        bar_w = 90; bar_x = GW // 2 - bar_w // 2; bar_y = 24
        p.setBrush(QBrush(QColor(30, 30, 60, 180))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, 3), 1.5, 1.5)
        fill = min(1.0, (self._smult - 1.0) / 2.0)
        if fill > 0:
            r2 = int(60 + 195 * fill); g2 = int(190 - 150 * fill); b2 = int(255 - 210 * fill)
            p.setBrush(QBrush(QColor(r2, g2, b2)))
            p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w * fill, 3), 1.5, 1.5)

    def _paint_flash(self, p: QPainter):
        if self._flash_ms <= 0 or not self._flash_msg:
            return
        # Fade in quickly, hold, then fade out
        t = self._flash_ms / 1800
        alpha = int(min(1.0, t * 6) * 255) if t > 0.7 else int(t / 0.7 * 255)
        rise  = (1.0 - t) * 35

        if "TRIPLO" in self._flash_msg:
            col = QColor(210, 120, 255, alpha)
        else:
            col = QColor(255, 225, 60, alpha)

        p.setPen(QPen(col))
        p.setFont(QFont("SF Pro Display", 17, QFont.Weight.Bold))
        p.drawText(QRectF(0, GH / 2 - 55 - rise, GW, 34), Qt.AlignmentFlag.AlignCenter, self._flash_msg)

    def _paint_idle(self, p: QPainter):
        p.setPen(QPen(QColor(130, 195, 255)))
        p.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        p.drawText(QRectF(0, GH / 2 - 70, GW, 50), Qt.AlignmentFlag.AlignCenter, "🚀  Navinha")

        lines = [
            (12, QColor(160, 200, 240, 220), "Clique para começar"),
            (11, QColor(120, 160, 200, 180), "Segure o mouse para mover  ·  Tiros automáticos"),
            (10, QColor( 90, 130, 170, 150), "Desvie dos asteroides  ·  Objetivo: durar 5 minutos"),
            ( 9, QColor(200, 160,  50, 160), "★  Colete a estrela dourada aos 2min para tiro duplo"),
            ( 9, QColor(180,  80, 255, 150), "★  Colete a estrela roxa aos 4min para tiro triplo"),
        ]
        base_y = GH / 2 + 2
        for size, color, text in lines:
            p.setPen(QPen(color)); p.setFont(QFont("SF Pro Text", size))
            p.drawText(QRectF(0, base_y, GW, 24), Qt.AlignmentFlag.AlignCenter, text)
            base_y += 22

    def _paint_overlay(self, p: QPainter, title: str, title_col: QColor,
                       sub1: str, sub2: str):
        p.fillRect(0, 0, GW, GH, QColor(0, 0, 10, 165))
        cy = GH // 2
        p.setPen(QPen(title_col))
        p.setFont(QFont("SF Pro Display", 21, QFont.Weight.Bold))
        p.drawText(QRectF(0, cy - 62, GW, 40), Qt.AlignmentFlag.AlignCenter, title)
        p.setPen(QPen(QColor(200, 220, 255, 230)))
        p.setFont(QFont("SF Pro Text", 12))
        p.drawText(QRectF(0, cy - 14, GW, 30), Qt.AlignmentFlag.AlignCenter, sub1)
        p.setPen(QPen(QColor(145, 175, 215, 190)))
        p.setFont(QFont("SF Pro Text", 10))
        p.drawText(QRectF(0, cy + 22, GW, 26), Qt.AlignmentFlag.AlignCenter, sub2)


# ── Popup wrapper ─────────────────────────────────────────────────────────────

class SpaceshipPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("ss-card")
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("ss-header")
        hh  = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("🚀  Navinha"); ttl.setObjectName("ss-title")
        cls = QPushButton("✕"); cls.setObjectName("ss-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self._on_close)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        self._game = _GameCanvas()
        v.addWidget(self._game)
        outer.addWidget(self._card)

    def _on_close(self):
        self._game.stop()
        self.hide()

    def apply_theme(self, bg: str, border: str, mode: str):
        muted = "rgba(0,0,0,0.45)" if mode == "light" else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)" if mode == "light" else "rgba(255,255,255,0.07)"
        self._card.setStyleSheet(f"""
            QFrame#ss-card {{
                background: #04040f; border-radius: 16px; border: 1px solid {border};
            }}
            QFrame#ss-header {{
                background: transparent; border-bottom: 1px solid {sep};
            }}
            QLabel#ss-title {{
                color: #7ecfff; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#ss-close {{
                color: {muted}; background: transparent; border: none;
                border-radius: 11px; font-size: 12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#ss-close:hover {{ background: rgba(255,80,80,0.15); color: #ff453a; }}
        """)
