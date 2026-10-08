import adentk.maya.prop_rig_toolkit.controls as controls
import adentk.maya.prop_rig_toolkit.rigging as rigging
import maya.OpenMayaUI as omui
from PySide6 import QtWidgets, QtGui, QtCore
from shiboken6 import wrapInstance
import os
import logging

# Shim: PyMEL calls logging._acquireLock, which Python 3.13 removed. Must run before importing pymel.
if not hasattr(logging, '_acquireLock'):
    logging._acquireLock = lambda: logging._lock.acquire()
    logging._releaseLock = lambda: logging._lock.release()
import maya.cmds as cmds

DEV_ROOT = r"D:\_dev\adentk"
ICONS_DIR = os.path.join(DEV_ROOT, "maya", "icons")


def get_maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


class PropRiggingUI(QtWidgets.QDialog):
    WINDOW_TITLE = "Automatic Prop Rigger"
    OBJECT_NAME = "AutomaticPropRigger"

    def __init__(self, parent=None):
        if parent is None:
            parent = get_maya_main_window()
        super().__init__(parent)

        self.setStyleSheet("""

            QPushButton {
                background-color: none;
                font-weight: bold;
                color: white;
            }
            QLabel {
                padding: 2px;
                margin: 0px;
                qproperty-alignment: AlignCenter;
                font-weight: bold;
                font-size: 14px;
                color: white;
                background-color: #333;
            }
        """)

        self.ControlUtils = controls.BSControlsUtils()
        self.Rigging = rigging.RiggingToolkit()

        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(300, 600)

        box_layout = QtWidgets.QVBoxLayout(self)
        box_layout.setContentsMargins(10, 10, 10, 10)
        box_layout.setSpacing(6)

        # ------------ CONTROL SHAPES ------------------
        ctrl_shapes_label = QtWidgets.QLabel(text="Control Shapes")
        ctrl_shapes_grid = QtWidgets.QGridLayout()
        ctrl_shapes_grid.setSpacing(4)
        box_layout.addWidget(ctrl_shapes_label)
        box_layout.addLayout(ctrl_shapes_grid)

        buttons_data = [
            ("btn_circle", "Circle", "circle.png"),
            ("btn_square", "Square", "square.png"),
            ("btn_triangle", "Triangle", "triangle.png"),
            ("btn_sphere", "Sphere", "sphere.png"),
            ("btn_cube", "Cube", "Box.png"),
            ("btn_pyramid", "Pyramid", "pyramid.png"),
            ("btn_diamond", "Diamond", "diamond.png"),
            ("btn_circle_pin", "Circle Pin", "circle_pin.png"),
            ("btn_circle_dumbbell", "Circle Dumbbell", "circle_dumbbell.png"),
            ("btn_four_arrows", "Four Arrows", "four_arrows.png"),
            ("btn_curved_four_arrows", "Curved Four Arrows", "curved_four_arrows.png"),
            ("btn_two_arrows", "Two Arrows", "two_arrows.png"),
            ("btn_curved_two_arrows", "Curved Two Arrows", "curved_two_arrows.png"),
            ("btn_circle_one_arrow", "Circle One Arrow", "circle_one_arrow.png"),
            ("btn_circle_two_arrows", "Circle Two Arrows", "circle_two_arrows.png"),
            ("btn_circle_four_arrows", "Circle Four Arrows", "circle_four_arrows.png"),
            ("btn_gear", "Gear", "gear.png"),
        ]

        columns = 4
        for i, (attr_name, label, icon_filename) in enumerate(buttons_data):
            btn = QtWidgets.QPushButton()
            btn.setToolTip(label)
            btn.setIconSize(QtCore.QSize(60, 60))
            btn.setMaximumSize(70, 70)
            # Resolve full absolute path to icon
            icon_path = os.path.join(ICONS_DIR, icon_filename)
            btn.setIcon(QtGui.QIcon(icon_path))

            btn.clicked.connect(lambda checked=False, s=label, b=btn: self.on_select_shape(shape=s, clicked_btn=b))
            setattr(self, attr_name, btn)

            row = i // columns
            col = i % columns
            ctrl_shapes_grid.addWidget(btn, row, col)

        # Default selected shape is Circle
        self.selected_shape = "Circle"
        self.selected_shape_btn = self.btn_circle
        self.selected_shape_btn.setStyleSheet("background-color: red")

        # ------------ RIGGING OPTIONS ------------------
        rig_options_label = QtWidgets.QLabel(text="Rig Options")
        rig_options_box = QtWidgets.QHBoxLayout()
        box_layout.addWidget(rig_options_label)
        box_layout.addLayout(rig_options_box)

        self.fullRigBtn = QtWidgets.QPushButton("Full Rig")
        self.jointsOnlyBtn = QtWidgets.QPushButton("Joints Only")
        self.ctrlsOnlyBtn = QtWidgets.QPushButton("Controls Only")
        rig_options_box.addWidget(self.fullRigBtn)
        rig_options_box.addWidget(self.jointsOnlyBtn)
        rig_options_box.addWidget(self.ctrlsOnlyBtn)

        self.fullRigBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Full Rig"))
        self.jointsOnlyBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Joints Only"))
        self.ctrlsOnlyBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Controls Only"))
        box_layout.addStretch()

    def on_select_shape(self, shape: str, clicked_btn: QtWidgets.QPushButton):
        # toggle active/inactive button colors
        self.selected_shape_btn.setStyleSheet("background-color: none")
        clicked_btn.setStyleSheet("background-color: red")

        self.selected_shape_btn = clicked_btn
        self.selected_shape = shape

        selection = cmds.ls(sl=True, l=True)

        if selection:
            for objs in selection:
                # Getting and checking node type to act on shape level
                nType = cmds.nodeType(objs)

                if nType == 'transform':
                    objs = cmds.listRelatives(objs, s=True)
                elif nType == 'shape':
                    pass
                else:
                    cmds.error('Selected object(s) is not a nurbs curve.')

                print(objs)


def show_ui():
    maya_window = get_maya_main_window()
    existing_window = maya_window.findChild(QtWidgets.QDialog, PropRiggingUI.OBJECT_NAME)
    if existing_window:
        existing_window.close()
        existing_window.deleteLater()

    qt_window = PropRiggingUI()
    qt_window.show()

    return qt_window


show_ui()