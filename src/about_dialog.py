
from qtpy.QtWidgets import QDialog, QApplication
from qtpy.QtCore import QSize

from ui.about_patchichi import Ui_DialogAboutPatchichi

import resourcer

class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_DialogAboutPatchichi()
        self.ui.setupUi(self)
        self.ui.labelPixmap.setPixmap(
            resourcer.main_icon().pixmap(QSize(128, 128)))
        self.ui.labelRayAndVersion.setText(
            self.ui.labelRayAndVersion.text() % QApplication.applicationVersion())