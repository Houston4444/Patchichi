
from dataclasses import dataclass
from enum import Enum
from telnetlib import LINEMODE
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QWidget, QCompleter, QApplication
from PyQt5.QtGui import (
    QPaintEvent, QColor, QPainter, QResizeEvent, QFont, QFocusEvent,
    QKeyEvent,
    QTextFormat, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QTextDocument)
from PyQt5.QtCore import Qt, QRect, QSize, QRegularExpression
from patchbay.patchcanvas.init_values import BoxLayoutMode

from string_sep import string_sep, PRE_ATTRIBUTES, POST_ATTRIBUTES


class LineMode(Enum):
    NONE = 0
    GROUP = 1
    ATTR = 2
    PORT = 3


DARK_SCHEME = {
    'GROUP_COLOR': QColor(100, 214, 189),
    'ATTR_PRE_COLOR': QColor(150, 211, 241),
    'ATTR_POST_COLOR': QColor(220, 220, 170),
    'ATTR_ERR_COLOR': QColor(255, 0, 0),
    'VALUE_COLOR': QColor(206, 145, 120)
}

LIGHT_SCHEME = {
    'GROUP_COLOR': QColor(60, 126, 91),
    'ATTR_PRE_COLOR': QColor(7, 23, 132),
    'ATTR_POST_COLOR': QColor(113, 100, 76),
    'ATTR_ERR_COLOR': QColor(255, 0, 0),
    'VALUE_COLOR': QColor(138, 80, 80)
}


# Code translated from C++ from 
# https://doc.qt.io/qt-6/qtwidgets-widgets-codeeditor-example.html

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        
        dark = self.palette().text().color().lightnessF() > 0.5
        
        if dark:
            self.setStyleSheet(
                'QPlainTextEdit{background-color:#1e1e1e; color:white}')
        else:
            self.setStyleSheet(
                'QPlainTextEdit{background-color:#eeeeee; color:black}')

        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._block_count_changed)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._update_completer_mode)
        
        self._update_line_number_area_width()
        
        self._highlighter = Highlighter(self.document(), dark)

        self._completer_mode = LineMode.NONE
        self._port_models = list[str]()
        self._completer = Completer([], self)
        self._set_completer(self._completer_mode)

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
    
    def _block_count_changed(self, new_block_count:int):
        self._update_line_number_area_width()
        if self._completer_mode is LineMode.PORT:
            cursor = self.textCursor()
            block = cursor.block().previous()
            if not block.text().startswith(':'):
                self._set_completer(LineMode.PORT)
    
    def _update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def _update_completer_mode(self):
        cursor = self.textCursor()
        block = cursor.block()
        
        completer_mode = LineMode.NONE
        
        if block.text().startswith('::'):
            completer_mode = LineMode.GROUP
        elif block.text().startswith(':'):
            completer_mode = LineMode.ATTR
        else:
            completer_mode = LineMode.PORT
            
        if completer_mode != self._completer_mode:
            self._set_completer(completer_mode)

    def _insert_completion(self, completion: str):
        if self._completer.widget() is not self:
            return
        
        if completion in ('PORTGROUP', 'PRETTY_NAME', 'PORT_ORDER',
                          'ICON_NAME', 'CLIENT_ICON'):
            completion += '='
        
        tc = self.textCursor()
        tc.movePosition(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
        tc.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        tc.removeSelectedText()
        tc.insertText(completion)
        self.setTextCursor(tc)

    def _get_completer(self):
        return self._completer

    def _set_completer(self, completer_mode: LineMode):
        del self._completer
        
        self._completer_mode = completer_mode
        
        if completer_mode is LineMode.ATTR:
            self._completer = Completer(
                list(PRE_ATTRIBUTES) + list(POST_ATTRIBUTES), self)
        elif completer_mode is LineMode.PORT:
            self._port_models.clear()
            for line in self.toPlainText().splitlines():
                if line.startswith(':'):
                    continue
                if not line[:-1] in self._port_models:
                    self._port_models.append(line[:-1])
            self._completer = Completer(self._port_models, self)
        else:
            self._completer = Completer([], self)
            
        if not self._completer:
            return
        
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.activated.connect(self._insert_completion)

    def _text_under_cursor(self) -> str:
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        if self._completer:
            self._completer.setWidget(self)
            
    def keyPressEvent(self, event: QKeyEvent):
        if self._completer and self._completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape,
                               Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        
        modifiers = QApplication.keyboardModifiers()
                
        super().keyPressEvent(event)
        
        ctrl_or_shift = modifiers & Qt.ControlModifier or modifiers & Qt.ShiftModifier
        if not self._completer or (ctrl_or_shift and not(event.text())):
            return
        
        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        has_modifier = bool(modifiers != Qt.NoModifier and not ctrl_or_shift)
        completion_prefix = self._text_under_cursor()
        
        if (has_modifier
                or not(event.text())
                or len(completion_prefix) < 1
                or event.text()[-1] in eow):
            self._completer.popup().hide()
            return
        
        if completion_prefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completion_prefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))
        
        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(0)
                    + self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr)


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._code_editor = editor
    
    def sizeHint(self) -> QSize:
        return QSize(self._code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event: QPaintEvent):
        self._code_editor.line_number_area_paint_event(event)


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument, dark=False):
        super().__init__(parent)
        self._col = DARK_SCHEME if dark else LIGHT_SCHEME

        self._default_format = QTextCharFormat()

        self._group_format = QTextCharFormat()
        self._group_format.setForeground(self._col['GROUP_COLOR'])        

        self._pre_attr_format = QTextCharFormat()
        self._pre_attr_format.setForeground(self._col['ATTR_PRE_COLOR'])

        self._post_attr_format = QTextCharFormat()
        self._post_attr_format.setForeground(self._col['ATTR_POST_COLOR'])

        self._value_format = QTextCharFormat()
        self._value_format.setForeground(self._col['VALUE_COLOR'])

        self._err_format = QTextCharFormat()
        self._err_format.setForeground(self._col['ATTR_ERR_COLOR'])
    
    def highlightBlock(self, text: str):
        if text.startswith('::'):
            if len(text) > 2:
                self.setFormat(2, len(text) -1, self._group_format)

        elif text.startswith(':'):
            for word, start, end, is_value in string_sep(
                    text, split_equal=True, get_splitter=True):
                if is_value:
                    format = self._value_format
                elif word in PRE_ATTRIBUTES:
                    format = self._pre_attr_format
                elif word in POST_ATTRIBUTES:
                    format = self._post_attr_format
                elif word in (':', '='):
                    format = self._default_format
                else:
                    if text.endswith(word):
                        for pre_attr in PRE_ATTRIBUTES:
                            if pre_attr.startswith(word.upper()):
                                format = self._pre_attr_format
                                break
                        else:
                            for post_attr in POST_ATTRIBUTES:
                                if post_attr.startswith(word.upper()):
                                    format = self._post_attr_format
                                    break
                            else:
                                format = self._err_format
                    else:
                        format = self._err_format
                self.setFormat(start, end, format)


class Completer(QCompleter):
    def __init__(self, *args):
        QCompleter.__init__(self, *args)
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() not in (Qt.Key_Right, Qt.Key_Tab, Qt.Key_Enter):
            event.ignore()
