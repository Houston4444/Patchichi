#!/usr/bin/python3 -u

APP_TITLE = 'Patchichi'
VERSION = (0, 5, 0)

from enum import Enum, auto
import sys
from typing import TYPE_CHECKING


class ReadArg(Enum):
    NONE = auto()
    SCENE = auto()
    DBG = auto()
    INFO = auto()


# manage arguments now
# Yes, that is not conventional to do this kind of code during imports
# but it allows faster answer for --version argument.
scene_to_load = ''
info_str = ''
debug_str = ''
read_arg = ReadArg.SCENE

for arg in sys.argv[1:]:
    match arg:
        case '--version':
            sys.stdout.write('.'.join([str(i) for i in VERSION]) + '\n')
            sys.exit(0)
        case '--help':
            from help_message import HELP_MESSAGE
            sys.stdout.write(HELP_MESSAGE)
            sys.exit(0)
        case '--dbg'|'-dbg':
            read_arg = ReadArg.DBG
        case '--info'|'-info':
            read_arg = ReadArg.INFO
        case _:
            match read_arg:
                case ReadArg.DBG:
                    debug_str = arg
                case ReadArg.INFO:
                    info_str = arg
                case ReadArg.SCENE:
                    scene_to_load = arg

import os
from pathlib import Path

# set HoustonPatchbay submodule as lib
sys.path.insert(1, str(Path(__file__).parents[1] / 'HoustonPatchbay/source'))

from qt_api import QT_API

# Needed for qtpy to know if it should use PyQt5 or PyQt6
os.environ['QT_API'] = QT_API

import signal
import logging

from dataclasses import dataclass
from os.path import dirname
from pathlib import Path

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QIcon, QFontDatabase
from qtpy.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings

from main_win import MainWindow
from patchichi_pb_manager import PatchichiPatchbayManager


_logger = logging.getLogger()
_log_handler = logging.StreamHandler()
_log_handler.setFormatter(logging.Formatter(
    f"%(levelname)s:%(name)s - %(message)s"))
_logger.addHandler(_log_handler)

if info_str:
    for module_name in info_str.split(':'):
        _mod_logger = logging.getLogger(module_name)
        _mod_logger.setLevel(logging.INFO)

if debug_str:
    for module_name in debug_str.split(':'):
        _mod_logger = logging.getLogger(module_name)
        _mod_logger.setLevel(logging.DEBUG)



@dataclass
class Main:
    app: QApplication
    main_win: MainWindow
    patchbay_manager: PatchichiPatchbayManager
    settings: QSettings


def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGTERM):
        QApplication.quit()

def get_code_root():
    return dirname(dirname(__file__))

def make_logger():
    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter(
        f"%(name)s - %(levelname)s - %(message)s"))
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_handler)

def main_loop():
    make_logger()
    
    import resources_rc
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion('.'.join([str(i) for i in VERSION]))
    app.setOrganizationName(APP_TITLE)
    app.setWindowIcon(QIcon(
        f':/main_icon/scalable/{APP_TITLE.lower()}.svg'))
    app.setDesktopFileName(APP_TITLE.lower())
    
    ### Translation process
    app_translator = QTranslator()
    if app_translator.load(QLocale(), APP_TITLE.lower(),
                           '_', "%s/locale" % get_code_root()):
        app.installTranslator(app_translator)

    patchbay_translator = QTranslator()
    if patchbay_translator.load(
            QLocale(), 'patchbay',
            '_', "%s/HoustonPatchbay/locale" % get_code_root()):
        app.installTranslator(patchbay_translator)

    sys_translator = QTranslator()
    if QT_API != 'PyQt5' or TYPE_CHECKING:
        path_sys_translations = QLibraryInfo.path(
            QLibraryInfo.LibraryPath.TranslationsPath)
    else:
        path_sys_translations = QLibraryInfo.location(
            QLibraryInfo.TranslationsPath)
    sys_translator.load(path_sys_translations)
    app.installTranslator(sys_translator)

    QFontDatabase.addApplicationFont(":/fonts/Ubuntu-R.ttf")
    QFontDatabase.addApplicationFont(":/fonts/Ubuntu-C.ttf")

    #connect signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    #needed for signals SIGINT, SIGTERM
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    settings = QSettings()
    main_win = MainWindow()
    pb_manager = PatchichiPatchbayManager(settings)

    main = Main(app, main_win, pb_manager, settings)
    pb_manager.finish_init(main)
    main_win.finish_init(main)
    main_win.show()

    load_scene_ok = False
    if scene_to_load:
        load_scene_ok = main_win.load_scene_at_startup(scene_to_load)
    
    last_patch = Path(settings.fileName()).parent / 'last.patchichi.json'

    # auto load patch as it was at last exit
    # It doesn't loads a saved scene
    # 'Save file' action will ask the destination path
    if not load_scene_ok:
        if last_patch.is_file():
            pb_manager.load_file(last_patch)
        else:
            default_patch = (Path(__file__).parent.parent
                            / 'scenes' / 'default_cardboard.patchichi.json')
            if default_patch.is_file():
                pb_manager.load_file(default_patch)

    app.exec()
    settings.sync()
    pb_manager.save_patchcanvas_cache()
    
    # save file to last patch if there are groups
    if pb_manager.groups:
        pb_manager.save_file_to(last_patch)
    
    del app


if __name__ == '__main__':
    main_loop()
