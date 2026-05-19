import math
import random

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QPainter, QPixmap, QPolygonF, QCursor,
)

from ui.popups.base_popup import BasePopup
from config import MONSTERS_DIR

_STRESS_MONSTERS = [
    {"name": "Slime",           "hp": 12, "time":  8, "color": (50,  200,  80), "kind": "slime"},
    {"name": "Morcego",         "hp": 15, "time":  9, "color": (110,  60, 160), "kind": "bat"},
    {"name": "Esqueleto",       "hp": 18, "time": 10, "color": (210, 200, 175), "kind": "skeleton"},
    {"name": "Fantasma",        "hp": 16, "time":  9, "color": (150, 180, 230), "kind": "ghost"},
    {"name": "Goblin",          "hp": 20, "time": 11, "color": ( 60, 160,  50), "kind": "goblin"},
    {"name": "Aranha",          "hp": 18, "time": 10, "color": ( 50,  35,  65), "kind": "spider"},
    {"name": "Orc",             "hp": 25, "time": 12, "color": (100, 140,  70), "kind": "orc"},
    {"name": "Dragão",          "hp": 30, "time": 13, "color": (160,  50, 190), "kind": "dragon"},
    {"name": "Demônio",         "hp": 35, "time": 14, "color": (210,  30,  30), "kind": "demon"},
    {"name": "Cavaleiro Negro", "hp": 40, "time": 16, "color": ( 25,  25,  40), "kind": "knight"},
]

_STRESS_LOSE_MSGS = [
    "O monstro venceu! Você estava devagar demais...\nDescanse um pouco e tente de novo!",
    "Derrota! O monstro riu na sua cara.\nVingança é um prato servido frio — e rápido.",
    "Você ficou paraliso de medo!\nO monstro aproveitou e foi embora vitorioso.",
    "Tempo esgotado! O monstro escapou.\nPróxima vez clique mais rápido, guerreiro!",
    "O monstro foi rápido demais para você desta vez.\nMas você vai melhorar — acredito em você!",
]

_STRESS_WIN_MSGS = [
    "Parabéns, guerreiro! Você destruiu todos os monstros!\nSua sanidade agradece — por enquanto.\nEles já estão se reagrupando nas sombras...",
    "10 monstros eliminados!\nInfelizmente seu chefe, sua ex e sua conta bancária\nainda estão vivos, mas foi uma boa tentativa.",
    "Vitória total! Os monstros fugiram!\nAs reuniões de segunda-feira de manhã continuam intactas, porém.",
    "Incrível! Você é imparável!\nPelo menos aqui no mundo virtual.\nQuer mais uma rodada?",
    "Os 10 monstros foram derrotados com maestria!\nO médico recomenda esta técnica — provavelmente.",
]

