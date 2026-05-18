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
