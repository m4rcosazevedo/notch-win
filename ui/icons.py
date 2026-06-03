import math

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt6.QtGui import QIcon, QCursor, QPixmap, QPainter, QColor, QBrush, QPen, QPolygonF

_DEFAULT_DARK  = QColor(220, 220, 220, 190)
_DEFAULT_LIGHT = QColor( 30,  30,  40, 200)


def _make_icon(draw_fn, size: int = 22, color: QColor = None) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(p, size, color or _DEFAULT_DARK)
    p.end()
    return px


def _icon_btn(draw_fn, size: int = 22, color: QColor = None) -> QPushButton:
    btn = QPushButton()
    btn.setFixedSize(size, size)
    px = _make_icon(draw_fn, size, color)
    btn.setIcon(QIcon(px))
    btn.setIconSize(btn.size())
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    return btn


def _refresh_icon(btn: QPushButton, draw_fn, size: int = 22, color: QColor = None):
    px = _make_icon(draw_fn, size, color)
    btn.setIcon(QIcon(px))
    btn.setIconSize(btn.size())


def _ic_prev(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(3, 4, 3, s - 8, 1.5, 1.5)
    p.drawPolygon(QPolygonF([QPointF(s-4, 4), QPointF(7, s/2), QPointF(s-4, s-4)]))


def _ic_next(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(s-6, 4, 3, s-8, 1.5, 1.5)
    p.drawPolygon(QPolygonF([QPointF(4, 4), QPointF(s-7, s/2), QPointF(4, s-4)]))


def _ic_play(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([QPointF(5, 3), QPointF(s-3, s/2), QPointF(5, s-3)]))


def _ic_pause(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4,   3, 4, s-6, 2, 2)
    p.drawRoundedRect(s-8, 3, 4, s-6, 2, 2)


def _ic_reset(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 2.0); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(3, 3, s-6, s-6), 40*16, 290*16)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    tx, ty = s-4.5, 4.5
    p.drawPolygon(QPolygonF([QPointF(tx-4, ty), QPointF(tx+1, ty+4), QPointF(tx+2, ty-3)]))


def _ic_timer(p: QPainter, s: int, c: QColor):
    cx, cy = s/2, s/2 + 1.5
    r = (s - 9) / 2
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(int(cx)-2, 0, 4, 4, 1.5, 1.5)
    pen = QPen(c, 1.8); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(3, 4, s-6, s-6))
    pen2 = QPen(c, 1.8); pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    a_m = math.radians(-70)
    p.drawLine(QLineF(cx, cy, cx + r*0.58*math.sin(a_m), cy - r*0.58*math.cos(a_m)))
    a_h = math.radians(90)
    p.drawLine(QLineF(cx, cy, cx + r*0.38*math.sin(a_h), cy - r*0.38*math.cos(a_h)))


def _ic_clip_open(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    m = s/2
    p.drawPolyline(QPolygonF([QPointF(4, m-2), QPointF(m, m+3), QPointF(s-4, m-2)]))


def _ic_youtube(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.8)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 5, s - 4, s - 10), 3, 3)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    cx, cy = s / 2, s / 2
    p.drawPolygon(QPolygonF([QPointF(cx-3.5, cy-4), QPointF(cx+4.5, cy), QPointF(cx-3.5, cy+4)]))


def _ic_calc(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(3, 2, s-6, s-4), 3, 3)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for gx in range(2):
        for gy in range(3):
            p.drawEllipse(QRectF(6 + gx*8, 6 + gy*5, 3, 3))


def _ic_notes(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(4, 2, s-8, s-4), 3, 3)
    for y in [7, 11, 15]:
        p.drawLine(QLineF(7, y, s-7, y))


def _ic_alarm(p: QPainter, s: int, c: QColor):
    cx, cy, r = s/2, s/2+1, (s-10)/2
    pen = QPen(c, 1.7); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
    p.drawLine(QLineF(3, 6, 7, 2))
    p.drawLine(QLineF(s-3, 6, s-7, 2))
    p.drawLine(QLineF(cx, cy, cx, cy - r*0.55))
    p.drawLine(QLineF(cx, cy, cx + r*0.4, cy))


def _ic_quotes(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for ox in [3, 12]:
        p.drawRoundedRect(QRectF(ox, 4, 3.5, 5), 1.5, 1.5)
        p.drawRoundedRect(QRectF(ox+4.5, 4, 3.5, 5), 1.5, 1.5)
    pen = QPen(c, 1.4); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(QLineF(3, 14, s-3, 14))
    p.drawLine(QLineF(3, 18, s-7, 18))


def _ic_todo(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(3):
        y = 4 + i*6
        p.drawRect(QRectF(2, y, 5, 5))
        p.drawLine(QLineF(10, y+2.5, s-3, y+2.5))
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(QRectF(3.5, 5.5, 2, 2))


def _ic_photo(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 4, s-4, s-7), 3, 3)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s-8, 7, 4, 4))
    p.drawPolygon(QPolygonF([QPointF(3, s-5), QPointF(8, 11), QPointF(13, s-5)]))
    p.drawPolygon(QPolygonF([QPointF(10, s-5), QPointF(16, 13), QPointF(s-3, s-5)]))


