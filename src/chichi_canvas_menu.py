import inspect
import threading
from typing import TYPE_CHECKING
import sys

from qtpy.QtCore import Slot # type:ignore
from qtpy.QtWidgets import QMenu

from patchbay.menus.canvas_menu import CanvasMenu

if TYPE_CHECKING:
    from patchichi_pb_manager import PatchichiPatchbayManager


class ChichiCanvasMenu(CanvasMenu):
    def __init__(self, patchbay_manager: 'PatchichiPatchbayManager'):
        super().__init__(patchbay_manager)
        
    def _build(self):
        super()._build()
        
        if 'tests_actions' in sys.modules:
            del sys.modules['tests_actions']
        import tests_actions
        
        self._tests_acts_menu = QMenu(self)
        self._tests_acts_menu.setTitle('Special Actions')
        
        for func in [
                obj for name, obj in inspect.getmembers(tests_actions)
                if inspect.isfunction(obj)
                    and obj.__module__ == tests_actions.__name__
                    and not name.startswith('_')]:
            _special_act = self._tests_acts_menu.addAction(func.__name__)
            _special_act.setData(func)
            _special_act.triggered.connect(self._special_act_triggered)
        self.addMenu(self._tests_acts_menu)
        
    @Slot()
    def _special_act_triggered(self):
        func = self.sender().data() # type:ignore
        thread = threading.Thread(target=func, args=[self.mng])
        thread.start()