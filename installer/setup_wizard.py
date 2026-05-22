#!/usr/bin/env python3
"""
Notch Win — Assistente de Instalação
Wizard com 3 etapas: boas-vindas, instalação, conclusão.
Usa apenas tkinter (embutido no Python) para rodar sem dependências.
"""

import sys
import os
import subprocess
import threading
import webbrowser
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# ── Paths ──────────────────────────────────────────────────────────────────────
# Quando empacotado com PyInstaller, arquivos do app ficam em sys._MEIPASS/app/
if getattr(sys, "frozen", False):
    _APP_SRC = Path(sys._MEIPASS) / "app"
else:
    _APP_SRC = Path(__file__).resolve().parent.parent  # raiz do notch-win/

DEFAULT_INSTALL  = Path.home() / "AppData" / "Local" / "NotchWin"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# ── Theme ──────────────────────────────────────────────────────────────────────
BG     = "#141414"
CARD   = "#1e1e1e"
INPUT  = "#252525"
ACCENT = "#e63946"
GREEN  = "#2ecc71"
TEXT   = "#ececec"
MUTED  = "#7f8c8d"
BORDER = "#2c2c2c"
HOVER  = "#c1121f"

TF = ("Segoe UI", 20, "bold")   # título
SF = ("Segoe UI", 12)            # subtítulo
BF = ("Segoe UI", 11)            # corpo
CF = ("Consolas", 10)            # código / mono
LF = ("Segoe UI", 10, "bold")   # label de campo

STEPS = ["Boas-vindas", "Instalação", "Concluir"]

# ── Widgets reutilizáveis ──────────────────────────────────────────────────────

class StyledButton(tk.Button):
    def __init__(self, master, text, command=None, variant="primary", **kw):
        palettes = {
            "primary":   (ACCENT, TEXT,  HOVER,     TEXT),
            "secondary": ("#2c2c2c", MUTED, "#383838", TEXT),
            "ghost":     (CARD,  MUTED, "#252525",  TEXT),
        }
        bg, fg, hbg, hfg = palettes.get(variant, palettes["primary"])
        opts = dict(
            bg=bg, fg=fg, activebackground=hbg, activeforeground=hfg,
            relief="flat", cursor="hand2", bd=0,
            padx=18, pady=7, font=BF,
        )
        opts.update(kw)  # caller kwargs sobrescrevem os defaults
        super().__init__(master, text=text, command=command, **opts)
        self.bind("<Enter>", lambda _: self.configure(bg=hbg, fg=hfg))
        self.bind("<Leave>", lambda _: self.configure(bg=bg,  fg=fg))


class CheckItem(tk.Frame):
    """Linha de checagem com ícone de status (○ / ✓ / ✗ / …)."""
    def __init__(self, master, label, **kw):
        super().__init__(master, bg=BG, **kw)
        self._dot = tk.Label(self, text="○", fg=MUTED, bg=BG,
                             font=("Segoe UI", 13), width=2)
        self._dot.pack(side="left")
        tk.Label(self, text=label, fg=TEXT, bg=BG, font=BF).pack(side="left", padx=(4, 0))
        self._detail = tk.Label(self, text="", fg=MUTED, bg=BG, font=("Segoe UI", 9))
        self._detail.pack(side="left", padx=(8, 0))

    def ok(self, detail=""):
        self._dot.configure(text="✓", fg=GREEN)
        self._detail.configure(text=detail, fg=MUTED)

    def fail(self, detail=""):
        self._dot.configure(text="✗", fg=ACCENT)
        self._detail.configure(text=detail, fg=ACCENT)

    def loading(self):
        self._dot.configure(text="…", fg=MUTED)
        self._detail.configure(text="")


class CopyLabel(tk.Frame):
    """Label com botão 'Copiar' ao lado — para URIs e IDs."""
    def __init__(self, master, value, **kw):
        super().__init__(master, bg=CARD, **kw)
        tk.Label(self, text=value, fg=ACCENT, bg=CARD, font=CF).pack(side="left")
        self._btn = tk.Button(
            self, text="Copiar", command=self._copy,
            bg="#2a2a2a", fg=MUTED, relief="flat", bd=0,
            font=("Segoe UI", 8), cursor="hand2", padx=6, pady=1
        )
        self._btn.pack(side="left", padx=(8, 0))
        self._value = value

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self._value)
        self._btn.configure(text="Copiado ✓", fg=GREEN)
        self.after(2000, lambda: self._btn.configure(text="Copiar", fg=MUTED))


