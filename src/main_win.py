
from dis import dis
import os
from pathlib import Path
from re import L
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QShortcut, QMenu, QApplication, QToolButton, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSlot

from about_dialog import AboutDialog
from editor_help_dialog import EditorHelpDialog
from patchbay.tools_widgets import PatchbayToolsWidget
from patchbay.base_elements import ToolDisplayed
from patchbay.patchcanvas import xdg

from ui.main_win import Ui_MainWindow
from xdg import xdg_data_home


if TYPE_CHECKING:
    from patchichi import Main

_translate = QApplication.translate


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.patchbay_manager = None
        self.settings = None

        self.main_menu = QMenu()
        self.last_separator = self.main_menu.addSeparator()
        self.main_menu.addMenu(self.ui.menuHelp)
        self.main_menu.addAction(self.ui.actionShowMenuBar)
        self.main_menu.addAction(self.ui.actionQuit)
        
        self.menu_button = self.ui.toolBar.widgetForAction(self.ui.actionMainMenu)
        if TYPE_CHECKING:
            assert isinstance(self.menu_button, QToolButton)
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setMenu(self.main_menu)
        
        self.ui.filterFrame.setVisible(False)
        self.ui.actionShowMenuBar.toggled.connect(self._menubar_shown_toggled)
        self.ui.actionQuit.triggered.connect(QApplication.quit)
        self.ui.actionAboutPatchichi.triggered.connect(self._show_about_dialog)
        self.ui.actionAboutQt.triggered.connect(QApplication.aboutQt)

        self.ui.actionLoadScene.triggered.connect(self._load_scene)
        self.ui.actionSaveScene.triggered.connect(self._save_scene)
        self.ui.actionSaveAs.triggered.connect(self._save_scene_as)
        self.ui.toolButtonEditorHelp.clicked.connect(self._show_editor_help)

        filter_bar_shortcut = QShortcut('Ctrl+F', self)
        filter_bar_shortcut.setContext(Qt.ApplicationShortcut)
        filter_bar_shortcut.activated.connect(
            self.toggle_filter_frame_visibility)
        
        refresh_shortcut = QShortcut('Ctrl+R', self)
        refresh_shortcut.setContext(Qt.ApplicationShortcut)
        refresh_shortcut.activated.connect(self.refresh_patchbay)
        refresh_shortcut_alt = QShortcut('F5', self)
        refresh_shortcut_alt.setContext(Qt.ApplicationShortcut)
        refresh_shortcut_alt.activated.connect(self.refresh_patchbay)
        
        self._normal_screen_maximized = False
        self._normal_screen_had_menu = False

        patchbay_tools_act = self.ui.toolBar.addWidget(PatchbayToolsWidget())
        self.patchbay_tools = self.ui.toolBar.widgetForAction(patchbay_tools_act)
        self.ui.toolBar.set_default_displayed_widgets(
            ToolDisplayed.PORT_TYPES_VIEW| ToolDisplayed.ZOOM_SLIDER)
        
        self.ui.plainTextEditPorts.textChanged.connect(self._text_changed)
        
        self.ui.graphicsView.setFocus()
        
        self._current_path: Optional[Path] = None
        
    def finish_init(self, main: 'Main'):
        self.patchbay_manager = main.patchbay_manager
        self.settings = main.settings
        self.ui.toolBar.set_patchbay_manager(main.patchbay_manager)
        self.ui.filterFrame.set_patchbay_manager(main.patchbay_manager)
        main.patchbay_manager.sg.filters_bar_toggle_wanted.connect(
            self.toggle_filter_frame_visibility)
        main.patchbay_manager.sg.full_screen_toggle_wanted.connect(
            self.toggle_patchbay_full_screen)
        geom = self.settings.value('MainWindow/geometry')

        if geom:
            self.restoreGeometry(geom)
        
        main_splitter_sizes = self.settings.value(
            'MainWindow/splitter_canvas_sizes', [273, 1115], type=list)
        self.ui.splitterMainVsCanvas.setSizes(
            [int(s) for s in main_splitter_sizes])
        port_logs_sizes = self.settings.value(
            'MainWindow/splitter_portlogs_sizes', [687, 139], type=list)
        self.ui.splitterPortsVsLogs.setSizes(
            [int(s) for s in port_logs_sizes])

        self._normal_screen_maximized = self.isMaximized()
        
        show_menubar = self.settings.value(
            'MainWindow/show_menubar', False, type=bool)
        self.ui.actionShowMenuBar.setChecked(show_menubar)
        self.ui.menubar.setVisible(show_menubar)

        self.ui.menubar.addMenu(main.patchbay_manager.canvas_menu)
        self.main_menu.insertMenu(
            self.last_separator, main.patchbay_manager.canvas_menu)

        self.ui.toolBar.set_default_displayed_widgets(
            ToolDisplayed.PORT_TYPES_VIEW
            | ToolDisplayed.ZOOM_SLIDER)
        
        # self.ui.splitterMainVsCanvas.setSizes([10, 90])

    def _menubar_shown_toggled(self, state: int):
        self.ui.menubar.setVisible(bool(state))
    
    def _show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def _text_changed(self):
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.update_from_text(
            self.ui.plainTextEditPorts.toPlainText())
    
    def get_editor_text(self) -> str:
        return self.ui.plainTextEditPorts.toPlainText()
    
    def refresh_patchbay(self):
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.refresh()
    
    def toggle_patchbay_full_screen(self):
        if self.isFullScreen():
            self.ui.verticalLayout.setContentsMargins(2, 2, 2, 2)
            self.ui.toolBar.setVisible(True)
            self.showNormal()
            if self._normal_screen_maximized:
                self.showMaximized()
            
            self.ui.menubar.setVisible(self._normal_screen_had_menu)
                
        else:
            self._normal_screen_maximized = self.isMaximized()
            self._normal_screen_had_menu = self.ui.menubar.isVisible()
            self.ui.menubar.setVisible(False)
            self.ui.toolBar.setVisible(False)
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()

    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())

    def set_logs_text(self, text: str):
        self.ui.textEditLogs.setPlainText(text)

    def _get_scenes_path(self) -> Path:
        scenes_dir = xdg_data_home() / 'Patchichi' / 'scenes'
        try:
            if not scenes_dir.exists():
                scenes_dir.mkdir()
        except:
            return Path.home()

        return scenes_dir
    
    @pyqtSlot()
    def _load_scene(self):
        ret, ok = QFileDialog.getOpenFileName(
            self,
            _translate('file_dialog', 'Choose the patchichi scene to load...'),
            str(self._get_scenes_path()),
            _translate('file_dialog', 'Patchichi files (*.patchichi.json)'))

        if ok:
            if self.patchbay_manager.load_file(Path(ret)):
                self._current_path = Path(ret)
                scene_name = self._current_path.name.rpartition(
                    '.patchichi.json')[0]
                self.setWindowTitle(
                    f"Patchichi - {scene_name}")
    
    @pyqtSlot()
    def _save_scene(self):
        if self._current_path is None:
            self._save_scene_as()
            return
        
        if not self.patchbay_manager.save_file_to(self._current_path):
            # TODO error dialog
            pass
    
    @pyqtSlot()
    def _save_scene_as(self):
        ret, ok = QFileDialog.getSaveFileName(
            self,
            _translate('file_dialog', 'Where do you want to save this patchbay scene ?'),
            str(self._get_scenes_path()),
            _translate('file_dialog', 'Patchichi files (*.patchichi.json)'))

        if not ok:
            return

        if self.patchbay_manager.save_file_to(Path(ret)):
            self._current_path = Path(ret)
            scene_name = self._current_path.name.rpartition('.patchichi.json')[0]
            self.setWindowTitle(
                f"Patchichi - {scene_name}")

    @pyqtSlot()
    def _show_editor_help(self):
        dialog = EditorHelpDialog(self)
        dialog.show()
        

    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        self.settings.setValue(
            'MainWindow/splitter_canvas_sizes',
            self.ui.splitterMainVsCanvas.sizes())
        self.settings.setValue(
            'MainWindow/splitter_portlogs_sizes',
            self.ui.splitterPortsVsLogs.sizes())
    
        super().closeEvent(event)
    