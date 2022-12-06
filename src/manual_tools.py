

from pathlib import Path
import subprocess

from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication
from PyQt5.QtCore import QLocale

_translate = QApplication.translate


def get_manual_path() -> Path:
    lang = QLocale().name().partition('_')[0]
    
    manual_path = (Path(__file__).parent.parent
                   / 'manual' / lang / 'editor_help.html')
    
    if manual_path.is_file():
        return manual_path
    
    return Path(__file__).parent.parent / 'manual' / 'en' / 'editor_help.html'

def open_in_browser(parent: QWidget, path: Path):
    try:
        subprocess.Popen(['xdg-open', str(path)])
    except:
        ret = QMessageBox.critical(
            parent,
            _translate('help_error', 'Error'),
            _translate('help_error', 'failed to open help in browser !'),
            QMessageBox.Close)