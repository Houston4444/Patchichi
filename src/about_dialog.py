
from PyQt5.QtWidgets import QDialog, QApplication
from ui.about_patchichi import Ui_DialogAboutPatchichi

class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_DialogAboutPatchichi()
        self.ui.setupUi(self)
        self.ui.labelRayAndVersion.setText(
            self.ui.labelRayAndVersion.text() % QApplication.applicationVersion())