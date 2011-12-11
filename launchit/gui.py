#!/usr/bin/env python
"""
Graphical user-interface made with PySide.
"""
# Stdlib
import sys

# 3rd party
from PySide import QtCore, QtGui

# Launchit package
from . import core, icongetter, settings
from ._stringutils import altstring, basestring

class MarkedCompletionRenderer(QtGui.QTextDocument):
    """
    A rich text / HTML renderer that is specialized to create the markup 
    used to show a completion item with a marked fragment. Its contents 
    may be rendered by a painter.
    """
    def __init__(self, fragment='', start_mark='<b><u>', 
                       end_mark='</u></b>', parent=None):
        """
        Given `start_mark` and `end_mark` are intended to be used as tags in
        order to surround the current `fragment` inside a given completion. 
        The resulting markup is then interpreted as rich text, when rendering 
        is done. Note that the fragment does not need to be known on instance 
        creation-time, since it may be set/changed later by just accessing the 
        instance's `fragment`-attribute.
        """
        QtGui.QTextDocument.__init__(self, parent)
        self.fragment = fragment
        self.start_mark = start_mark
        self.end_mark = end_mark

    def _get_markup(self, completion):
        """
        Return given `completion`-string, where each occurrence of the current 
        fragment is surrounded by marking tags.
        """
        return core.get_marked_completion(completion, self.fragment,
                                          self.start_mark, self.end_mark)

    def make_completion_markup(self, text, max_width=None):
        """
        Generate markup for given `text` and set the result onto the renderer.
        If `max_width` is set to a pixel value and the rendered result would
        become larger than that width, the result is truncated by an ellipsis. 
        """
        markup = self._get_markup(text)
        self.setHtml(markup)
        if max_width is not None:
            # Note that truncation can't be made with QFontMetrics.elidedText()
            # here, since that doesn't handle rich text. The trial and error
            # approach has been chosen in order to avoid messing with the
            # rendering engine. There probably should be no situation where
            # memory consumption of this method is really getting noticeable.
            rendered_width = self.idealWidth
            while text and (rendered_width() > max_width):
                text = text[:-1]
                markup = self._get_markup(text) + '...'
                self.setHtml(markup)

class MarkedCompletionDelegate(QtGui.QItemDelegate):
    """
    An item delegate used to draw a completion with a marked fragment.
    """
    def __init__(self, renderer=None, parent=None):
        """
        Setup the delegate. `renderer` is expected to be a given as a
        `MarkedCompletionRenderer()`-like instance. When `None` is used
        instead, such renderer-instance is created automatically.
        """
        QtGui.QItemDelegate.__init__(self, parent)
        self.renderer = renderer or MarkedCompletionRenderer(parent=self)

    def update_fragment(self, fragment):
        """
        Update the fragment that is marked inside each completion with 
        new `fragment`.
        """
        self.renderer.fragment = fragment

    def paint(self, painter, option, index):
        """
        Reimplemented method to draw a completion entry. This makes use
        of Qt's model/view framework. Note that there usually is no need 
        to call this method directly, since Qt already does this for us.
        """
        self.drawBackground(painter, option, index)
        self.draw_contents(painter, option, index)

    def draw_contents(self, painter, option, index):
        """
        Let the renderer generate the markup for the current completion
        string. That string is retrieved by a call to `index.data()`.
        The result is then rendered and painted.
        """
        self.renderer.make_completion_markup(index.data(), option.rect.width())
        self.draw_markup(painter, option.rect.topLeft())

    def draw_markup(self, painter, start_pos):
        """
        Draw the renderer's markup with `painter`. Note that painting 
        is done relative to `start_pos`.
        """
        painter.save()
        painter.translate(start_pos)
        self.renderer.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        """
        Reimplemented method, which returns the size of the rendered 
        entry. This is needed by Qt in order to know about how much
        space it should provide for the item, when its painting is 
        requested.
        """
        return self.renderer.size().toSize()

class CommandlineCompleter(QtGui.QCompleter):
    """
    This class may be used to provide a popup in order to show possible
    completions for a given fragment.
    """
    fragment_updated = QtCore.Signal([str], [altstring])

    def __init__(self, parent=None):
        """
        Setup the completer.
        """
        QtGui.QCompleter.__init__(self, parent)
        mode = self.UnfilteredPopupCompletion
        self.setCompletionMode(mode)
        model = QtGui.QStringListModel(parent=self)
        self.setModel(model)

    @property
    def delegate(self):
        """
        Return the item delegate that is set on the completer's popup.
        """
        return self.popup().itemDelegate()

    @delegate.setter
    def delegate(self, delegate):
        """
        Set given item delegate on the completer's popup. If `delegate` 
        has an `update_fragment`-method, it is connected to the completer's
        `fragment_updated`-signal. Note that the popup will take ownership
        of the delegate.
        """
        if hasattr(delegate, 'update_fragment'):
            self.fragment_updated.connect(delegate.update_fragment)
        delegate.setParent(self.popup())
        self.popup().setItemDelegate(delegate)

    def update(self, fragment):
        """
        Update the list of possible completions based on `fragment` and 
        emit a `fragment_updated`-signal, using the new fragment as the 
        signal's argument.
        """
        completions = core.get_name_completions(fragment)
        self.model().setStringList(completions)
        self.fragment_updated.emit(fragment)

