#!/usr/bin/env python
# Stdlib
import sys

# 3rd party
from PySide import QtGui

# launchit package
from . import core, icongetter, settings

class CompletionMarkupBuilder(object):
    def __init__(self, start_mark='<b><u>', end_mark='</u></b>'):
        self.start_mark = start_mark
        self.end_mark = end_mark

    def get_elided_markup(self, text, fragment, width):
        # Note that truncation can't be made with QFontMetrics.elidedText()
        # here, since that doesn't handle rich text. The trial and error
        # approach has been chosen in order to avoid messing with the
        # rendering engine. There probably should be no situation where
        # memory consumption of this method is really getting noticeable.
        markup = self.get_completion_markup(text, fragment)
        temporary_renderer = QtGui.QTextDocument()
        temporary_renderer.setHtml(markup)
        rendered_width = temporary_renderer.idealWidth
        ellipsis = '...'
        while text and (rendered_width() > width):
            text = text[:-1]
            markup = self.get_completion_markup(text, fragment) + ellipsis
            temporary_renderer.setHtml(markup)
        return markup

    def get_completion_markup(self, completion, fragment):
        return core.get_marked_completion(completion, fragment,
                                          self.start_mark, self.end_mark)

class MarkedCompletionDelegate(QtGui.QItemDelegate):
    def __init__(self, markup_builder=CompletionMarkupBuilder(), parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.markup_builder = markup_builder
        self._renderer = QtGui.QTextDocument()
        self.fragment = ''

    def paint(self, painter, option, index):
        self.drawBackground(painter, option, index)
        self.draw_contents(painter, option, index)

    def draw_contents(self, painter, option, index):
        markup = self.markup_builder.get_elided_markup(
            index.data(), self.fragment, option.rect.width())
        self.draw_markup(markup, painter, option.rect.topLeft())

    def draw_markup(self, markup, painter, start_pos):
        self._renderer.setHtml(markup)
        painter.save()
        painter.translate(start_pos)
        self._renderer.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        return self._renderer.size().toSize()

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

class Icon(QtGui.QIcon):
    def __init__(self, source_or_engine=None):
        if not source_or_engine:
            QtGui.QIcon.__init__(self)
        else:
            QtGui.QIcon.__init__(self, source_or_engine)

class CommandIconLabel(QtGui.QLabel):
    def __init__(self, icon_size=32, icon=Icon(), parent=None):
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
        self.icon = Icon(icon_path)

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

def run_app(args=[], title='Launchit'):
    app = QtGui.QApplication(args)
    launcher = LaunchWidget()
    launcher.setWindowTitle(title)
    launcher.show()
    return app.exec_()

def main():
    sys.exit(run_app(sys.argv))

if __name__ == '__main__':
    main()