def _load_monster_pixmap(kind: str) -> "QPixmap | None":
    path = MONSTERS_DIR / f"{kind}.png"
    if not path.exists():
        return None
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    return pm.scaled(
        200, 200,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class _HPBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self._ratio = 1.0

    def set_ratio(self, r: float):
        self._ratio = max(0.0, min(1.0, r))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(0, 0, 0, 55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, h // 2, h // 2)
        if self._ratio > 0:
            fw = max(h, int(w * self._ratio))
            if self._ratio > 0.5:    clr = QColor(48, 209, 88)
            elif self._ratio > 0.25: clr = QColor(255, 190, 0)
            else:                    clr = QColor(255, 60, 60)
            p.setBrush(QBrush(clr))
            p.drawRoundedRect(0, 0, fw, h, h // 2, h // 2)
        p.end()


class _TimeBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._ratio = 1.0

    def set_ratio(self, r: float):
        self._ratio = max(0.0, min(1.0, r))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(0, 0, 0, 55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, h // 2, h // 2)
        if self._ratio > 0:
            fw = max(h, int(w * self._ratio))
            if self._ratio > 0.5:    clr = QColor(10, 132, 255)
            elif self._ratio > 0.25: clr = QColor(255, 149, 0)
            else:                    clr = QColor(255, 59, 48)
            p.setBrush(QBrush(clr))
            p.drawRoundedRect(0, 0, fw, h, h // 2, h // 2)
        p.end()


class _MonsterCanvas(QLabel):
    clicked_at = pyqtSignal(int, int)
    _cache: dict = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(252, 216)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setStyleSheet("background: rgb(26, 22, 36);")
        self._kind       = "slime"
        self._dead       = False
        self._flash      = False
        self._has_sprite = False
        self._dmg_pos: tuple | None = None
        self._flash_t = QTimer(self); self._flash_t.setSingleShot(True)
        self._flash_t.timeout.connect(self._end_flash)
        self._dmg_t = QTimer(self); self._dmg_t.setSingleShot(True)
        self._dmg_t.timeout.connect(self._end_dmg)

    @classmethod
    def _sprite(cls, kind: str):
        if kind not in cls._cache:
            cls._cache[kind] = _load_monster_pixmap(kind)
        return cls._cache[kind]

    def set_monster(self, kind: str, color: tuple, dead: bool = False):
        self._kind  = kind
        self._dead  = dead
        self._flash = False
        pm = self._sprite(kind)
        if pm is not None:
            self.setPixmap(pm)
            self._has_sprite = True
        else:
            self.setPixmap(QPixmap())
            self._has_sprite = False
        self.update()

    def do_hit(self, x: int, y: int):
        self._flash = True; self._dmg_pos = (x, y)
        self._flash_t.start(110); self._dmg_t.start(480)
        self.update()

    def _end_flash(self): self._flash = False; self.update()
    def _end_dmg(self):   self._dmg_pos = None; self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked_at.emit(int(e.position().x()), int(e.position().y()))

    def paintEvent(self, event):
        if self._has_sprite:
            super().paintEvent(event)
            p = QPainter(self)
            if self._dead:
                p.fillRect(self.rect(), QColor(26, 22, 36, 170))
            elif self._flash:
                p.fillRect(self.rect(), QColor(255, 30, 30, 80))
            if self._dmg_pos:
                x, y = self._dmg_pos
                p.setPen(QPen(QColor(255, 55, 55)))
                f = p.font(); f.setPixelSize(19); f.setBold(True); p.setFont(f)
                p.drawText(x - 8, max(22, y - 8), "−1")
            p.end()
        else:
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(26, 22, 36))
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cx, cy = self.width() // 2, self.height() // 2 + 14
            if self._dead:
                self._draw_dead(p, cx, cy)
            else:
                getattr(self, f"_draw_{self._kind}", self._draw_slime)(p, cx, cy)
                if self._flash:
                    p.fillRect(self.rect(), QColor(255, 0, 0, 52))
            if self._dmg_pos:
                x, y = self._dmg_pos
                p.setPen(QPen(QColor(255, 55, 55)))
                f = p.font(); f.setPixelSize(19); f.setBold(True); p.setFont(f)
                p.drawText(x - 8, max(22, y - 8), "−1")
            p.end()

    def _eye(self, p, cx, cy, r=6, col=QColor(255, 255, 255)):
        p.setBrush(QBrush(col)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
        p.setBrush(QBrush(QColor(18, 18, 18)))
        p.drawEllipse(QRectF(cx-r*.45, cy-r*.45, r*.9, r*.9))

    def _star(self, p, cx, cy, r):
        p.setPen(QPen(QColor(255, 220, 0), 2))
        for i in range(4):
            a = math.radians(i * 45)
            p.drawLine(int(cx+math.cos(a)*r), int(cy+math.sin(a)*r),
                       int(cx-math.cos(a)*r), int(cy-math.sin(a)*r))

    def _draw_dead(self, p, cx, cy):
        p.setBrush(QBrush(QColor(155, 155, 155))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-42, cy-52, 84, 78))
        pen = QPen(QColor(55, 55, 55), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for ox in (-18, 14):
            p.drawLine(int(cx+ox-9), int(cy-24), int(cx+ox+9), int(cy-8))
            p.drawLine(int(cx+ox+9), int(cy-24), int(cx+ox-9), int(cy-8))
        p.setBrush(QBrush(QColor(220, 55, 80))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(cx-8, cy+6, 16, 20), 8, 8)
        for dx, dy in [(-50, -42), (50, -38), (2, -72)]:
            self._star(p, cx+dx, cy+dy, 9)

    def _draw_slime(self, p, cx, cy):
        p.setBrush(QBrush(QColor(0,80,0,55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-50, cy+34, 100, 18))
        body = QColor(28, 138, 18); p.setBrush(QBrush(body))
        for dx,w,h in [(-36,13,28),(-16,15,36),(6,14,32),(26,12,24)]:
            p.drawRoundedRect(QRectF(cx+dx, cy+20, w, h), 5, 8)
        p.drawEllipse(QRectF(cx-52, cy-44, 104, 76))
        for ox,r in [(-30,20),(-4,26),(22,18),(36,14)]:
            p.drawEllipse(QRectF(cx+ox-r, cy-58, r*2, r*2))
        p.setBrush(QBrush(QColor(100, 240, 40, 65)))
        p.drawEllipse(QRectF(cx-34, cy-38, 28, 18))
        for ox in (-17, 16):
            p.setBrush(QBrush(QColor(140, 255, 0, 80))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(cx+ox-10, cy-22, 20, 20))
            p.setBrush(QBrush(QColor(210, 255, 30)))
            p.drawEllipse(QRectF(cx+ox-7, cy-19, 14, 14))
            p.setBrush(QBrush(QColor(8,8,8)))
            p.drawRect(QRectF(cx+ox-2, cy-18, 4, 12))
        p.setBrush(QBrush(QColor(8,55,5)))
        p.drawRoundedRect(QRectF(cx-16, cy+4, 32, 13), 4, 4)
        p.setBrush(QBrush(QColor(200,225,170)))
        for i in range(4):
            p.drawPolygon(QPolygonF([QPointF(cx-12+i*8,cy+4),QPointF(cx-8+i*8,cy+4),QPointF(cx-10+i*8,cy+13)]))

    def _draw_bat(self, p, cx, cy):
        body_c = QColor(62, 22, 102); dark = QColor(35, 10, 62)
        p.setPen(Qt.PenStyle.NoPen)
        mem = QColor(48, 18, 82, 225); p.setBrush(QBrush(mem))
        p.drawPolygon(QPolygonF([QPointF(cx-6,cy-18),QPointF(cx-104,cy-62),QPointF(cx-86,cy-6),QPointF(cx-48,cy+10),QPointF(cx-16,cy+6)]))
        p.drawPolygon(QPolygonF([QPointF(cx+6,cy-18),QPointF(cx+104,cy-62),QPointF(cx+86,cy-6),QPointF(cx+48,cy+10),QPointF(cx+16,cy+6)]))
        pen = QPen(QColor(88, 38, 138), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen)
        for tx,ty in [(-68,-50),(-46,-18),(-84,-12)]: p.drawLine(int(cx), int(cy-14), int(cx+tx), int(cy+ty))
        for tx,ty in [(68,-50),(46,-18),(84,-12)]: p.drawLine(int(cx), int(cy-14), int(cx+tx), int(cy+ty))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(body_c))
        p.drawEllipse(QRectF(cx-18, cy-26, 36, 46))
        p.drawEllipse(QRectF(cx-17, cy-54, 34, 32))
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-17,cy-50),QPointF(cx-9,cy-50),QPointF(cx-15,cy-82)]))
        p.drawPolygon(QPolygonF([QPointF(cx+9,cy-50),QPointF(cx+17,cy-50),QPointF(cx+15,cy-82)]))
        p.setBrush(QBrush(QColor(195, 75, 135)))
        p.drawPolygon(QPolygonF([QPointF(cx-15,cy-52),QPointF(cx-10,cy-52),QPointF(cx-14,cy-75)]))
        p.drawPolygon(QPolygonF([QPointF(cx+10,cy-52),QPointF(cx+15,cy-52),QPointF(cx+14,cy-75)]))
        for ox in (-8, 8):
            p.setBrush(QBrush(QColor(255,60,20,100))); p.drawEllipse(QRectF(cx+ox-7, cy-44, 14, 12))
            p.setBrush(QBrush(QColor(255,85,20))); p.drawEllipse(QRectF(cx+ox-5, cy-42, 10, 9))
            p.setBrush(QBrush(QColor(8,3,3))); p.drawEllipse(QRectF(cx+ox-3, cy-41, 6, 7))
        p.setBrush(QBrush(QColor(238,228,215)))
        p.drawPolygon(QPolygonF([QPointF(cx-7,cy-24),QPointF(cx-3,cy-24),QPointF(cx-5,cy-11)]))
        p.drawPolygon(QPolygonF([QPointF(cx+3,cy-24),QPointF(cx+7,cy-24),QPointF(cx+5,cy-11)]))
        p.setBrush(QBrush(dark))
        for dx in (-12, 0, 12):
            p.drawPolygon(QPolygonF([QPointF(cx+dx-3,cy+18),QPointF(cx+dx+3,cy+18),QPointF(cx+dx,cy+32)]))

    def _draw_skeleton(self, p, cx, cy):
        bone = QColor(222, 212, 180); shade = QColor(165, 155, 122)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-26, cy-76, 52, 50)); p.fillRect(int(cx-18), int(cy-32), 36, 14, bone)
        p.setBrush(QBrush(QColor(8,6,4)))
        p.drawEllipse(QRectF(cx-20,cy-62,16,15)); p.drawEllipse(QRectF(cx+4,cy-62,16,15))
        p.setBrush(QBrush(QColor(190,25,25,170)))
        p.drawEllipse(QRectF(cx-17,cy-59,10,9)); p.drawEllipse(QRectF(cx+7,cy-59,10,9))
        p.setBrush(QBrush(QColor(8,6,4))); p.drawEllipse(QRectF(cx-5,cy-44,10,8))
        p.setBrush(QBrush(bone))
        for i in range(5): p.fillRect(int(cx-14+i*7),int(cy-28),5,10,bone)
        p.setBrush(QBrush(QColor(8,6,4)))
        for i in range(4): p.fillRect(int(cx-11+i*7),int(cy-30),2,3,QColor(8,6,4))
        for i in range(5):
            p.setBrush(QBrush(bone if i%2==0 else shade))
            p.drawEllipse(QRectF(cx-8, cy-14+i*13, 16, 11))
        pen = QPen(bone, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        for j in range(3):
            y0 = cy-10+j*13
            p.drawArc(QRectF(cx-34,y0,34,18), 0, 160*16)
            p.drawArc(QRectF(cx,y0,34,18), 180*16,-160*16)
        pen2 = QPen(bone, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen2)
        p.drawLine(int(cx-8),int(cy-12), int(cx-40),int(cy-2))
        p.drawLine(int(cx-40),int(cy-2), int(cx-52),int(cy+30))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(shade))
        p.fillRect(int(cx-62),int(cy-48), 7, 52, shade)
        p.setBrush(QBrush(bone)); p.drawEllipse(QRectF(cx-67, cy-56, 18, 18))
        for a in range(0,360,60):
            ax = cx-58 + math.cos(math.radians(a))*12
            ay = cy-48 + math.sin(math.radians(a))*12
            p.drawEllipse(QRectF(ax-4, ay-4, 8, 8))
        pen2.setWidth(5); p.setPen(pen2)
        p.drawLine(int(cx+8),int(cy-12), int(cx+42),int(cy+6))
        p.drawLine(int(cx+42),int(cy+6), int(cx+50),int(cy+34))
        pen3 = QPen(bone, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen3)
        for dx in (-2,5,12): p.drawLine(int(cx+50),int(cy+34), int(cx+48+dx),int(cy+48))
        pen4 = QPen(bone, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen4)
        p.drawLine(int(cx-6),int(cy+54), int(cx-18),int(cy+94))
        p.drawLine(int(cx+6),int(cy+54), int(cx+18),int(cy+94))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(55,35,22,155)))
        p.drawPolygon(QPolygonF([QPointF(cx-14,cy+50),QPointF(cx+14,cy+50),QPointF(cx+10,cy+74),QPointF(cx,cy+68),QPointF(cx-10,cy+74)]))

    def _draw_ghost(self, p, cx, cy):
        p.setBrush(QBrush(QColor(70,110,210,45))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-64, cy-84, 128, 148))
        shroud = [
            QPointF(cx-42,cy-64), QPointF(cx-26,cy-84), QPointF(cx,cy-90),
            QPointF(cx+26,cy-84), QPointF(cx+42,cy-64), QPointF(cx+50,cy+8),
            QPointF(cx+40,cy+44), QPointF(cx+24,cy+24), QPointF(cx+12,cy+50),
            QPointF(cx,cy+30), QPointF(cx-12,cy+50), QPointF(cx-24,cy+24),
            QPointF(cx-40,cy+44), QPointF(cx-50,cy+8),
        ]
        p.setBrush(QBrush(QColor(128, 168, 238, 215))); p.drawPolygon(QPolygonF(shroud))
        p.setBrush(QBrush(QColor(6,8,30,210))); p.drawEllipse(QRectF(cx-30,cy-80,60,56))
        for ox in (-14, 14):
            p.setBrush(QBrush(QColor(30,70,190,80))); p.drawEllipse(QRectF(cx+ox-10, cy-64, 20, 18))
            p.setBrush(QBrush(QColor(155, 198, 255, 230))); p.drawEllipse(QRectF(cx+ox-7, cy-61, 14, 13))
            p.setBrush(QBrush(QColor(4,4,26))); p.drawEllipse(QRectF(cx+ox-4, cy-59, 8, 9))
        p.setBrush(QBrush(QColor(4,6,24,220))); p.drawEllipse(QRectF(cx-10, cy-40, 20, 16))
        arm = QColor(155, 188, 235, 205); p.setBrush(QBrush(arm))
        p.drawEllipse(QRectF(cx-70,cy-28,30,14)); p.drawEllipse(QRectF(cx+40,cy-28,30,14))
        pen = QPen(arm, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen)
        for dx in (-74,-66,-58): p.drawLine(int(cx+dx),int(cy-22), int(cx+dx-6),int(cy-8))
        for dx in (48,56,64):    p.drawLine(int(cx+dx),int(cy-22), int(cx+dx+6),int(cy-8))

    def _draw_goblin(self, p, cx, cy):
        skin = QColor(88, 148, 58); dark = QColor(55, 100, 35)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(skin))
        p.drawEllipse(QRectF(cx-24, cy-10, 48, 58)); p.drawEllipse(QRectF(cx-20, cy-30, 40, 38))
        p.drawEllipse(QRectF(cx-22, cy-58, 44, 38))
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-22,cy-46),QPointF(cx+22,cy-46),QPointF(cx+20,cy-38),QPointF(cx-20,cy-38)]))
        p.setBrush(QBrush(QColor(240,195,10)))
        p.drawEllipse(QRectF(cx-17,cy-46,12,10)); p.drawEllipse(QRectF(cx+5,cy-46,12,10))
        p.setBrush(QBrush(QColor(8,6,4)))
        p.drawEllipse(QRectF(cx-14,cy-44,6,6)); p.drawEllipse(QRectF(cx+8,cy-44,6,6))
        p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([QPointF(cx-22,cy-52),QPointF(cx-34,cy-76),QPointF(cx-14,cy-52)]))
        p.drawPolygon(QPolygonF([QPointF(cx+22,cy-52),QPointF(cx+34,cy-76),QPointF(cx+14,cy-52)]))
        p.setBrush(QBrush(QColor(30,18,8))); p.drawRoundedRect(QRectF(cx-13,cy-26,26,11), 3, 3)
        p.setBrush(QBrush(QColor(225,210,158)))
        for i in range(3):
            p.drawPolygon(QPolygonF([QPointF(cx-9+i*9,cy-26),QPointF(cx-5+i*9,cy-26),QPointF(cx-7+i*9,cy-17)]))
        p.setBrush(QBrush(skin)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx+20,cy-22,20,44)); p.drawEllipse(QRectF(cx+36,cy-38,18,28))
        axe_p = QPen(QColor(72,50,22),5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(axe_p)
        p.drawLine(int(cx+46),int(cy-46), int(cx+54),int(cy+22))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(155,155,178)))
        p.drawPolygon(QPolygonF([QPointF(cx+38,cy-62),QPointF(cx+62,cy-56),QPointF(cx+56,cy-34),QPointF(cx+42,cy-38)]))
        p.setBrush(QBrush(QColor(205,205,228)))
        p.drawPolygon(QPolygonF([QPointF(cx+40,cy-58),QPointF(cx+58,cy-53),QPointF(cx+52,cy-38),QPointF(cx+42,cy-42)]))
        p.setBrush(QBrush(skin)); p.drawEllipse(QRectF(cx-40,cy-18,20,44))
        pen = QPen(dark, 2); p.setPen(pen)
        for dx in (-38,-30,-22): p.drawLine(int(cx+dx),int(cy+26),int(cx+dx-5),int(cy+40))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(dark))
        p.drawEllipse(QRectF(cx-20,cy+44,18,28)); p.drawEllipse(QRectF(cx+2,cy+44,18,28))

    def _draw_spider(self, p, cx, cy):
        gold = QColor(210, 172, 38); skin = QColor(222, 192, 138)
        snake = QColor(38, 148, 38); dark_s = QColor(18, 92, 18)
        p.setPen(Qt.PenStyle.NoPen)
        for ang in range(0, 360, 33):
            a = math.radians(ang); dist = 50
            sx = cx + math.cos(a)*dist; sy = cy-12 + math.sin(a)*dist
            pen = QPen(snake, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen)
            mid_x = cx + math.cos(a)*dist*0.5 + math.cos(a+1.2)*10
            mid_y = cy-12 + math.sin(a)*dist*0.5 + math.sin(a+1.2)*10
            p.drawLine(int(cx+math.cos(a)*20), int(cy-12+math.sin(a)*20), int(mid_x), int(mid_y))
            p.drawLine(int(mid_x),int(mid_y), int(sx),int(sy))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(dark_s))
            p.drawEllipse(QRectF(sx-5,sy-5,10,8))
            p.setBrush(QBrush(QColor(255,200,0)))
            p.drawEllipse(QRectF(sx-4,sy-4,3,3)); p.drawEllipse(QRectF(sx+1,sy-4,3,3))
        p.setBrush(QBrush(skin)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-36, cy-50, 72, 72))
        p.setBrush(QBrush(gold))
        crown = [QPointF(cx-38,cy-28),QPointF(cx-38,cy-38),QPointF(cx-26,cy-48),QPointF(cx-14,cy-56),
                 QPointF(cx,cy-60),QPointF(cx+14,cy-56),QPointF(cx+26,cy-48),QPointF(cx+38,cy-38),QPointF(cx+38,cy-28)]
        p.drawPolygon(QPolygonF(crown))
        p.setBrush(QBrush(QColor(220,35,35))); p.drawEllipse(QRectF(cx-5,cy-60,10,10))
        p.setBrush(QBrush(QColor(38,182,222)))
        p.drawEllipse(QRectF(cx-22,cy-54,8,8)); p.drawEllipse(QRectF(cx+14,cy-54,8,8))
        p.setBrush(QBrush(skin)); p.drawEllipse(QRectF(cx-34, cy-46, 68, 68))
        for ox in (-14, 14):
            p.setBrush(QBrush(QColor(220,178,18))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(cx+ox-10, cy-22, 20, 18))
            p.setBrush(QBrush(QColor(8,8,8))); p.drawRect(QRectF(cx+ox-2, cy-21, 4, 15))
        p.setBrush(QBrush(QColor(178,148,98)))
        p.drawEllipse(QRectF(cx-8,cy-2,8,5)); p.drawEllipse(QRectF(cx,cy-2,8,5))
        p.setBrush(QBrush(QColor(185,58,58))); p.drawEllipse(QRectF(cx-14,cy+8,28,12))
        p.setBrush(QBrush(QColor(222,88,88))); p.drawEllipse(QRectF(cx-10,cy+10,20,7))
        p.setBrush(QBrush(gold))
        p.drawEllipse(QRectF(cx-42,cy-12,10,10)); p.drawEllipse(QRectF(cx+32,cy-12,10,10))

    def _draw_orc(self, p, cx, cy):
        armor = QColor(72, 72, 96); metal = QColor(118, 118, 148)
        dark = QColor(28, 28, 42); accent = QColor(185, 28, 28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(52, 38, 18))); p.fillRect(int(cx+30),int(cy-88),8,98, QColor(52,38,18))
        p.setBrush(QBrush(metal))
        p.drawPolygon(QPolygonF([QPointF(cx+18,cy-92),QPointF(cx+62,cy-84),QPointF(cx+54,cy-54),QPointF(cx+24,cy-60)]))
        p.setBrush(QBrush(QColor(200,205,230)))
        p.drawPolygon(QPolygonF([QPointF(cx+22,cy-88),QPointF(cx+56,cy-82),QPointF(cx+50,cy-58),QPointF(cx+26,cy-64)]))
        pen = QPen(QColor(240,242,255),2); p.setPen(pen)
        p.drawLine(int(cx+18),int(cy-92),int(cx+62),int(cy-84)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(armor)); p.drawEllipse(QRectF(cx-40,cy-16,80,78))
        p.setBrush(QBrush(metal))
        p.drawPolygon(QPolygonF([QPointF(cx-28,cy-14),QPointF(cx+28,cy-14),QPointF(cx+24,cy+38),QPointF(cx,cy+48),QPointF(cx-24,cy+38)]))
        p.setBrush(QBrush(accent)); p.drawEllipse(QRectF(cx-11,cy+8,22,22))
        pen = QPen(QColor(218,178,28),2); p.setPen(pen)
        p.drawLine(int(cx-7),int(cy+19),int(cx+7),int(cy+19))
        p.drawLine(int(cx),int(cy+12),int(cx),int(cy+26)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx-64,cy-24,34,30)); p.drawEllipse(QRectF(cx+30,cy-24,34,30))
        p.setBrush(QBrush(metal))
        p.drawEllipse(QRectF(cx-60,cy-22,26,24)); p.drawEllipse(QRectF(cx+34,cy-22,26,24))
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx+20,cy-10,22,50)); p.drawEllipse(QRectF(cx+20,cy+36,22,22))
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-65,cy-10),QPointF(cx-40,cy-10),QPointF(cx-40,cy+34),QPointF(cx-52,cy+56),QPointF(cx-65,cy+34)]))
        p.setBrush(QBrush(accent))
        p.drawPolygon(QPolygonF([QPointF(cx-60,cy-2),QPointF(cx-46,cy-2),QPointF(cx-46,cy+28),QPointF(cx-54,cy+42),QPointF(cx-60,cy+28)]))
        p.setBrush(QBrush(QColor(218,178,28))); p.drawEllipse(QRectF(cx-57,cy+10,10,10))
        p.setBrush(QBrush(armor)); p.drawEllipse(QRectF(cx-32,cy-70,64,60))
        p.fillRect(int(cx-34),int(cy-34),68,10,armor)
        p.setBrush(QBrush(dark)); p.fillRect(int(cx-26),int(cy-32),52,7,dark)
        p.setBrush(QBrush(accent))
        p.drawEllipse(QRectF(cx-20,cy-31,14,5)); p.drawEllipse(QRectF(cx+6,cy-31,14,5))
        p.drawPolygon(QPolygonF([QPointF(cx-7,cy-70),QPointF(cx+7,cy-70),QPointF(cx+5,cy-98),QPointF(cx,cy-104),QPointF(cx-5,cy-98)]))
        p.setBrush(QBrush(metal))
        p.fillRect(int(cx-28),int(cy+58),24,44,metal); p.fillRect(int(cx+4),int(cy+58),24,44,metal)
        p.setBrush(QBrush(armor))
        p.fillRect(int(cx-30),int(cy+94),28,14,armor); p.fillRect(int(cx+2),int(cy+94),28,14,armor)

    def _draw_dragon(self, p, cx, cy):
        bone = QColor(218, 208, 174); shade = QColor(155, 145, 112); glow = QColor(148, 228, 78)
        p.setPen(Qt.PenStyle.NoPen)
        tp = QPen(bone,14,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(tp)
        p.drawLine(int(cx+30),int(cy+38),int(cx+72),int(cy+70))
        tp.setWidth(9); p.setPen(tp); p.drawLine(int(cx+72),int(cy+70),int(cx+92),int(cy+50))
        tp.setWidth(6); p.setPen(tp); p.drawLine(int(cx+92),int(cy+50),int(cx+104),int(cy+62))
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(6):
            rs = 9 - i*0.5
            p.setBrush(QBrush(bone if i%2==0 else shade))
            p.drawEllipse(QRectF(cx-rs, cy-14+i*14, rs*2, rs*1.4))
            if i < 4:
                p.setBrush(QBrush(shade))
                p.drawPolygon(QPolygonF([QPointF(cx-5,cy-14+i*14),QPointF(cx+5,cy-14+i*14),QPointF(cx,cy-28+i*14)]))
        wp = QPen(bone,6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(wp)
        p.drawLine(int(cx-8),int(cy-12),int(cx-84),int(cy-62))
        p.drawLine(int(cx-8),int(cy),   int(cx-72),int(cy-28))
        p.drawLine(int(cx-8),int(cy+12),int(cx-60),int(cy+6))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(200,190,152,95)))
        p.drawPolygon(QPolygonF([QPointF(cx-8,cy-12),QPointF(cx-84,cy-62),QPointF(cx-72,cy-28),QPointF(cx-60,cy+6),QPointF(cx-8,cy+12)]))
        np_ = QPen(bone,16,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(np_)
        p.drawLine(int(cx),int(cy-18),int(cx-28),int(cy-52))
        p.drawLine(int(cx-28),int(cy-52),int(cx-18),int(cy-82))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-54,cy-108,66,54)); p.fillRect(int(cx-36),int(cy-78),38,24,bone)
        for i,(sx,sh) in enumerate([(-46,14),(-28,20),(-10,16)]):
            p.setBrush(QBrush(shade if i%2==0 else bone))
            p.drawPolygon(QPolygonF([QPointF(cx+sx,cy-106),QPointF(cx+sx+9,cy-106),QPointF(cx+sx+4,cy-122)]))
        p.setBrush(QBrush(QColor(8,8,8)))
        p.drawEllipse(QRectF(cx-52,cy-102,19,17)); p.drawEllipse(QRectF(cx-26,cy-102,19,17))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(cx-49,cy-99,13,11)); p.drawEllipse(QRectF(cx-23,cy-99,13,11))
        p.setBrush(QBrush(QColor(228,255,128,185)))
        p.drawEllipse(QRectF(cx-46,cy-98,7,7)); p.drawEllipse(QRectF(cx-20,cy-98,7,7))
        p.setBrush(QBrush(shade))
        for i in range(6):
            p.drawPolygon(QPolygonF([QPointF(cx-34+i*7,cy-78),QPointF(cx-30+i*7,cy-78),QPointF(cx-32+i*7,cy-64)]))
        p.setBrush(QBrush(bone))
        for i in range(5):
            p.drawPolygon(QPolygonF([QPointF(cx-31+i*7,cy-56),QPointF(cx-27+i*7,cy-56),QPointF(cx-29+i*7,cy-68)]))

    def _draw_demon(self, p, cx, cy):
        skin = QColor(115, 155, 90); coat = QColor(22, 32, 20)
        bolt = QColor(180, 180, 200); glow = QColor(230, 225, 60); black = QColor(12, 12, 12)
        p.setBrush(QBrush(QColor(0,0,0,90))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-40, cy+82, 80, 14))
        p.setBrush(QBrush(coat))
        p.fillRect(int(cx-28), int(cy+50), 22, 36, coat); p.fillRect(int(cx+6), int(cy+50), 22, 36, coat)
        p.fillRect(int(cx-30), int(cy+82), 26, 14, QColor(30,18,8)); p.fillRect(int(cx+4), int(cy+82), 26, 14, QColor(30,18,8))
        p.setBrush(QBrush(coat))
        p.drawPolygon(QPolygonF([QPointF(cx-44, cy-10), QPointF(cx+44, cy-10), QPointF(cx+50, cy+54), QPointF(cx-50, cy+54)]))
        p.setBrush(QBrush(QColor(35,46,32)))
        p.drawPolygon(QPolygonF([QPointF(cx-20,cy-10),QPointF(cx,cy+12),QPointF(cx-32,cy+28),QPointF(cx-40,cy+10)]))
        p.drawPolygon(QPolygonF([QPointF(cx+20,cy-10),QPointF(cx,cy+12),QPointF(cx+32,cy+28),QPointF(cx+40,cy+10)]))
        p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([QPointF(cx-44,cy-10), QPointF(cx-56,cy-8), QPointF(cx-88,cy-56), QPointF(cx-76,cy-62)]))
        p.drawPolygon(QPolygonF([QPointF(cx+44,cy-10), QPointF(cx+56,cy-8), QPointF(cx+88,cy-56), QPointF(cx+76,cy-62)]))
        p.drawEllipse(QRectF(cx-98, cy-72, 30, 26)); p.drawEllipse(QRectF(cx+68, cy-72, 30, 26))
        for i in range(4):
            p.drawEllipse(QRectF(cx-94+i*7, cy-80, 8, 8)); p.drawEllipse(QRectF(cx+68+i*7, cy-80, 8, 8))
        p.fillRect(int(cx-14), int(cy-22), 28, 18, skin)
        p.setBrush(QBrush(bolt))
        p.fillRect(int(cx-26), int(cy-20), 14, 8, bolt); p.fillRect(int(cx+12), int(cy-20), 14, 8, bolt)
        p.drawEllipse(QRectF(cx-28, cy-24, 10, 10)); p.drawEllipse(QRectF(cx+18, cy-24, 10, 10))
        for pts in [
            [(cx-22,cy-26),(cx-35,cy-44),(cx-25,cy-50),(cx-37,cy-64)],
            [(cx+22,cy-26),(cx+35,cy-44),(cx+25,cy-50),(cx+37,cy-64)],
        ]:
            pen = QPen(QColor(255,255,140,220), 2); p.setPen(pen)
            for i in range(len(pts)-1):
                p.drawLine(int(pts[i][0]),int(pts[i][1]),int(pts[i+1][0]),int(pts[i+1][1]))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([QPointF(cx-28, cy-22), QPointF(cx+28, cy-22), QPointF(cx+26, cy-72), QPointF(cx-26, cy-72)]))
        p.setBrush(QBrush(black)); p.fillRect(int(cx-28), int(cy-78), 56, 14, black)
        pen = QPen(QColor(50,90,40), 2); p.setPen(pen)
        p.drawLine(int(cx-14), int(cy-57), int(cx+14), int(cy-57))
        for sx in [-12,-6,0,6,12]: p.drawLine(int(cx+sx), int(cy-62), int(cx+sx), int(cy-52))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(40,20,10)))
        p.drawEllipse(QRectF(cx-18, cy-52, 14, 12)); p.drawEllipse(QRectF(cx+4, cy-52, 14, 12))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(cx-15, cy-50, 8, 8)); p.drawEllipse(QRectF(cx+7, cy-50, 8, 8))
        p.setBrush(QBrush(black))
        p.drawPolygon(QPolygonF([QPointF(cx-14,cy-36), QPointF(cx+14,cy-36), QPointF(cx+12,cy-28), QPointF(cx-12,cy-28)]))
        p.setBrush(QBrush(QColor(220,215,195)))
        for tx in [-10,-5,0,5]: p.drawRect(QRectF(cx+tx, cy-35, 4, 6))

    def _draw_knight(self, p, cx, cy):
        robe = QColor(18, 12, 30); bone = QColor(198, 188, 155)
        blade = QColor(140, 210, 255); eye_c = QColor(140, 0, 210)
        p.setBrush(QBrush(QColor(60,0,90,110))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-38, cy+80, 76, 14))
        p.setBrush(QBrush(robe))
        p.drawPolygon(QPolygonF([QPointF(cx-30, cy-18), QPointF(cx+30, cy-18), QPointF(cx+55, cy+76), QPointF(cx-55, cy+76)]))
        pen = QPen(QColor(10,6,20), 2); p.setPen(pen)
        for ox in [-14, 0, 14]: p.drawLine(int(cx+ox), int(cy-10), int(cx+ox*2), int(cy+68))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(26,17,44)))
        for i, ox in enumerate(range(-44, 56, 16)):
            tip = cy + 76 + (8 if i % 2 == 0 else 16)
            p.drawPolygon(QPolygonF([QPointF(cx+ox-8, cy+72), QPointF(cx+ox+8, cy+72), QPointF(cx+ox, tip)]))
        p.setBrush(QBrush(robe)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-38, cy-86, 76, 74))
        p.setBrush(QBrush(QColor(8,4,16))); p.drawEllipse(QRectF(cx-26, cy-80, 52, 62))
        p.setBrush(QBrush(bone)); p.drawEllipse(QRectF(cx-18, cy-74, 36, 40))
        p.drawPolygon(QPolygonF([QPointF(cx-14,cy-40), QPointF(cx+14,cy-40), QPointF(cx+16,cy-28), QPointF(cx-16,cy-28)]))
        p.setBrush(QBrush(QColor(10,5,20)))
        p.drawEllipse(QRectF(cx-14, cy-66, 13, 13)); p.drawEllipse(QRectF(cx+1, cy-66, 13, 13))
        p.setBrush(QBrush(eye_c))
        p.drawEllipse(QRectF(cx-11, cy-63, 7, 7)); p.drawEllipse(QRectF(cx+4, cy-63, 7, 7))
        p.setBrush(QBrush(QColor(12,6,22)))
        p.drawPolygon(QPolygonF([QPointF(cx-3,cy-48),QPointF(cx+3,cy-48),QPointF(cx,cy-42)]))
        p.fillRect(int(cx-14), int(cy-36), 28, 3, QColor(12,6,22))
        p.setBrush(QBrush(bone))
        for tx in [-12,-7,-2,3,8]: p.drawRect(QRectF(cx+tx, cy-36, 4, 8))
        p.drawEllipse(QRectF(cx-36, cy-10, 14, 16))
        for fdx, fdy in [(-38,-20),(-33,-22),(-27,-22),(-22,-14)]:
            p.drawEllipse(QRectF(cx+fdx, cy+fdy, 7, 10))
        p.drawEllipse(QRectF(cx+22, cy-10, 14, 16))
        for fdx, fdy in [(22,-20),(28,-22),(34,-22),(38,-14)]:
            p.drawEllipse(QRectF(cx+fdx, cy+fdy, 7, 10))
        pen = QPen(QColor(55,38,18), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen)
        p.drawLine(int(cx-30), int(cy+10), int(cx+52), int(cy-76))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(100,175,240,150)))
        p.drawPolygon(QPolygonF([QPointF(cx+52, cy-76), QPointF(cx+16, cy-100), QPointF(cx-18, cy-82), QPointF(cx+2, cy-66), QPointF(cx+44, cy-72)]))
        pen = QPen(blade, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap); p.setPen(pen)
        p.drawLine(int(cx+52), int(cy-76), int(cx+16), int(cy-100))
        p.drawLine(int(cx+16), int(cy-100), int(cx-18), int(cy-82))
        p.drawLine(int(cx-18), int(cy-82), int(cx+2), int(cy-66))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(120,190,255,40)))
        p.drawEllipse(QRectF(cx-24, cy-108, 84, 40))


class StressPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._order: list[int] = []
        self._cur       = 0
        self._hp        = 0
        self._maxhp     = 0
        self._kills     = 0
        self._dead      = False
        self._time_left = 0
        self._time_max  = 0
        self._time_tick = QTimer(self)
        self._time_tick.setInterval(100)
        self._time_tick.timeout.connect(self._tick_time)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("stress-card")
        self._card.setFixedWidth(292)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("stress-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        self._title_lbl = QLabel("💢  Zona Anti-Stress"); self._title_lbl.setObjectName("stress-title")
        cls = QPushButton("✕"); cls.setObjectName("stress-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(self._title_lbl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # Battle frame
        self._battle_frame = QWidget(); self._battle_frame.setObjectName("stress-body")
        bv = QVBoxLayout(self._battle_frame)
        bv.setContentsMargins(14, 10, 14, 14); bv.setSpacing(8)

        self._counter_lbl = QLabel()
        self._counter_lbl.setObjectName("stress-counter")
        self._counter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._counter_lbl)

        time_row = QHBoxLayout(); time_row.setSpacing(6)
        self._time_bar = _TimeBar()
        self._time_lbl = QLabel(); self._time_lbl.setObjectName("stress-timelbl")
        self._time_lbl.setFixedWidth(28)
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_row.addWidget(self._time_bar); time_row.addWidget(self._time_lbl)
        bv.addLayout(time_row)

        self._canvas = _MonsterCanvas()
        self._canvas.clicked_at.connect(self._on_hit)
        bv.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

        row = QHBoxLayout(); row.setSpacing(10)
        self._mon_name = QLabel(); self._mon_name.setObjectName("stress-monname")
        self._hp_lbl   = QLabel(); self._hp_lbl.setObjectName("stress-hplbl")
        row.addWidget(self._mon_name); row.addStretch(); row.addWidget(self._hp_lbl)
        bv.addLayout(row)

        self._hp_bar = _HPBar()
        bv.addWidget(self._hp_bar)

        hint = QLabel("⚔  Clique para atacar!"); hint.setObjectName("stress-hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(hint)
        v.addWidget(self._battle_frame)

        # Victory frame
        self._victory_frame = QWidget(); self._victory_frame.setObjectName("stress-body")
        vv = QVBoxLayout(self._victory_frame)
        vv.setContentsMargins(14, 20, 14, 20); vv.setSpacing(14)
        trophy = QLabel("🏆"); trophy.setObjectName("stress-trophy")
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vv.addWidget(trophy)
        self._win_lbl = QLabel(); self._win_lbl.setObjectName("stress-winmsg")
        self._win_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._win_lbl.setWordWrap(True)
        vv.addWidget(self._win_lbl)
        restart = QPushButton("🔄  Nova Rodada"); restart.setObjectName("stress-btn")
        restart.clicked.connect(self._start_game)
        vv.addWidget(restart)
        self._victory_frame.setVisible(False)
        v.addWidget(self._victory_frame)

        # Defeat frame
        self._defeat_frame = QWidget(); self._defeat_frame.setObjectName("stress-body")
        dv = QVBoxLayout(self._defeat_frame)
        dv.setContentsMargins(14, 20, 14, 20); dv.setSpacing(14)
        skull = QLabel("💀"); skull.setObjectName("stress-trophy")
        skull.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dv.addWidget(skull)
        self._lose_lbl = QLabel(); self._lose_lbl.setObjectName("stress-winmsg")
        self._lose_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lose_lbl.setWordWrap(True)
        dv.addWidget(self._lose_lbl)
        retry = QPushButton("🔄  Tentar Novamente"); retry.setObjectName("stress-btn")
        retry.clicked.connect(self._start_game)
        dv.addWidget(retry)
        self._defeat_frame.setVisible(False)
        v.addWidget(self._defeat_frame)

        outer.addWidget(self._card)

    def _start_game(self):
        self._time_tick.stop()
        self._order = random.sample(range(len(_STRESS_MONSTERS)), len(_STRESS_MONSTERS))
        self._cur = 0; self._kills = 0; self._dead = False
        self._victory_frame.setVisible(False); self._defeat_frame.setVisible(False)
        self._battle_frame.setVisible(True)
        self._title_lbl.setText("💢  Zona Anti-Stress")
        self._load_monster()
        self.adjustSize()

    def _load_monster(self):
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._hp = self._maxhp = m["hp"]
        self._time_left = self._time_max = m["time"] * 10
        self._canvas.set_monster(m["kind"], m["color"])
        self._mon_name.setText(m["name"])
        self._update_counter(); self._update_hp(); self._update_time()
        self._time_tick.start()

    def _on_hit(self, x: int, y: int):
        if self._dead or self._hp <= 0:
            return
        self._hp -= 1
        self._canvas.do_hit(x, y)
        self._update_hp()
        if self._hp <= 0:
            self._kill_monster()

    def _kill_monster(self):
        self._time_tick.stop(); self._dead = True
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._canvas.set_monster(m["kind"], m["color"], dead=True)
        self._kills += 1; self._update_counter()
        if self._kills >= len(_STRESS_MONSTERS):
            QTimer.singleShot(900, self._show_victory)
        else:
            self._cur += 1; self._dead = False
            QTimer.singleShot(950, self._load_monster)

    def _tick_time(self):
        if self._dead or self._hp <= 0:
            return
        self._time_left -= 1; self._update_time()
        if self._time_left <= 0:
            self._time_tick.stop(); self._monster_wins()

    def _monster_wins(self):
        self._dead = True
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._canvas.set_monster(m["kind"], m["color"], dead=False)
        QTimer.singleShot(400, self._show_defeat)

    def _show_victory(self):
        self._battle_frame.setVisible(False); self._victory_frame.setVisible(True)
        self._title_lbl.setText("🏆  Vitória!")
        self._win_lbl.setText(random.choice(_STRESS_WIN_MSGS))
        self.adjustSize()

    def _show_defeat(self):
        self._battle_frame.setVisible(False); self._defeat_frame.setVisible(True)
        self._title_lbl.setText("💀  Derrota!")
        self._lose_lbl.setText(random.choice(_STRESS_LOSE_MSGS))
        self.adjustSize()

    def _update_hp(self):
        ratio = self._hp / self._maxhp if self._maxhp else 0
        self._hp_bar.set_ratio(ratio)
        self._hp_lbl.setText(f"{self._hp} / {self._maxhp}")

    def _update_time(self):
        ratio = self._time_left / self._time_max if self._time_max else 0
        self._time_bar.set_ratio(ratio)
        self._time_lbl.setText(f"{math.ceil(self._time_left / 10)}s")

    def _update_counter(self):
        parts = []
        for i in range(len(_STRESS_MONSTERS)):
            if i < self._kills:   parts.append("☠")
            elif i == self._cur:  parts.append("⚔")
            else:                 parts.append("○")
        self._counter_lbl.setText("  ".join(parts))

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text  = "#1c1c1e"            if is_light else "#e5e5ea"
        muted = "rgba(0,0,0,0.45)"  if is_light else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)"  if is_light else "rgba(255,255,255,0.07)"
        self._card.setStyleSheet(f"""
            QFrame#stress-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#stress-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#stress-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#stress-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#stress-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#stress-body {{ background:transparent; }}
            QLabel#stress-counter {{
                color:{muted}; font-size:14px; letter-spacing:2px; background:transparent;
                font-family:"SF Pro Text","Segoe UI",sans-serif;
            }}
            QLabel#stress-monname {{
                color:{text}; font-size:14px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#stress-hplbl {{
                color:{muted}; font-size:12px;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent;
            }}
            QLabel#stress-hint {{
                color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#stress-timelbl {{
                color:{muted}; font-size:10px;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent;
            }}
            QLabel#stress-trophy {{ font-size:52px; background:transparent; }}
            QLabel#stress-winmsg {{
                color:{text}; font-size:12px; line-height:1.5;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#stress-btn {{
                background:#0a84ff; color:#fff; border:none; border-radius:9px;
                font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:10px;
            }}
            QPushButton#stress-btn:hover {{ background:#0070e0; }}
        """)
