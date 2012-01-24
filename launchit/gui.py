#!/usr/bin/env python
"""
Graphical user-interface made with PySide.
"""
# NOTE: This file exceptionally follows Qt's naming conventions instead of
#       PEP-8 in order to avoid a mixing of those two naming schemes.

# Stdlib
import sys

# 3rd party
from PySide import QtCore, QtGui

# Launchit package
from . import core, icongetter, settings
from ._stringutils import altstring

class MarkedCompletionRenderer(QtGui.QTextDocument):
    """
    A rich text / HTML renderer that is specialized to create the markup 
    used to show a completion item with a marked fragment. Its contents 
    may be rendered by a painter.
    """
    def __init__(self, fragment='', startMark='<b><u>', 
                       endMark='</u></b>', parent=None):
        """
        Given `startMark` and `endMark` are intended to be used as tags in
        order to surround the current `fragment` inside a given completion. 
        The resulting markup is then interpreted as rich text, when rendering 
        is done. Note that the fragment does not need to be known on instance 
        creation-time, since it may be set/changed later by just accessing the 
        instance's `fragment`-attribute.
        """
        QtGui.QTextDocument.__init__(self, parent)
        self.fragment = fragment
        self.startMark = startMark
        self.endMark = endMark

    def _getMarkup(self, completion):
        """
        Return given `completion`-string, where each occurrence of the current 
        fragment is surrounded by marking tags.
        """
        return core.get_marked_completion(completion, self.fragment,
                                          self.startMark, self.endMark)

    def makeCompletionMarkup(self, text, maxWidth=None):
        """
        Generate markup for given `text` and set the result onto the renderer.
        If `maxWidth` is set to a pixel value and the rendered result would
        become larger than that width, the result is truncated by an ellipsis. 
        """
        markup = self._getMarkup(text)
        self.setHtml(markup)
        if maxWidth is not None:
            # Note that truncation can't be made with QFontMetrics.elidedText()
            # here, since that doesn't handle rich text. The trial and error
            # approach has been chosen in order to avoid messing with the
            # rendering engine. There probably should be no situation where
            # memory consumption of this method is really getting noticeable.
            ellipsis = '...'
            renderedWidth = self.idealWidth
            while text and (renderedWidth() > maxWidth):
                text = text[:-1]
                markup = self._getMarkup(text) + ellipsis
                self.setHtml(markup)

