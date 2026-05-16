#!/usr/bin/env python3
"""
Gera NotchSetup.exe usando PyInstaller.

Uso:
    cd notch-win/
    pip install pyinstaller
    python installer/build.py

O executável final fica em installer/dist/NotchSetup.exe
"""

import subprocess
import sys
import shutil
from pathlib import Path

HERE    = Path(__file__).resolve().parent   # notch-win/installer/
ROOT    = HERE.parent                        # notch-win/
DIST    = HERE / "dist"
WORK    = HERE / "build"
WIZARD  = HERE / "setup_wizard.py"
ICON    = HERE / "notch.ico"                # opcional — coloque um .ico aqui

def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "NotchSetup",
        "--distpath", str(DIST),
        "--workpath", str(WORK),
        "--specpath", str(HERE),
        # Empacota o app inteiro como dado — acessível via sys._MEIPASS/app/
        # No Windows o separador é ";" — no Linux/Mac é ":"
        "--add-data", f"{ROOT};app" if sys.platform == "win32" else f"{ROOT}:app",
        # Garante que tkinter esteja disponível
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
    ]

    if ICON.exists():
        cmd += ["--icon", str(ICON)]

    cmd.append(str(WIZARD))

    print("=" * 60)
    print("Construindo NotchSetup.exe...")
    print("=" * 60)
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe = DIST / "NotchSetup.exe"
        print(f"\n✓ Sucesso! Instalador gerado em:\n  {exe}")
    else:
        print("\n✗ Build falhou. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    import os
    build()
