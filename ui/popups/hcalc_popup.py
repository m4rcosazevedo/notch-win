from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QLineEdit, QWidget,
)
from PyQt6.QtCore import Qt

from ui.popups.base_popup import BasePopup


class HoursCalcPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("hcalc-card")
        self._card.setFixedWidth(300)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("hcalc-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("⏱  Calculadora de Horas"); ttl.setObjectName("hcalc-title")
        cls = QPushButton("✕"); cls.setObjectName("hcalc-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        body = QWidget(); body.setObjectName("hcalc-body")
        bv = QVBoxLayout(body); bv.setContentsMargins(16, 14, 16, 14); bv.setSpacing(10)

        time_row = QWidget()
        tr = QHBoxLayout(time_row); tr.setContentsMargins(0, 0, 0, 0); tr.setSpacing(10)
        for attr, lbl_text, ph in [("_inp_h", "HORAS", "0"), ("_inp_m", "MINUTOS", "0")]:
            col = QVBoxLayout(); col.setSpacing(4)
            lbl = QLabel(lbl_text); lbl.setObjectName("hcalc-field-lbl")
            inp = QLineEdit(); inp.setObjectName("hcalc-input")
            inp.setPlaceholderText(ph)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inp.returnPressed.connect(self._calc)
            setattr(self, attr, inp)
            col.addWidget(lbl); col.addWidget(inp)
            tr.addLayout(col)
        bv.addWidget(time_row)

        rate_lbl = QLabel("VALOR POR HORA  (R$)"); rate_lbl.setObjectName("hcalc-field-lbl")
        self._inp_rate = QLineEdit(); self._inp_rate.setObjectName("hcalc-input")
        self._inp_rate.setPlaceholderText("0,00")
        self._inp_rate.returnPressed.connect(self._calc)
        bv.addWidget(rate_lbl); bv.addWidget(self._inp_rate)

        calc_btn = QPushButton("Calcular →"); calc_btn.setObjectName("hcalc-btn")
        calc_btn.clicked.connect(self._calc)
        bv.addWidget(calc_btn)

        self._result_frame = QFrame(); self._result_frame.setObjectName("hcalc-result-frame")
        self._result_frame.setVisible(False)
        rv = QVBoxLayout(self._result_frame)
        rv.setContentsMargins(14, 12, 14, 12); rv.setSpacing(4)
        lbl_rec = QLabel("Você receberá:"); lbl_rec.setObjectName("hcalc-result-label")
        lbl_rec.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_main = QLabel(); self._result_main.setObjectName("hcalc-result-main")
        self._result_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_sub = QLabel(); self._result_sub.setObjectName("hcalc-result-sub")
        self._result_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.addWidget(lbl_rec); rv.addWidget(self._result_main); rv.addWidget(self._result_sub)
        bv.addWidget(self._result_frame)

        v.addWidget(body)
        outer.addWidget(self._card)

    def _calc(self):
        try:
            h = int(self._inp_h.text().strip() or 0)
            m = int(self._inp_m.text().strip() or 0)
            if not (0 <= m <= 59):
                raise ValueError
            rate_str = self._inp_rate.text().strip().replace(',', '.')
            rate = float(rate_str or 0)
        except ValueError:
            self._result_main.setText("⚠  Verifique os valores")
            self._result_sub.setText("Minutos: 0–59 · Valores numéricos")
            self._result_frame.setVisible(True)
            self.adjustSize()
            return

        total = (h + m / 60) * rate
        self._result_main.setText(self._fmt(total))
        self._result_sub.setText(f"{h}h {m:02d}min  ×  {self._fmt(rate)}/h")
        self._result_frame.setVisible(True)
        self.adjustSize()

    @staticmethod
    def _fmt(v: float) -> str:
        return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text    = "#1c1c1e"              if is_light else "#e5e5ea"
        muted   = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep     = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        inp_bg  = "rgba(0,0,0,0.05)"    if is_light else "rgba(255,255,255,0.07)"
        inp_brd = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.14)"
        green   = "#1a7a3a"             if is_light else "#30d158"
        self._card.setStyleSheet(f"""
            QFrame#hcalc-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#hcalc-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#hcalc-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#hcalc-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#hcalc-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#hcalc-body {{ background:transparent; }}
            QLabel#hcalc-field-lbl {{
                color:{muted}; font-size:10px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; letter-spacing:0.6px;
            }}
            QLineEdit#hcalc-input {{
                background:{inp_bg}; color:{text}; border:1px solid {inp_brd}; border-radius:8px;
                font-size:16px; font-weight:600;
                font-family:"Consolas","Cascadia Code",monospace; padding:6px 8px;
                selection-background-color:#0a84ff;
            }}
            QLineEdit#hcalc-input:focus {{ border:1px solid rgba(10,132,255,0.55); }}
            QPushButton#hcalc-btn {{
                background:#0a84ff; color:#fff; border:none; border-radius:9px;
                font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:9px;
            }}
            QPushButton#hcalc-btn:hover {{ background:#0070e0; }}
            QFrame#hcalc-result-frame {{
                background:rgba(48,209,88,0.10); border-radius:10px;
                border:1px solid rgba(48,209,88,0.20);
            }}
            QLabel#hcalc-result-label {{
                color:{muted}; font-size:10px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; letter-spacing:0.5px;
            }}
            QLabel#hcalc-result-main {{
                color:{green}; font-size:24px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent;
            }}
            QLabel#hcalc-result-sub {{
                color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
        """)