class MarkedCompletionDelegate(QtGui.QStyledItemDelegate):
    """
    An item delegate used to draw a completion with a marked fragment.
    """
    def __init__(self, renderer=None, parent=None):
        """
        Setup the delegate. `renderer` is expected to be a given as a
        `MarkedCompletionRenderer`-like instance. When `None` is used
        instead, such renderer-instance is created automatically.
        """
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.renderer = renderer or MarkedCompletionRenderer(parent=self)

    def updateFragment(self, fragment):
        """
        Update the fragment that is marked inside each completion with 
        new `fragment`.
        """
        self.renderer.fragment = fragment

    def paint(self, painter, option, index):
        """
        Render a marked completion item using the given `painter`. 

        Initially, the "framing" is done by painting the item without
        any contents. Therefore, `option` is used to determine the
        desired style for the item. `option` is expected to be given
        as a `QStyleOptionViewItem`-instance.

        After that, the contents to fill the item are retrieved from
        the given `index`, passed to the delegate's renderer in order
        mark the completion's fragment and finally drawn inside the 
        "empty" item.

        Note that this reimplemented method is usually invoked by Qt
        on its own. Users normally do not need to call it explicitly.
        """
        self.drawItem(painter, option) # => empty item
        indexOption = self.getOptionForIndex(option, index)
        self.drawMarkedContents(painter, indexOption)

    def drawItem(self, painter, option):
        """
        Draw an item for the view using `painter` based on the values of
        given `option`. If `option` supports a `widget`-member, then that
        widget's style is used, otherwise the application's style is used.
        Note that this method is not able to interpret fomatting tags.
        """
        widget = getattr(option, 'widget', None)
        style = widget.style() if widget else QtGui.QApplication.style()
        style.drawControl(style.CE_ItemViewItem, option, painter, widget)

    def getOptionForIndex(self, option, index):
        """
        Use a new `QStyleOptionViewItemV4`-instance for given `option`,
        fill in the values for each role based on `index` and return it.
        """
        new_option = QtGui.QStyleOptionViewItemV4(option)
        self.initStyleOption(new_option, index)
        return new_option

    def drawMarkedContents(self, painter, option):
        """
        Draw the completion item's text using `painter`. Each occurrence of
        the current fragment will appear as marked. `option` is expected to 
        include the same information (especially about positioning) that has
        already been used to draw the item's framing.
        """
        # Note that this is more or less a hack in order to override Qt's
        # usual text rendering behavior, which seems not to be able to 
        # interpret rich text formatting tags in a view. For that part, a 
        # customized renderer must take the job. Unfortunately, it does not 
        # cover every detail of Qt's text attribute handling (e.g. direction 
        # or alignment). Therefore, it may come to somewhat odd  behavior in 
        # special cases.
        self.setupMarkup(option.text, option.rect.width())
        self.drawMarkup(painter, option.rect.topLeft())

    def setupMarkup(self, text, maxWidth=None):
        """
        Set appropriated markup for given completion `text` onto the renderer. 
        Note that `maxWidth` can be used (with a pixel value) to let the text
        be truncated if it doesn't fit into the item.
        """
        self.renderer.makeCompletionMarkup(text, maxWidth)

    def drawMarkup(self, painter, startPos):
        """
        Draw the renderer's markup with `painter`. Note that painting 
        is done relative to `startPos`.
        """
        painter.save()
        painter.translate(startPos)
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
    fragmentUpdated = QtCore.Signal([str], [altstring])

    def __init__(self, completiongetter, markFragment=True, parent=None):
        """
        Setup the completer. 

        `completiongetter` should be a callable that takes a string as an 
        argument for a given fragment. Its return value should be a list 
        of possible completions based on that fragment.

        `markFragment` is used to determine, whether the current fragment 
        should appear as marked inside each completion item. When this is 
        `True`, the item delegate of the completer's popup is replaced with 
        `MarkedCompletionDelegate`.
        """
        QtGui.QCompleter.__init__(self, parent)
        mode = self.UnfilteredPopupCompletion
        self.setCompletionMode(mode)
        model = QtGui.QStringListModel(parent=self)
        self.setModel(model)
        self.completiongetter = completiongetter
        if markFragment:
            self.delegate = MarkedCompletionDelegate()

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
        has an `updateFragment`-method, it is connected to the completer's
        `fragmentUpdated`-signal. Note that the popup will take ownership
        of the delegate.
        """
        if hasattr(delegate, 'updateFragment'):
            self.fragmentUpdated.connect(delegate.updateFragment)
        delegate.setParent(self.popup())
        self.popup().setItemDelegate(delegate)

    def update(self, fragment):
        """
        Update the list of possible completions based on `fragment` and 
        emit a `fragmentUpdated`-signal, using the new fragment as the 
        signal's argument.
        """
        completions = self.completiongetter(fragment)
        self.model().setStringList(completions)
        self.fragmentUpdated.emit(fragment)

class LaunchEdit(QtGui.QLineEdit):
    """
    An editable text field, into which the user may type a command.
    """
    def __init__(self, launcher=None, parent=None):
        """
        Setup the text field. Possible completions will appear as soon as 
        the user starts typing. Pressing the return key will invoke the 
        command.

        Note that `launcher` is expected to be a callable that takes the 
        command to launch as a string. The way how the given command will 
        be invoked is up to that callable.
        """
        QtGui.QLineEdit.__init__(self, parent)
        completer = CommandlineCompleter(
            core.get_name_completions, parent=self)
        self.textEdited.connect(completer.update)
        self.setCompleter(completer)
        self.launcher = launcher
        self.returnPressed.connect(self.launch)

    def launch(self):
        """
        Launch the contents of the text field.
        """
        self.launcher(self.text())

class Icon(QtGui.QIcon):
    """
    A class to represent an icon.
    """
    def __init__(self, icon):
        """
        Setup an instance for the given `icon`, which may either be a 
        string containing the path to the icon or an instance of `QIcon`, 
        `QPixmap` or `QIconEngine`.
        """
        QtGui.QIcon.__init__(self, icon)
        self._theme_icon_name = None

    @classmethod
    def fromCommand(cls, command):
        """
        Return a new instance of this class holding an appropriated 
        icon for the given `command`.
        """
        iconName = icongetter.guess_icon_name(command)
        return cls.fromTheme(iconName)

    @classmethod
    def fromTheme(cls, name, fallback=QtGui.QIcon()):
        """
        Look for icon with given `name` inside the current icon theme 
        and return it in a new instance of this class. If no suitable 
        icon was found, then the instance is based on `fallback`.
        """
        icon = cls(icongetter.get_icon_path(name, theme=cls.themeName()))
        if icon.isNull():
            icon = cls(fallback)
        else:
            # Quick hack to convert the icon name into Pyside's 
            # string-type afterwards (for the sake of consistency).
            _str = type(QtGui.QIcon.name(icon))
            # Use own attribute here, since setting an icon name
            # with "knowledge" of Qt seems not to be trivial.
            icon._theme_icon_name = _str(name)
        return icon

    def name(self):
        """
        Return the name used to create the icon. Note that this is usually
        only relevant when the instance was created by `.fromTheme()`. If
        no (theme) icon name was set, an empty string will be returned.
        """
        return self._theme_icon_name or QtGui.QIcon.name(self)

class CommandIconLabel(QtGui.QLabel):
    """
    A label, which holds an icon to represent a command.
    """
    def __init__(self, iconName=None, maxIconSize=32, 
                       iconTheme=None, parent=None):
        """
        Setup the icon label.

        On startup an icon with the given `iconName` is retrieved from 
        the current icon theme and initially set to the label. If that 
        name is `None`, then `icongetter.ICON_RUN` is used instead.

        The maximal size, that an icon may become for that label, is 
        defined by the given `maxIconSize`. 

        Note that the current icon theme is determined by Qt. In order
        to change that icon theme, a new theme name may be passed as 
        `iconTheme`. This might be helpful, since Qt is making wrong 
        assumptions about that theme on some desktop environments.
        """
        QtGui.QLabel.__init__(self, parent)
        self.maxIconSize = maxIconSize
        if iconTheme:
            Icon.setThemeName(iconTheme)
        self.icon = Icon.fromTheme(iconName or icongetter.ICON_RUN)

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
        which should a `QIcon`- or `Icon`-like instance.
        """
        maxWidth = maxHeight = self.maxIconSize
        pixmap = icon.pixmap(maxWidth, maxHeight)
        self.setPixmap(pixmap)
        self._icon = icon

    def update(self, command):
        """
        Update the icon inside the label based on given `command`. 
        If the command consists of multiple arguments, only its 
        first argument is used for determination.
        """
        self.icon = Icon.fromCommand(command)

