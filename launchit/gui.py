# Stdlib
import sys
# 3rd party
from PySide import QtGui
# launchit package
from . import core

class CmdlineCompleter(QtGui.QCompleter):
    def __init__(self, parent=None):
        QtGui.QCompleter.__init__(self, parent)
        mode = self.UnfilteredPopupCompletion
        self.setCompletionMode(mode)
        model = QtGui.QStringListModel()
        self.setModel(model)

    def update(self, fragment):
        completions = core.get_name_completions(fragment)
        self.model().setStringList(completions)

class LaunchEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        completer = CmdlineCompleter()
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
