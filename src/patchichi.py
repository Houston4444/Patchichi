#!/usr/bin/python3 -u

APP_TITLE = 'Patchichi'
VERSION = (0, 2, 0)

import sys

# manage arguments now
# Yes, that is not conventional to do this kind of code during imports
# but it allows faster answer for --version argument.
for arg in sys.argv[1:]:
    if arg == '--version':
        sys.stdout.write('.'.join([str(i) for i in VERSION]) + '\n')
        sys.exit(0)
    if arg == '--help':
        sys.stdout.write(
            "Abstract JACK patchbay application\n"
            "Usage: patchichi [--help] [--version]\n"
            "  --help     show this help\n"
            "  --version  print program version\n"
        )
        sys.exit(0)


import signal
import logging

from dataclasses import dataclass
from os.path import dirname
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings

from main_win import MainWindow
from patchichi_pb_manager import PatchichiPatchbayManager


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
    if patchbay_translator.load(QLocale(), 'patchbay',
                                '_', "%s/HoustonPatchbay/locale" % get_code_root()):
        app.installTranslator(patchbay_translator)

    sys_translator = QTranslator()
    path_sys_translations = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if sys_translator.load(QLocale(), 'qt', '_', path_sys_translations):
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

    # auto load patch as it was at last exit
    # It doesn't loads a saved scene
    # 'Save file' action will ask the destination path
    last_patch = Path(settings.fileName()).parent / 'last.patchichi.json'
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