class LaunchWidget(QtGui.QWidget):
    """
    Provides an editable text field, into which a command may be typed 
    in. In addition, an icon suitable for that command will be shown 
    beside the text field.
    """
    def __init__(self, iconTheme=None, parent=None):
        """
        Setup the widget. When the user starts typing, a popup is shown
        to suggest possible completions. If a command is recognized, an
        appropriated icon is shown (retrieved from the current icon theme). 

        To explicitly set a custom theme name as the current icon theme, 
        `iconName` may be used. If this is `None`, then the configuration 
        dictionary's value for `icon-theme` is used instead (if any).
        """
        QtGui.QWidget.__init__(self, parent)
        theme = iconTheme or settings.config['icon-theme']
        self.iconLabel = CommandIconLabel(iconTheme=theme, parent=self)
        self.edit = LaunchEdit(core.launch, parent=self)
        self.edit.textChanged.connect(self.iconLabel.update)
        self._makeLayout([self.iconLabel, self.edit])

    def _makeLayout(self, widgets):
        """
        Create a horizontal layout and fill it with `widgets` with respect 
        to the order in which the widgets are given. Finally set the layout 
        to the `LaunchWidget`.
        """
        layout = QtGui.QHBoxLayout(self)
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)

def runApp(args=[], title='Launchit'):
    """
    Run the application based on `args`. The `LaunchWidget` will appear 
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
    sys.exit(runApp(sys.argv))

if __name__ == '__main__':
    main()
