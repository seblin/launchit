#!/usr/bin/env python
"""
Graphical user-interface made with PySide.
"""
# Stdlib
import sys

# 3rd party
from PySide import QtGui

# Launchit package
from . import core, icongetter, settings

class CompletionMarkupBuilder(object):
    """
    This class is responsible for the markup, which is used to show
    a completion item.
    """
    def __init__(self, start_mark='<b><u>', end_mark='</u></b>'):
        """
        The `start_mark` and `end_mark` tags are interpreted as rich text
        in order to mark a fragment inside a completion. `start_mark` will
        be placed before and `end_mark` will be placed after the fragment.
        """
        self.start_mark = start_mark
        self.end_mark = end_mark

    def get_elided_markup(self, text, fragment, width):
        """
        Return `text` with each occurrence of `fragment` surrounded by
        marking tags. Note that the result is truncated by an ellipsis, 
        if it doesn't fit into `width`, when rendered. Though, in the 
        end this function just returns the markup.
        """
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
        """
        Place `self.start_mark` and `self.end_mark` around each occurrence 
        of `fragment` inside `completion` and return the result.
        """
        return core.get_marked_completion(completion, fragment,
                                          self.start_mark, self.end_mark)

class MarkedCompletionDelegate(QtGui.QItemDelegate):
    """
    This class is intended to be used as an item delegate. It is able to 
    render and draw a completion with a marked fragment.
    """
    def __init__(self, markup_builder=CompletionMarkupBuilder(), parent=None):
        """
        A new instance will have its `fragment`-attribute initially set 
        to an empty string. That attribute is intended to be changed from 
        "outside", whenever an appropriated event occurs (e.g. user has 
        typed a new character to the commandline).

        The `markup_builder` will be used to generate the corresponding
        markup in order to render the completion entry. It is assumed to
        provide an interface similar to `CompletionMarkupBuilder()` (at
        least a `.get_elided_markup()`-method with the same signature).
        """
        QtGui.QItemDelegate.__init__(self, parent)
        self.markup_builder = markup_builder
        self._renderer = QtGui.QTextDocument()
        self.fragment = ''

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
        Let `self.markup_builder` generate the markup for the current 
        completion (retrieved via `index.data()`) in order to make any 
        occurrence of `self.fragment` appear inside marking tags. The
        result is then rendered and painted. In case that the rendered
        result is larger than the available width (which is taken from 
        `option.rect`), it will be truncated by an ellipsis.
        """
        markup = self.markup_builder.get_elided_markup(
            index.data(), self.fragment, option.rect.width())
        self.draw_markup(markup, painter, option.rect.topLeft())

    def draw_markup(self, markup, painter, start_pos):
        """
        Render `markup`, which is assumed to be given in Qt's rich text 
        format and draw it by using `painter`. Note that painting will 
        be done relative to `start_pos`.
        """
        self._renderer.setHtml(markup)
        painter.save()
        painter.translate(start_pos)
        self._renderer.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        """
        Reimplemented method, which returns the size of the rendered 
        entry. This is needed by Qt in order to know about how much
        space it should provide for the item, when its painting is 
        requested.
        """
        return self._renderer.size().toSize()

class CommandlineCompleter(QtGui.QCompleter):
    """
    This class provides and handles the popup, which shows the possible
    completions for a given fragment. It is used by `LaunchEdit()`.
    """
    def __init__(self, parent=None):
        """
        Setup the completer. `MarkedCompletionDelegate()` is used to show 
        an entry.
        """
        QtGui.QCompleter.__init__(self, parent)
        mode = self.UnfilteredPopupCompletion
        self.setCompletionMode(mode)
        model = QtGui.QStringListModel()
        self.setModel(model)
        delegate = MarkedCompletionDelegate()
        self.popup().setItemDelegate(delegate)

    def update(self, fragment):
        """
        Update the list of possible completions based on `fragment` and 
        inform the delegate that it has to mark a new fragment.
        """
        completions = core.get_name_completions(fragment)
        self.model().setStringList(completions)
        self.popup().itemDelegate().fragment = fragment

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
        completer = CommandlineCompleter()
        self.textEdited.connect(completer.update)
        self.setCompleter(completer)
        self.returnPressed.connect(self.launch)

    def launch(self):
        """
        Launch the contents of the text field.
        """
        core.launch(self.text())

class Icon(QtGui.QIcon):
    """
    This class is intended for scalable icons.
    """
    def __init__(self, source_or_engine=None):
        """
        Takes `source_or_engine` to determine the icon to use. If
        this is `None`, then initialization is made without an icon.
        Otherwise the argument may be an icon path given as a string, 
        a `QIcon()`-like class, a `QPixmap()` or a `QIconEngine()`.
        """
        if not source_or_engine:
            QtGui.QIcon.__init__(self)
        else:
            QtGui.QIcon.__init__(self, source_or_engine)

class CommandIconLabel(QtGui.QLabel):
    """
    A label, which holds an icon to represent a command.
    """
    def __init__(self, icon_size=32, icon=Icon(), parent=None):
        """
        Takes `icon_size`, which should hold the size to use as an 
        integer and an `Icon()` or a `QIcon()`-like class in order 
        to determine the icon, which should appear inside the label.
        """
        QtGui.QLabel.__init__(self, parent)
        self.icon_size = icon_size
        self.icon = icon

    @property
    def icon(self):
        """
        Return the icon, which the label currently uses.
        """
        return self._icon

    @icon.setter
    def icon(self, icon):
        """
        Replace the old icon inside the label with new `icon`.
        """
        width = height = self.icon_size
        pixmap = icon.pixmap(width, height)
        self.setPixmap(pixmap)
        self._icon = icon

    def set_icon_by_command(self, cmdline):
        """
        Show an icon corresponding to `cmdline`s first argument.
        """
        # TODO: Implement theme detection for XFCE and LXDE, since these
        #       are not supported by Qt's theme detection. Currently the
        #       user must manually set the theme name inside launchit's
        #       configuration file, if using an unsupported environment.
        theme = settings.config['icon-theme'] or QtGui.QIcon.themeName()
        args = (cmdline, self.icon_size, theme)
        icon_path = icongetter.get_iconpath_for_commandline(*args)
        self.icon = Icon(icon_path)

class LaunchWidget(QtGui.QWidget):
    """
    Provides an editable text field, where a command may be typed in.
    In addition, an icon suitable for that command will be shown beside
    the text field.
    """
    def __init__(self, parent=None):
        """
        Setup the widget. When the user starts typing, a popup is shown
        to suggest possible completions. If a command is recognized, an
        appropriated icon is shown.
        """
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
        """
        Update the widget based on `fragment`. This is simply done by
        emitting an appropriated signal with the new fragment as an
        argument in order to let the other parts know about the change.
        If `fragment` is `None`, then the current contents of the text
        field are used as the fragment.
        """
        text = self.edit.text()
        if fragment is None or fragment == text:
            self.edit.textChanged.emit(text)
        else:
            self.edit.setText(fragment)

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
