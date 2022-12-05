import logging
from pathlib import Path
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

import ui.editor_help

_logger = logging.Logger(__name__)

class EditorHelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = ui.editor_help.Ui_Dialog()
        self.ui.setupUi(self)

        path = Path(__file__).parent.parent / 'manual' / 'en' / 'editor_help.html'
        try:
            with open(path, 'r') as file:
                contents = file.read()
        except Exception as e:
            _logger(str(e))
            return
        
        self.ui.webEngineView.setHtml(contents)
        