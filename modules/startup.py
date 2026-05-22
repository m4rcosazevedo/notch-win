import sys
import os
from pathlib import Path

def set_startup(enabled: bool):
    """Ativa ou desativa a inicialização automática com o sistema."""
    if sys.platform == "win32":
        _set_startup_windows(enabled)
    elif sys.platform == "linux":
        _set_startup_linux(enabled)

def is_startup_enabled() -> bool:
    """Verifica se a inicialização automática está ativa no sistema."""
    if sys.platform == "win32":
        return _is_startup_enabled_windows()
    elif sys.platform == "linux":
        return _is_startup_enabled_linux()
    return False

def _set_startup_windows(enabled: bool):
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        except PermissionError:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)

        if enabled:
            python_exe = sys.executable
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, '__file__'):
                script_path = os.path.abspath(main_module.__file__)
            else:
                script_path = os.path.abspath(sys.argv[0])
            
            if script_path.endswith(".py"):
                cmd = f'"{python_exe}" "{script_path}"'
            else:
                cmd = f'"{script_path}"'
                
            winreg.SetValueEx(key, "NotchWin", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "NotchWin")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Erro ao configurar inicialização no Windows: {e}")

def _is_startup_enabled_windows() -> bool:
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, "NotchWin")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False

def _set_startup_linux(enabled: bool):
    autostart_dir = Path.home() / ".config" / "autostart"
    desktop_file = autostart_dir / "notch-win.desktop"
    
    if enabled:
        try:
            autostart_dir.mkdir(parents=True, exist_ok=True)
            python_exe = sys.executable
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, '__file__'):
                script_path = os.path.abspath(main_module.__file__)
            else:
                script_path = os.path.abspath(sys.argv[0])
            
            exec_cmd = f'"{python_exe}" "{script_path}"' if script_path.endswith(".py") else f'"{script_path}"'
            
            content = f"""[Desktop Entry]
Type=Application
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Notch Win
Comment=Notch application
"""
            desktop_file.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"Erro ao configurar inicialização no Linux: {e}")
    else:
        if desktop_file.exists():
            try:
                desktop_file.unlink()
            except Exception:
                pass

def _is_startup_enabled_linux() -> bool:
    desktop_file = Path.home() / ".config" / "autostart" / "notch-win.desktop"
    return desktop_file.exists()
