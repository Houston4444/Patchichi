import logging

from qtpy.QtWidgets import QDialog

from manual_tools import open_in_browser, get_manual_path

import ui.editor_help

_logger = logging.Logger(__name__)

class EditorHelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = ui.editor_help.Ui_Dialog()
        self.ui.setupUi(self)

        try:
            with open(get_manual_path(), 'r') as file:
                contents = file.read()
        except Exception as e:
            _logger(str(e))
            return

        self.ui.webEngineView.setHtml(contents)
        self.ui.pushButtonOpenBrowser.clicked.connect(
            self._open_browser)
        
    def _open_browser(self):
        open_in_browser(self, get_manual_path())
        