def _ic_hcalc(p: QPainter, s: int, c: QColor):
    r, cx, cy = (s-10)/2, s/2-2, s/2
    pen = QPen(c, 1.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
    p.drawLine(QLineF(cx, cy, cx, cy - r*0.6))
    p.drawLine(QLineF(cx, cy, cx + r*0.45, cy))
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s-8, s-8, 7, 7))
    pen2 = QPen(QColor(0, 0, 0, 160), 1.2); pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    mx = s - 4.5
    p.drawLine(QLineF(mx, s-7.5, mx, s-1.5))
    p.drawLine(QLineF(mx-2, s-6,   mx+1.5, s-6))
    p.drawLine(QLineF(mx-2, s-4.2, mx+1.5, s-4.2))


def _ic_pokemon(p: QPainter, s: int, c: QColor):
    r, cx, cy = (s-4)/2, s/2, s/2
    pen = QPen(c, 1.6); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
    semi = QColor(c); semi.setAlpha(int(c.alpha() * 0.35))
    p.setBrush(QBrush(semi)); p.setPen(Qt.PenStyle.NoPen)
    p.drawChord(QRectF(cx-r, cy-r, r*2, r*2), 0, 180*16)
    p.setPen(pen)
    p.drawLine(QLineF(cx-r, cy, cx+r, cy))
    cr = r * 0.27
    p.setBrush(QBrush(QColor(255, 255, 255, 220))); p.setPen(pen)
    p.drawEllipse(QRectF(cx-cr, cy-cr, cr*2, cr*2))


def _ic_stress(p: QPainter, s: int, c: QColor):
    cx, cy = s/2, s/2+1
    r = (s-6)/2
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    horn  = [QPointF(cx-r*0.5, cy-r*0.7), QPointF(cx-r*0.25, cy-r*0.7), QPointF(cx-r*0.38, cy-r*1.15)]
    horn2 = [QPointF(cx+r*0.25, cy-r*0.7), QPointF(cx+r*0.5, cy-r*0.7), QPointF(cx+r*0.38, cy-r*1.15)]
    p.drawPolygon(QPolygonF(horn))
    p.drawPolygon(QPolygonF(horn2))
    p.drawEllipse(QRectF(cx-r*0.72, cy-r*0.82, r*1.44, r*1.30))
    p.setBrush(QBrush(QColor(0, 0, 0, 0)))
    pen2 = QPen(QColor(0, 0, 0, 200), 1.4); p.setPen(pen2)
    p.setBrush(QBrush(QColor(0, 0, 0, 180)))
    p.drawEllipse(QRectF(cx-r*0.48, cy-r*0.38, r*0.32, r*0.30))
    p.drawEllipse(QRectF(cx+r*0.16, cy-r*0.38, r*0.32, r*0.30))
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for i in range(3):
        tx = cx - r*0.28 + i * r*0.28
        p.drawRect(QRectF(tx, cy+r*0.22, r*0.18, r*0.28))


def _ic_color_picker(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.8); pen.setCapStyle(Qt.PenCapStyle.RoundCap); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(3, 3, s-6, s-6), 4, 4)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s/2-4, s/2-4, 8, 8))


def _ic_ruler(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.6); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 6, s-4, 10), 2, 2)
    for i in range(1, 10):
        x = 2 + (s-4) * i / 10
        h = 3 if i % 2 == 0 else 2
        p.drawLine(QLineF(x, 6, x, 6+h))


def _ic_github(p: QPainter, s: int, c: QColor):
    cx, cy, r = s/2, s/2, s/2 - 2
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
    p.setBrush(QBrush(QColor(0, 0, 0, 150)))
    # Simple silhouette
    p.drawEllipse(QRectF(cx-r*0.6, cy-r*0.4, r*1.2, r*0.9))
    p.drawPolygon(QPolygonF([QPointF(cx-r*0.5, cy-r*0.6), QPointF(cx-r*0.3, cy-r*0.3), QPointF(cx-r*0.7, cy-r*0.3)]))
    p.drawPolygon(QPolygonF([QPointF(cx+r*0.5, cy-r*0.6), QPointF(cx+r*0.3, cy-r*0.3), QPointF(cx+r*0.7, cy-r*0.3)]))


def _ic_calendar(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.8); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(3, 4, s-6, s-8), 3, 3)
    p.drawLine(QLineF(3, 8, s-3, 8))
    p.drawLine(QLineF(s/2-2, 2, s/2-2, 6))
    p.drawLine(QLineF(s/2+2, 2, s/2+2, 6))


def _ic_whatsapp(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.8); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    # Balloon shape
    p.drawRoundedRect(QRectF(2, 4, s-4, s-8), 6, 6)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    # Triangle tail
    p.drawPolygon(QPolygonF([QPointF(5, s-4), QPointF(9, s-10), QPointF(5, s-10)]))
    # Phone silhouette
    pen2 = QPen(c, 1.5); pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(s/2-4, s/2-4, 8, 8), 40*16, 200*16)


def _ic_refresh_action(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.8); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(4, 4, s-8, s-8), 45*16, 270*16)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([QPointF(s-6, 4), QPointF(s-2, 8), QPointF(s-8, 10)]))


def _ic_weather(p: QPainter, s: int, c: QColor):
    cx, cy = s / 2, s / 2
    r = s * 0.22
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)
    pen = QPen(c, 1.8); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(8):
        angle = math.radians(i * 45)
        x1 = cx + math.cos(angle) * (r + 2.5)
        y1 = cy + math.sin(angle) * (r + 2.5)
        x2 = cx + math.cos(angle) * (r + 5.0)
        y2 = cy + math.sin(angle) * (r + 5.0)
        p.drawLine(QLineF(x1, y1, x2, y2))
