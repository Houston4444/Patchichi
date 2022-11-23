
from dataclasses import dataclass
from operator import is_
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PyQt5.QtGui import (
    QPaintEvent, QColor, QPainter, QResizeEvent, QFont,
    QTextFormat, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QTextDocument)
from PyQt5.QtCore import Qt, QRect, QSize, QRegularExpression
from patchbay.patchcanvas.init_values import BoxLayoutMode

from string_sep import string_sep, PRE_ATTRIBUTES, POST_ATTRIBUTES

# Code translated from C++ from 
# https://doc.qt.io/qt-6/qtwidgets-widgets-codeeditor-example.html

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setStyleSheet('QPlainTextEdit{background-color:#1e1e1e; color:white}')
        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        # self.cursorPositionChanged.connect(self._highlight_current_line)
        
        self._update_line_number_area_width(0)
        
        self._highlighter = Highlighter(self.document())
        # self._highlight_current_line()

    def line_number_area_paint_event(self, event: QPaintEvent):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(127, 127, 127, 40))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(
            self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(144, 144, 144))
                painter.drawText(
                    0,
                    top, 
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
    
    def line_number_area_width(self) -> int:
        digits = 1
        maxi = max(1, self.blockCount())
        while maxi >= 10:
            maxi /= 10
            digits += 1
            
        return 7 + self.fontMetrics().horizontalAdvance('9') * digits

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
    
    def _update_line_number_area_width(self, new_block_count: int):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    
    def _highlight_current_line(self):
        extra_selections = list[QTextEdit.ExtraSelection]()
        
        if not self.isReadOnly():
            sel_box = QTextEdit.ExtraSelection()
            line_color = QColor(255, 255, 80, 20)
            sel_box.format.setBackground(line_color)
            sel_box.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel_box.cursor = self.textCursor()
            sel_box.cursor.clearSelection()
            extra_selections.append(sel_box)
        
        block = self.firstVisibleBlock()
        while block.isValid():
            GROUP_COLOR = QColor(100, 214, 189)
            ATTR_PRE_COLOR = QColor(150, 211, 241)
            ATTR_POST_COLOR = QColor(220, 220, 170)
            ATTR_ERR_COLOR = QColor(255, 0, 0)
            VALUE_COLOR = QColor(206, 145, 120)
            # text_color = None
            str_role = ''
            if block.text().startswith('::'):
                # text_color = QColor(100, 214, 189)
                str_role = '::'
            elif block.text().startswith(':'):
                # text_color = QColor(150, 211, 241)
                str_role = ':'

            if str_role:
                start = block.position()
                end = start + block.length() -1
                # print(start, end)
                if str_role == '::' and end >= 2:
                    sel_box = QTextEdit.ExtraSelection()
                    sel_box.format.setForeground(GROUP_COLOR)
                    sel_box.format.setFontWeight(800)
                    sel_box.cursor = QTextCursor(block)
                    sel_box.cursor.setPosition(
                        start + 2, QTextCursor.MoveAnchor)
                    sel_box.cursor.setPosition(
                        end, QTextCursor.KeepAnchor)
                    
                    extra_selections.append(sel_box)
                
                elif str_role == ':':
                    test_ze = False
                    if block.text().startswith(':ICON_NAME=appl'):
                        test_ze = True
                        print('zkoe', block.lineCount(), block.length(), block.text() )
                    for word, wstart, wend, is_value in string_sep(
                            block.text(), split_equal=True):
                        if test_ze:
                            print('sp', is_value, word)
                        
                        sel = QTextEdit.ExtraSelection()
                        if is_value:
                            sel.format.setForeground(VALUE_COLOR)
                        elif word in PRE_ATTRIBUTES:
                            sel.format.setForeground(ATTR_PRE_COLOR)
                        elif word in POST_ATTRIBUTES:
                            sel.format.setForeground(ATTR_POST_COLOR)
                        else:
                            sel.format.setForeground(ATTR_ERR_COLOR)

                        sel.cursor = QTextCursor(block)
                        sel.cursor.setPosition(start + wstart, QTextCursor.MoveAnchor)
                        sel.cursor.setPosition(start + wend + 1, QTextCursor.KeepAnchor)
                        extra_selections.append(sel)
                    
                    
                    # colon_indexes = [i for i, x in enumerate(block.text())
                    #                  if x == ':']
                    
                    # for i in range(len(colon_indexes)):
                    #     col_index = colon_indexes[i]
                    #     start = col_index + 1
                        
                    #     if i + 1 == len(colon_indexes):
                    #         end = block.length()
                    #     else:
                    #         # print('ofk', i, colon_indexes)
                    #         end = colon_indexes[i+1]
                            
                    #     sel = QTextEdit.ExtraSelection()
                    #     sel.format.setForeground(ATTR_OK_COL)
                    #     sel.cursor = QTextCursor(block)
                    #     sel.cursor.setPosition(start, QTextCursor.MoveAnchor)
                    #     sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
                    #     extra_selections.append(sel)
                        
                        
                # else:
                #     selection.cursor.setPosition(
                #         block.position() + 1, QTextCursor.MoveAnchor)
                #     selection.cursor.setPosition(
                #         block.position() + block.length(), QTextCursor.KeepAnchor)
                #     extra_selections.append(selection)
            block = block.next()
        
        self.setExtraSelections(extra_selections)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    # def paintEvent(self, event: QPaintEvent) -> None:
    #     self._highlight_current_line()
        
    #     super().paintEvent(event)

class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._code_editor = editor
    
    def sizeHint(self) -> QSize:
        return QSize(self._code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event: QPaintEvent):
        self._code_editor.line_number_area_paint_event(event)
        

DARK_SCHEME = {
    'GROUP_COLOR': QColor(100, 214, 189),
    'ATTR_PRE_COLOR': QColor(150, 211, 241),
    'ATTR_POST_COLOR': QColor(220, 220, 170),
    'ATTR_ERR_COLOR': QColor(255, 0, 0),
    'VALUE_COLOR': QColor(206, 145, 120)
}


@dataclass
class HighlightingRule:
    pattern: QRegularExpression
    format: QTextCharFormat


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._parent = parent
        
        self._col = DARK_SCHEME
        
        self._default_format = QTextCharFormat()
        
        self._group_format = QTextCharFormat()
        self._group_format.setForeground(self._col['GROUP_COLOR'])
        # self._group_format.setFontWeight(QFont.Bold)
        
        self._pre_attr_format = QTextCharFormat()
        self._pre_attr_format.setForeground(self._col['ATTR_PRE_COLOR'])
        # self._pre_attr.setFontWeight(QFont.Bold)
        
        self._post_attr_format = QTextCharFormat()
        self._post_attr_format.setForeground(self._col['ATTR_POST_COLOR'])
        
        self._value_format = QTextCharFormat()
        self._value_format.setForeground(self._col['VALUE_COLOR'])
        
        self._err_format = QTextCharFormat()
        self._err_format.setForeground(self._col['ATTR_ERR_COLOR'])
        
        self._highlighting_rules = list[HighlightingRule]()
        
        # keyword_patterns = PRE_ATTRIBUTES
        for attr_str in PRE_ATTRIBUTES:
            self._highlighting_rules.append(
                HighlightingRule(QRegularExpression(attr_str),
                                 self._pre_attr_format))
            
        for attr_str in POST_ATTRIBUTES:
            self._highlighting_rules.append(
                HighlightingRule(QRegularExpression(attr_str),
                                 self._post_attr_format))
    
    def highlightBlock(self, text: str):
        if text.startswith('::'):
            if len(text) > 2:
                self.setFormat(2, len(text) -1, self._group_format)
                
        elif text.startswith(':'):
            for word, start, end, is_value in string_sep(text, split_equal=True, get_splitter=True):
                print(f"'{word}'")
                if is_value:
                    format = self._value_format
                elif word in PRE_ATTRIBUTES:
                    format = self._pre_attr_format
                elif word in POST_ATTRIBUTES:
                    format = self._post_attr_format
                elif word in (':', '='):
                    format = self._default_format
                else:
                    format = self._err_format
                self.setFormat(start, end, format)
        
    