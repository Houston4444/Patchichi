from pathlib import Path
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

import ui.editor_help

class EditorHelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = ui.editor_help.Ui_Dialog()
        self.ui.setupUi(self)

        path = Path(__file__).parent.parent / 'manual' / 'en' / 'editor_help.html'
        file = open(path, 'r')
        contents = file.read()
        
        self.ui.webEngineView.setHtml(contents)
        