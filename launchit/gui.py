#!/usr/bin/env python
# Stdlib
import sys

# 3rd party
from PySide import QtGui

# launchit package
from . import core, icongetter, settings

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

class CommandIconLabel(QtGui.QLabel):
    def __init__(self, icon_size=32, icon=QtGui.QIcon(), parent=None):
        QtGui.QLabel.__init__(self, parent)
        self.icon_size = icon_size
        self.icon = icon

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        width = height = self.icon_size
        pixmap = icon.pixmap(width, height)
        self.setPixmap(pixmap)
        self._icon = icon

    def set_icon_by_command(self, cmdline):
        # TODO: Implement theme detection for XFCE and LXDE, since these
        #       are not supported by Qt's theme detection. Currently the
        #       user must manually set the theme name inside launchit's
        #       configuration file, if using an unsupported environment.
        theme = settings.config['icon-theme'] or QtGui.QIcon.themeName()
        args = (cmdline, self.icon_size, theme)
        icon_path = icongetter.get_iconpath_for_commandline(*args)
        if icon_path is None:
            # TODO: Use fallback instead of empty icon
            icon = QtGui.QIcon()
        else:
            icon = QtGui.QIcon(icon_path)
        self.icon = icon

class LaunchWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QHBoxLayout()
        self.icon_label = CommandIconLabel()
        layout.addWidget(self.icon_label)
        self.edit = LaunchEdit()
        update_icon = self.icon_label.set_icon_by_command
        self.edit.textChanged.connect(update_icon)
        layout.addWidget(self.edit)
        self.setLayout(layout)
        # Doing this will update the icon for empty state
        self.update()

    def update(self, fragment=None):
        text = self.edit.text()
        if fragment is None or fragment == text:
            self.edit.textChanged.emit(text)
        else:
            self.edit.setText(fragment)

def run_app(args=[]):
    app = QtGui.QApplication(args)
    launcher = LaunchWidget()
    launcher.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(run_app(sys.argv))
