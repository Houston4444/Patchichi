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
        
        if 'strange_events' in sys.modules:
            del sys.modules['strange_events']
        import strange_events

        self.strange_events_menu = QMenu(self)
        self.strange_events_menu.setTitle('Strange events')

        for func in [
                obj for name, obj in inspect.getmembers(strange_events)
                if inspect.isfunction(obj)
                    and obj.__module__ == strange_events.__name__
                    and not name.startswith('_')]:
            _special_act = self.strange_events_menu.addAction(func.__name__)
            _special_act.setData(func)
            _special_act.triggered.connect(self._special_act_triggered)
        self.addMenu(self.strange_events_menu)

    @Slot()
    def _special_act_triggered(self):
        func = self.sender().data() # type:ignore
        thread = threading.Thread(target=func, args=[self.mng])
        thread.start()