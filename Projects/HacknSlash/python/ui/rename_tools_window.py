# Imports
# from PySide2 import QtCore, QtWidgets, QtGui
from Interop.pyside.core.qt import QtCore, QtWidgets, QtGui, loadUiType
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import os
import logging
import pymel.core as pymel

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Load UI File
ui_path = ui_file_name = os.path.dirname(__file__) + r'\rename_tools.ui'
FormClass, BaseClass = loadUiType(ui_file_name)

mode = None


class RenameToolsWindow(QtWidgets.QMainWindow, FormClass):
    def __init__(self):
        maya_main = None
        try:
            maya_main = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)  # GET MAIN MAYA WINDOW
        except:
            pass
        super(RenameToolsWindow, self).__init__(maya_main)  # PARENT WINDOW
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)  # DELETE WINDOW ON CLOSE
        self.setupUi(self)

        self.cbx_strip_letters.hide()
        self.lbl_strip_letters.hide()
        self.btn_execute.setText('Replace')

    def reset_ui(self):
        pass

    # @QtCore.Slot(): Decorator based on widget name that connects QT signal.
    @QtCore.Slot()
    def on_cb_mode_currentIndexChanged(self):
        # Replace
        if self.cb_mode.currentText() == 'Replace':
            self.cbx_strip_letters.hide()
            self.lbl_strip_letters.hide()
            self.ln_find.show()
            self.lbl_find.show()
            self.ln_replace.show()
            self.lbl_replace.show()
            self.lbl_replace.setText('Replace')
            self.btn_execute.setText('Replace')

        #  Rename
        if self.cb_mode.currentText() == 'Rename':
            self.cbx_strip_letters.hide()
            self.lbl_strip_letters.hide()
            self.ln_find.hide()
            self.lbl_find.hide()
            self.ln_replace.show()
            self.lbl_replace.show()
            self.lbl_replace.setText('Rename')
            self.btn_execute.setText('Rename')

        #  Add Prefix
        if self.cb_mode.currentText() == 'Add Prefix':
            self.cbx_strip_letters.hide()
            self.lbl_strip_letters.hide()
            self.ln_find.hide()
            self.lbl_find.hide()
            self.ln_replace.show()
            self.lbl_replace.show()
            self.lbl_replace.setText('Prefix')
            self.btn_execute.setText('Add Prefix')

        #  Add Suffix
        if self.cb_mode.currentText() == 'Add Suffix':
            self.cbx_strip_letters.hide()
            self.lbl_strip_letters.hide()
            self.ln_find.hide()
            self.lbl_find.hide()
            self.ln_replace.show()
            self.lbl_replace.show()
            self.lbl_replace.setText('Suffix')
            self.btn_execute.setText('Add Suffix')

        #  Strip Start Letters
        if self.cb_mode.currentText() == 'Remove Start Letters' \
                or self.cb_mode.currentText() == 'Remove End Letters':
            self.cbx_strip_letters.show()
            self.lbl_strip_letters.show()
            self.ln_find.hide()
            self.lbl_find.hide()
            self.ln_replace.hide()
            self.lbl_replace.hide()
            self.btn_execute.setText('Remove Letters')

    @QtCore.Slot()
    def on_btn_execute_clicked(self):
        self.rename(selection=pymel.selected())

    @QtCore.Slot()
    def on_btn_cancel_clicked(self):
        log.info('on_btn_unlock_attr_clicked, CLICKED')
        print 'on_btn_canceled_clicked, clicked'
        self.close()

    def rename(self, selection=None):
        if self.cb_mode.currentText() == 'Replace':
            for item in selection:
                item.rename(item.name().replace(self.ln_find.text(), self.ln_replace.text()))

        if self.cb_mode.currentText() == 'Rename':
            for item in selection:
                item.rename(self.ln_replace.text())

        if self.cb_mode.currentText() == 'Add Prefix':
            for item in selection:
                item.rename(self.ln_replace.text() + item.name())

        if self.cb_mode.currentText() == 'Add Suffix':
            for item in selection:
                item.rename(item.name() + self.ln_replace.text())

        if self.cb_mode.currentText() == 'Remove Start Letters':
            print self.cbx_strip_letters.value()
            for item in selection:

                item.rename(item.name() + self.ln_replace.text())


def showUI():
    log.info(RenameToolsWindow.__name__)
    for widget in QtWidgets.QApplication.allWidgets():
        if type(widget).__name__ == RenameToolsWindow.__name__:
            try:
                widget.close()
            except:
                pass
    rename_tools_window = RenameToolsWindow()
    rename_tools_window.show()


# app = QtWidgets.QApplication([])
# win = RenameToolsWindow()
# win.show()
# app.exec_()


# C:\Program Files\Autodesk\Maya2017\bin\mayapy E:\Python_Projects\Projects\HacknSlash\python\ui\tools_window.py

# from Projects.HacknSlash.python.ui import rename_tools_window
# reload(rename_tools_window)
# win = rename_tools_window.ToolsWindow()
# win.show()
