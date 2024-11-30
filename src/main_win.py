

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from qtpy.QtWidgets import (
    QMainWindow, QShortcut, QMenu, QApplication, QToolButton, QFileDialog,
    QBoxLayout, QVBoxLayout, QFrame, QSpacerItem, QSizePolicy, QWidget)
from qtpy.QtGui import QKeyEvent, QResizeEvent
from qtpy.QtCore import Qt, Slot

from about_dialog import AboutDialog
from xdg import xdg_data_home
from manual_tools import get_manual_path, open_in_browser

from patchbay.view_selector_frame import ViewSelectorWidget
from patchbay.type_filter_frame import TypeFilterFrame
from patchbay.surclassed_widgets import ZoomSlider
from patchbay.tools_widgets import PatchbayToolsWidget, TextWithIcons
from patchbay.bar_widget_transport import BarWidgetTransport
from patchbay.bar_widget_jack import BarWidgetJack
from patchbay.bar_widget_canvas import BarWidgetCanvas
from patchbay.base_elements import ToolDisplayed

from ui.main_win import Ui_MainWindow

try:
    from editor_help_dialog import EditorHelpDialog
    HAS_WEB_ENGINE = True
except ImportError:
    HAS_WEB_ENGINE = False

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
        
        self.menu_button = self.ui.toolBar.widgetForAction(
            self.ui.actionMainMenu)

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
        
        self.ui.plainTextEditPorts.textChanged.connect(self._text_changed)
        self.ui.plainTextEditPorts.cursor_on_port.connect(
            self._select_port_in_patchbay)
        self.ui.plainTextEditPorts.cursor_on_group.connect(
            self._select_group_in_patchbay)
        
        self.ui.checkBoxAutoUpdate.stateChanged.connect(
            self._auto_update_changed)
        self.ui.pushButtonUpdatePatchbay.clicked.connect(
            self.refresh_patchbay)
        self.ui.pushButtonUpdatePatchbay.setVisible(False)

        splitter_handle = self.ui.splitterPortsVsLogs.handle(1)
        layout = QVBoxLayout(splitter_handle)
        self._splitter_line = QFrame(splitter_handle)
        self._splitter_line.setFrameShape(QFrame.HLine)
        self._splitter_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(self._splitter_line)
        
        self.ui.graphicsView.setFocus()
        
        self._current_path: Optional[Path] = None

        self._tools_widgets = PatchbayToolsWidget()
        self._tools_widgets.set_tool_bars(
            self.ui.toolBar, self.ui.toolBarTransport,
            self.ui.toolBarJack, self.ui.toolBarCanvas)
        
    def finish_init(self, main: 'Main'):
        self.patchbay_manager = main.patchbay_manager
        self.settings = main.settings
        # self.ui.toolBar.set_patchbay_manager(main.patchbay_manager)
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
        
        default_disp_widg = (
            ToolDisplayed.PORT_TYPES_VIEW
            | ToolDisplayed.ZOOM_SLIDER
            | ToolDisplayed.TRANSPORT_CLOCK
            | ToolDisplayed.TRANSPORT_PLAY_STOP
            | ToolDisplayed.BUFFER_SIZE
            | ToolDisplayed.SAMPLERATE
            | ToolDisplayed.XRUNS
            | ToolDisplayed.DSP_LOAD)
        
        text_with_icons = TextWithIcons.by_name(
            self.settings.value(
                'tool_bar/text_with_icons', 'YES'))
        default_disp_str = self.settings.value(
            'tool_bar/jack_elements', '', type=str)
        
        main.patchbay_manager._tools_widget.change_text_with_icons(
            text_with_icons)
        main.patchbay_manager._tools_widget.change_tools_displayed(
            default_disp_widg.filtered_by_string(default_disp_str))

    def _menubar_shown_toggled(self, state: int):
        self.ui.menubar.setVisible(bool(state))
    
    def _show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def _auto_update_changed(self, state: int):
        self.ui.pushButtonUpdatePatchbay.setVisible(not bool(state))
        if state and self.patchbay_manager is not None:
            self.patchbay_manager.update_from_text(
                self.get_editor_text())
    
    def _text_changed(self):
        if not self.ui.checkBoxAutoUpdate.isChecked():
            return
        
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.update_from_text(
            self.get_editor_text())
    
    def get_editor_text(self) -> str:
        return self.ui.plainTextEditPorts.toPlainText()
    
    def _select_port_in_patchbay(self, full_port_name: str):
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.select_port(full_port_name)
    
    def _select_group_in_patchbay(self, group_name: str):
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.select_group(group_name)

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
    
    def load_scene_at_startup(self, scene_name: str) -> bool:
        if scene_name.endswith('.patchichi.json'):
            scene_path = Path(scene_name)
        else:
            scene_path = self._get_scenes_path() / f'{scene_name}.patchichi.json'
        
        if self.patchbay_manager.load_file(scene_path):
            self._current_path = scene_path
            scene_name = self._current_path.name.rpartition(
                '.patchichi.json')[0]
            self.setWindowTitle(
                f"Patchichi - {scene_name}")
            return True

        return False
    
    @Slot()
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
    
    @Slot()
    def _save_scene(self):
        if self._current_path is None:
            self._save_scene_as()
            return
        
        if not self.patchbay_manager.save_file_to(self._current_path):
            # TODO error dialog
            pass
    
    @Slot()
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

    @Slot()
    def _show_editor_help(self):
        if HAS_WEB_ENGINE:
            dialog = EditorHelpDialog(self)
            dialog.show()
            return
        
        open_in_browser(self, get_manual_path())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._tools_widgets.main_win_resize(self)

    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        self.settings.setValue(
            'MainWindow/splitter_canvas_sizes',
            self.ui.splitterMainVsCanvas.sizes())
        self.settings.setValue(
            'MainWindow/splitter_portlogs_sizes',
            self.ui.splitterPortsVsLogs.sizes())
        
        if self.patchbay_manager is not None:
            self.settings.setValue(
                'tool_bar/text_with_icons',
                self.patchbay_manager._tools_widget._text_with_icons.name)

            tools_displayed = \
                self.patchbay_manager._tools_widget._tools_displayed
            self.settings.setValue(
                'tool_bar/jack_elements',
                tools_displayed.to_save_string())
            self.patchbay_manager.save_settings()
    
        super().closeEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.patchbay_manager.key_press_event(event)