from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QIcon, QCursor, QPixmap, QPainter, QColor, QBrush, QPolygonF

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
