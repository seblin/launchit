#!/usr/bin/env python
# Stdlib
import sys
# 3rd party
from PySide import QtGui
# launchit package
import core

class MarkedCompletionDelegate(QtGui.QItemDelegate):
    def __init__(self, start_mark='<b><u>', end_mark='</u></b>', parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.fragment = ''
        self.renderer = QtGui.QTextDocument()

    def paint(self, painter, option, index):
        self.drawBackground(painter, option, index)
        self.draw_contents(painter, option, index)

    def draw_contents(self, painter, option, index):
        painter.save()
        painter.translate(option.rect.topLeft())
        self._draw_marked_text(painter, index.data(), option.rect.width())
        painter.restore()

    def _draw_marked_text(self, painter, text, width):
        # Note that truncation can't be made with QFontMetrics.elidedText() 
        # here, since that doesn't handle rich text. The trial and error 
        # approach has been chosen in order to avoid messing with the 
        # rendering engine. There probably should be no situation where 
        # memory consumption of this method is really getting noticeable.
        ellipsis = '...'
        rendered_width = self.renderer.idealWidth
        markup = self._markup_for_completion(text)
        self.renderer.setHtml(markup)
        while text and (rendered_width() > width):
            text = text[:-1]
            markup = self._markup_for_completion(text)
            self.renderer.setHtml(markup + ellipsis)
        self.renderer.drawContents(painter)

    def _markup_for_completion(self, completion):
        return core.get_marked_completion(completion, self.fragment, 
                                          self.start_mark, self.end_mark)

    def sizeHint(self, option, index):
        return self.renderer.size().toSize()

class CommandlineCompleter(QtGui.QCompleter):
    def __init__(self, parent=None):
        QtGui.QCompleter.__init__(self, parent)
        mode = self.UnfilteredPopupCompletion
        self.setCompletionMode(mode)
        model = QtGui.QStringListModel()
        self.setModel(model)
        delegate = MarkedCompletionDelegate()
        self.popup().setItemDelegate(delegate)

    def update(self, fragment):
        completions = core.get_name_completions(fragment)
        self.model().setStringList(completions)
        self.popup().itemDelegate().fragment = fragment

class LaunchEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        completer = CommandlineCompleter()
        self.textEdited.connect(completer.update)
        self.setCompleter(completer)
        self.returnPressed.connect(self.launch)

    def launch(self):
        core.launch(self.text())

def run_app(args=[]):
    app = QtGui.QApplication(args)
    edit = LaunchEdit()
    edit.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(run_app(sys.argv))