class LaunchEdit(QtGui.QLineEdit):
    """
    An editable text field, into which the user may type a command.
    """
    def __init__(self, parent=None):
        """
        Setup the text field. Possible completions will appear as 
        soon as the user starts typing. Pressing the return key 
        will invoke the command.
        """
        QtGui.QLineEdit.__init__(self, parent)
        completer = CommandlineCompleter(parent=self)
        self.textEdited.connect(completer.update)
        completer.delegate = MarkedCompletionDelegate()
        self.setCompleter(completer)
        self.returnPressed.connect(self.launch)

    def launch(self):
        """
        Launch the contents of the text field.
        """
        core.launch(self.text())

class CommandIconLabel(QtGui.QLabel):
    """
    A label, which holds an icon to represent a command.
    """
    def __init__(self, icon_size=32, parent=None):
        """
        Takes `icon_size`, which should be an integer to define the
        maximal size of an icon inside the label.
        """
        QtGui.QLabel.__init__(self, parent)
        self.icon_size = icon_size
        self._icon = QtGui.QIcon(parent=self)

    @property
    def icon(self):
        """
        Return the icon, which the label currently uses.
        """
        return self._icon

    @icon.setter
    def icon(self, icon):
        """
        Replace the old icon inside the label with new `icon`,
        which should be an instance of `QIcon()`.
        """
        width = height = self.icon_size
        pixmap = icon.pixmap(width, height)
        self.setPixmap(pixmap)
        self._icon = icon

    def update_icon(self, path):
        """
        Update the icon inside the label based on `path`. Note that
        `path` should refer to an existing icon file. If it is `None`,
        then an empty icon is set on the label.
        """
        if path is None:
            icon = QtGui.QIcon(parent=self)
        else:
            icon = QtGui.QIcon(path, parent=self)
        self.icon = icon

    @property
    def theme_name(self):
        """
        Return the theme name, which is used to retrieve an icon.
        """
        return settings.config['icon-theme'] or QtGui.QIcon.themeName()

    def set_icon_by_command(self, cmdline):
        """
        Let the label show an icon corresponding to `cmdline`s first argument.
        """
        args = (cmdline, self.icon_size, self.theme_name)
        icon_path = icongetter.get_iconpath_for_commandline(*args)
        self.update_icon(icon_path)

class LaunchWidget(QtGui.QWidget):
    """
    Provides an editable text field, into which a command may be typed 
    in. In addition, an icon suitable for that command will be shown 
    beside the text field.
    """
    def __init__(self, parent=None):
        """
        Setup the widget. When the user starts typing, a popup is shown
        to suggest possible completions. If a command is recognized, an
        appropriated icon is shown.
        """
        QtGui.QWidget.__init__(self, parent)
        self.icon_label = CommandIconLabel(parent=self)
        update_icon = self.icon_label.set_icon_by_command
        self.edit = LaunchEdit(parent=self)
        self.edit.textChanged.connect(update_icon)
        self._make_layout([self.icon_label, self.edit])
        update_icon(self.edit.text())

    def _make_layout(self, widgets):
        """
        Create a horizontal layout and fill it with `widgets` with respect 
        to the order in which the widgets are given. Finally set the layout 
        to the `LaunchWidget()`.
        """
        layout = QtGui.QHBoxLayout(self)
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)

def run_app(args=[], title='Launchit'):
    """
    Run the application based on `args`. The `LaunchWidget()` will appear 
    inside a window. That window will make use of `title` as the caption 
    for its title bar. The applications's exit code will be returned after 
    execution.
    """
    app = QtGui.QApplication(args)
    launcher = LaunchWidget()
    launcher.setWindowTitle(title)
    launcher.show()
    return app.exec_()

def main():
    """
    This function is intended to be used as an entry point, when Launchit 
    was invoked from the commandline. It will run the GUI with respect to 
    the commandline's arguments. When the GUI was exited, it will also exit
    the interpreter using the application's return value as the exit code. 
    """
    sys.exit(run_app(sys.argv))

if __name__ == '__main__':
    main()