# ── Wizard principal ────────────────────────────────────────────────────────────

class SetupWizard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Notch Win — Assistente de Instalação")
        self.geometry("660x510")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._center()

        # Detecta atualização antes de construir as páginas
        self._is_update     = (DEFAULT_INSTALL / "main.py").exists()

        # Estado compartilhado entre páginas
        self.install_dir = tk.StringVar(value=str(DEFAULT_INSTALL))
        self.shortcut    = tk.BooleanVar(value=not self._is_update)
        self.autostart      = tk.BooleanVar(value=False)
        self.launch_now     = tk.BooleanVar(value=True)
        self._install_done  = False
        self._python_exe    = self._find_python()

        self._pages: list[tk.Frame] = []
        self._page_idx = 0

        self._build_header()
        self._body = tk.Frame(self, bg=BG)
        self._body.pack(fill="both", expand=True)
        self._build_footer()

        self._init_pages()
        self._show(0)

    # ── Utilitários ──────────────────────────────────────────────────────────

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"660x510+{(sw-660)//2}+{(sh-510)//2}")

    @staticmethod
    def _find_python() -> str:
        """Retorna o executável Python disponível."""
        if not getattr(sys, "frozen", False):
            return sys.executable
        for candidate in ("python", "python3", "py"):
            found = shutil.which(candidate)
            if found:
                return found
        return "python"

    # ── Layout base ──────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🔲  Notch Win", fg=TEXT, bg=CARD, font=TF).pack(side="left", padx=24)

        steps_fr = tk.Frame(hdr, bg=CARD)
        steps_fr.pack(side="right", padx=20)
        self._step_dots: list[tuple[tk.Label, tk.Label]] = []
        for name in STEPS:
            col = tk.Frame(steps_fr, bg=CARD)
            col.pack(side="left", padx=6)
            dot = tk.Label(col, text="●", bg=CARD, font=("Segoe UI", 10))
            dot.pack()
            lbl = tk.Label(col, text=name, bg=CARD, font=("Segoe UI", 8))
            lbl.pack()
            self._step_dots.append((dot, lbl))

    def _update_steps(self, idx: int):
        for i, (dot, lbl) in enumerate(self._step_dots):
            if i < idx:
                dot.configure(fg="#444"); lbl.configure(fg="#555")
            elif i == idx:
                dot.configure(fg=ACCENT); lbl.configure(fg=TEXT)
            else:
                dot.configure(fg="#2a2a2a"); lbl.configure(fg="#333")

    def _build_footer(self):
        foot = tk.Frame(self, bg=CARD, height=54)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        tk.Frame(foot, bg=BORDER, height=1).pack(fill="x")

        btn_fr = tk.Frame(foot, bg=CARD)
        btn_fr.pack(side="right", padx=20, pady=10)
        self._btn_back = StyledButton(btn_fr, "← Voltar", self._prev, variant="secondary")
        self._btn_back.pack(side="left", padx=(0, 8))
        self._btn_next = StyledButton(btn_fr, "Próximo →", self._next)
        self._btn_next.pack(side="left")

    # ── Navegação ────────────────────────────────────────────────────────────

    def _init_pages(self):
        self._pages = [
            self._page_welcome(),
            self._page_install(),
            self._page_finish(),
        ]

    def _show(self, idx: int):
        for p in self._pages:
            p.pack_forget()
        self._pages[idx].pack(fill="both", expand=True, padx=32, pady=20)
        self._page_idx = idx
        self._update_steps(idx)
        is_last = idx == len(self._pages) - 1
        self._btn_back.configure(state="normal" if idx > 0 else "disabled")
        self._btn_next.configure(text="Concluir ✓" if is_last else "Próximo →")

    def _next(self):
        if self._page_idx == 1 and not self._install_done:
            messagebox.showwarning("Aguarde", "Clique em 'Instalar' e aguarde a conclusão.")
            return
        if self._page_idx == len(self._pages) - 1:
            self._finish()
            return
        self._show(self._page_idx + 1)

    def _prev(self):
        if self._page_idx > 0:
            self._show(self._page_idx - 1)

    # ── Página 0: Boas-vindas ─────────────────────────────────────────────────

    def _page_welcome(self) -> tk.Frame:
        f = tk.Frame(self._body, bg=BG)

        if self._is_update:
            tk.Label(f, text="Atualizar o Notch Win",
                     fg=TEXT, bg=BG, font=TF).pack(anchor="w")

            # Banner de atualização detectada
            banner = tk.Frame(f, bg="#1a2e1a", pady=10, padx=14)
            banner.pack(fill="x", pady=(8, 16))
            tk.Label(banner, text="✓  Instalação existente detectada",
                     fg=GREEN, bg="#1a2e1a", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(banner, text=f"Em:  {self.install_dir.get()}",
                     fg=MUTED, bg="#1a2e1a", font=CF).pack(anchor="w", pady=(3, 0))

            notes = [
                "Os arquivos do aplicativo serão atualizados para a nova versão.",
                "Suas credenciais do Spotify (.env) serão preservadas.",
                "Seu token do YouTube e configurações não serão alterados.",
            ]
            for note in notes:
                row = tk.Frame(f, bg=BG)
                row.pack(anchor="w", pady=2)
                tk.Label(row, text="•", fg=ACCENT, bg=BG,
                         font=BF, width=2).pack(side="left")
                tk.Label(row, text=note, fg=TEXT, bg=BG,
                         font=("Segoe UI", 10)).pack(side="left")

            tk.Label(f, text="Clique em Próximo para iniciar a atualização.",
                     fg=MUTED, bg=BG, font=("Segoe UI", 10)).pack(anchor="w", pady=(18, 0))
        else:
            tk.Label(f, text="Bem-vindo ao Notch Win",
                     fg=TEXT, bg=BG, font=TF).pack(anchor="w")
            tk.Label(f, text="Uma barra de produtividade estilo macOS flutuando no topo do Windows.",
                     fg=MUTED, bg=BG, font=SF).pack(anchor="w", pady=(6, 20))

            features = [
                ("🎵", "Controles do Spotify", "Veja a faixa atual e controle play/pause/skip"),
                ("🍅", "Timer Pomodoro",        "25/5/15 min com notificações nativas do Windows"),
                ("📋", "Histórico de clipboard","Acesso rápido aos últimos 15 itens copiados"),
            ]
            for icon, title, desc in features:
                card = tk.Frame(f, bg=CARD, pady=10, padx=14)
                card.pack(fill="x", pady=4)
                tk.Label(card, text=icon, bg=CARD,
                         font=("Segoe UI", 22), width=3).pack(side="left", anchor="n")
                col = tk.Frame(card, bg=CARD)
                col.pack(side="left", padx=10)
                tk.Label(col, text=title, fg=TEXT, bg=CARD, font=LF, anchor="w").pack(anchor="w")
                tk.Label(col, text=desc, fg=MUTED, bg=CARD, font=("Segoe UI", 10),
                         anchor="w").pack(anchor="w")

            tk.Label(f,
                     text="Este assistente instala as dependências e prepara o Notch Win para uso.",
                     fg=MUTED, bg=BG, font=("Segoe UI", 10)).pack(anchor="w", pady=(18, 0))
        return f

    # ── Página 1: Instalação ──────────────────────────────────────────────────

    def _page_install(self) -> tk.Frame:
        f = tk.Frame(self._body, bg=BG)

        tk.Label(f, text="Instalação", fg=TEXT, bg=BG, font=TF).pack(anchor="w")
        tk.Label(f, text="Copie os arquivos e instale as dependências Python.",
                 fg=MUTED, bg=BG, font=SF).pack(anchor="w", pady=(4, 14))

        # Seletor de diretório
        dir_fr = tk.Frame(f, bg=BG)
        dir_fr.pack(fill="x", pady=(0, 12))
        tk.Label(dir_fr, text="Pasta de instalação:", fg=TEXT, bg=BG, font=LF).pack(anchor="w")
        row = tk.Frame(dir_fr, bg=BG)
        row.pack(fill="x", pady=4)
        tk.Entry(row, textvariable=self.install_dir, bg=INPUT, fg=TEXT,
                 relief="flat", font=CF, insertbackground=TEXT,
                 disabledbackground=INPUT).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        StyledButton(row, "Escolher", self._pick_dir, variant="secondary").pack(side="left")

        # Indicadores de checagem
        checks_fr = tk.Frame(f, bg=BG)
        checks_fr.pack(fill="x", pady=4)
        self._chk_python = CheckItem(checks_fr, "Python 3.10+")
        self._chk_python.pack(anchor="w", pady=2)
        self._chk_copy = CheckItem(checks_fr, "Arquivos copiados para pasta de instalação")
        self._chk_copy.pack(anchor="w", pady=2)
        self._chk_deps = CheckItem(checks_fr, "Dependências (PyQt6, OpenCV, monitoramento de sistema…)")
        self._chk_deps.pack(anchor="w", pady=2)

        # Log de saída do pip
        self._log = tk.Text(f, bg=CARD, fg=MUTED, font=CF, height=5,
                            relief="flat", state="disabled", wrap="word")
        self._log.pack(fill="x", pady=(8, 10))

        self._install_btn = StyledButton(f, "▶  Instalar", self._run_install)
        self._install_btn.pack(anchor="w")

        return f

    def _pick_dir(self):
        d = filedialog.askdirectory(title="Escolha a pasta de instalação")
        if d:
            self.install_dir.set(d)

    def _log_append(self, msg: str):
        """Thread-safe: agenda atualização do log na thread principal."""
        self.after(0, self._log_write, msg)

    def _log_write(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _run_install(self):
        self._install_btn.configure(state="disabled", text="Instalando…")
        threading.Thread(target=self._do_install, daemon=True).start()

    def _do_install(self):
        dest = Path(self.install_dir.get())

        # 1. Checar Python
        self.after(0, self._chk_python.loading)
        ver = sys.version_info
        if ver >= (3, 10):
            self.after(0, self._chk_python.ok, f"Python {ver.major}.{ver.minor}.{ver.micro}")
        else:
            self.after(0, self._chk_python.fail, f"Python {ver.major}.{ver.minor} — requer 3.10+")
            self.after(0, lambda: self._install_btn.configure(state="normal", text="▶  Instalar"))
            return

        # 2. Copiar arquivos
        self.after(0, self._chk_copy.loading)
        try:
            dest.mkdir(parents=True, exist_ok=True)
            for item in ["main.py", "config.py", "modules", "ui", "assets", "requirements.txt", ".env.example"]:
                src = _APP_SRC / item
                if src.is_dir():
                    shutil.copytree(src, dest / item, dirs_exist_ok=True)
                elif src.exists():
                    shutil.copy2(src, dest / item)
            self.after(0, self._chk_copy.ok)
            self._log_append(f"Arquivos copiados para: {dest}")
        except Exception as exc:
            self.after(0, self._chk_copy.fail, str(exc))
            self.after(0, lambda: self._install_btn.configure(state="normal", text="▶  Instalar"))
            return

        # 3. Instalar dependências
        self.after(0, self._chk_deps.loading)
        self._log_append("Instalando dependências via pip…")
        req = dest / "requirements.txt"
        proc = subprocess.Popen(
            [self._python_exe, "-m", "pip", "install", "-r", str(req), "--user"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            line = line.strip()
            if line:
                self._log_append(line)
        proc.wait()

        if proc.returncode == 0:
            self.after(0, self._chk_deps.ok)
            self._install_done = True
            self.after(0, lambda: self._install_btn.configure(
                text="✓ Instalado", bg=GREEN, fg="#111", state="disabled"
            ))
            msg = "✓ Atualização concluída!" if self._is_update else "✓ Instalação concluída!"
            self._log_append(msg)
            self.after(1500, lambda: self._show(2))
        else:
            self.after(0, self._chk_deps.fail, "erro — veja o log acima")
            self.after(0, lambda: self._install_btn.configure(
                state="normal", text="↺  Tentar novamente"
            ))

    # ── Página 2: Conclusão ───────────────────────────────────────────────────

    def _page_finish(self) -> tk.Frame:
        f = tk.Frame(self._body, bg=BG)

        if self._is_update:
            tk.Label(f, text="Atualização concluída!", fg=GREEN, bg=BG, font=TF).pack(anchor="w")
            tk.Label(f, text="O Notch Win foi atualizado com sucesso.",
                     fg=MUTED, bg=BG, font=SF).pack(anchor="w", pady=(4, 20))
            checkboxes = [
                (self.launch_now, "Abrir o Notch agora ao clicar em Concluir"),
            ]
            note_text = "Suas configurações e credenciais foram preservadas."
        else:
            tk.Label(f, text="Tudo pronto!", fg=GREEN, bg=BG, font=TF).pack(anchor="w")
            tk.Label(f, text="O Notch Win foi instalado e configurado com sucesso.",
                     fg=MUTED, bg=BG, font=SF).pack(anchor="w", pady=(4, 20))
            checkboxes = [
                (self.shortcut,  "Criar atalho na Área de Trabalho"),
                (self.autostart, "Iniciar automaticamente com o Windows"),
                (self.launch_now, "Abrir o Notch agora ao clicar em Concluir"),
            ]
            note_text = "Configure o Spotify e o YouTube nas Configurações dentro do app."

        opts = tk.Frame(f, bg=BG)
        opts.pack(anchor="w")
        for var, label in checkboxes:
            row = tk.Frame(opts, bg=BG)
            row.pack(anchor="w", pady=5)
            tk.Checkbutton(
                row, variable=var, bg=BG, fg=TEXT,
                activebackground=BG, activeforeground=TEXT,
                selectcolor=CARD, relief="flat", cursor="hand2",
            ).pack(side="left")
            tk.Label(row, text=label, fg=TEXT, bg=BG, font=BF).pack(side="left")

        # Resumo da instalação
        summary = tk.Frame(f, bg=CARD, pady=14, padx=18)
        summary.pack(fill="x", pady=20)
        tk.Label(summary, text="Instalado em:", fg=MUTED, bg=CARD,
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(summary, textvariable=self.install_dir, fg=TEXT, bg=CARD,
                 font=CF).pack(anchor="w")
        tk.Label(summary, text=note_text,
                 fg=MUTED, bg=CARD, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))

        return f

    # ── Ação final ────────────────────────────────────────────────────────────

    def _finish(self):
        dest = Path(self.install_dir.get())

        if self.shortcut.get():
            self._create_shortcut(dest)

        if self.autostart.get():
            self._set_autostart(dest)

        if self.launch_now.get():
            pythonw = Path(self._python_exe).parent / "pythonw.exe"
            launcher = str(pythonw) if pythonw.exists() else self._python_exe
            flags = subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
            subprocess.Popen(
                [launcher, str(dest / "main.py")],
                cwd=str(dest),
                creationflags=flags,
            )

        messagebox.showinfo("Instalação concluída",
                            "O Notch Win foi instalado!\n\n"
                            "Procure-o na bandeja do sistema (canto inferior direito).")
        self.destroy()

    def _create_shortcut(self, dest: Path):
        # Usa variáveis PowerShell para evitar problemas com espaços, barras e
        # caracteres especiais em paths. GetFolderPath resolve corretamente o
        # Desktop mesmo quando está redirecionado para o OneDrive.
        # pythonw.exe roda sem janela de console, fechando o terminal ao iniciar.
        pythonw = Path(self._python_exe).parent / "pythonw.exe"
        py_exe  = str(pythonw) if pythonw.exists() else self._python_exe
        py     = py_exe.replace("'", "''")
        target = str(dest / "main.py").replace("'", "''")
        work   = str(dest).replace("'", "''")
        ps = (
            "$desktop = [Environment]::GetFolderPath('Desktop'); "
            "$ws = New-Object -ComObject WScript.Shell; "
            "$s  = $ws.CreateShortcut($desktop + '\\Notch Win.lnk'); "
            f"$s.TargetPath      = '{py}'; "
            f"$s.Arguments       = '{target}'; "
            f"$s.WorkingDirectory= '{work}'; "
            "$s.Save()"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            messagebox.showwarning(
                "Atalho",
                f"Não foi possível criar o atalho:\n{result.stderr.strip()}"
            )

    def _set_autostart(self, dest: Path):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            cmd = f'"{self._python_exe}" "{dest / "main.py"}"'
            winreg.SetValueEx(key, "NotchWin", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
        except Exception as exc:
            messagebox.showwarning("Autostart", f"Não foi possível configurar inicialização automática:\n{exc}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
