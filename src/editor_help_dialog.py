from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

import ui.editor_help

class EditorHelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = ui.editor_help.Ui_Dialog()
        self.ui.setupUi(self)
        # vbox =  QVBoxLayout(self)
        
        path = '/home/houston/codes_sources/Patchichi/manual/en/editor_help.html'
        
        file = open(path, 'r')
        contents = file.read()
        
        # self.ui.textBrowser.setHtml(contents)
        # self.ui.webView.set
        # self._web_view = QWebEngineView(self)
        # self._web_view.setHtml(contents)
        # vbox.addWidget(self._web_view)
        self.ui.webEngineView.setHtml(contents)
        