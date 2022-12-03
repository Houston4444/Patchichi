# from math import round

from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtGui import QPaintEvent, QResizeEvent, QColor, QTextFormat, QPainter, QTextCursor
from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView

from patchbay import PatchbayToolsWidget, FilterFrame, PatchGraphicsView
from patchbay.tool_bar import PatchbayToolBar
from patchbay.type_filter_frame import TypeFilterFrame

from code_editor import CodeEditor

class JackStatesWidget(PatchbayToolsWidget):
    def __init__(self, parent):
        super().__init__()
        

class PatchFilterFrame(FilterFrame):
    pass

        
class PatchichiGraphicsView(PatchGraphicsView):
    pass


