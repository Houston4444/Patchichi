

from patchbay import PatchbayToolsWidget, FilterFrame, PatchGraphicsView
from patchbay.tool_bar import PatchbayToolBar


class JackStatesWidget(PatchbayToolsWidget):
    def __init__(self, parent):
        super().__init__()
        

class PatchFilterFrame(FilterFrame):
    pass

        
class PatchichiGraphicsView(PatchGraphicsView):
    pass


class PatchichiToolBar(PatchbayToolBar):
    pass