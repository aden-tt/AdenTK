import adentk.maya.prop_rig_toolkit.controls as controls
import adentk.maya.prop_rig_toolkit.rigging as rigging
import maya.OpenMayaUI as omui
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Signal
from shiboken6 import wrapInstance
import os
import maya.cmds as cmds

DEV_ROOT = r"D:\_dev\adentk"
ICONS_DIR = os.path.join(DEV_ROOT, "maya", "icons")


def get_maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


def create_color_display(slider: QtWidgets.QSlider) -> QtWidgets.QPushButton:
    color_display = QtWidgets.QPushButton();
    color_display.setEnabled(False)
    color_display.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def update_color(value: int) -> None:
        color = QtGui.QColor.fromHsv(value, 255, 255)
        color_display.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #555;"
        )

    slider.valueChanged.connect(update_color)
    update_color(slider.value())
    return color_display


def create_size_slider() -> tuple[QtWidgets.QSlider, QtWidgets.QLineEdit]:
    MIN_VAL = 0.1
    MAX_VAL = 20.0
    STEP = 0.1
    SCALE = int(1 / STEP)  # Multiplier factor (10 for 1 decimal place)

    validator = QtGui.QDoubleValidator(MIN_VAL, MAX_VAL, 1)
    validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)

    field = QtWidgets.QLineEdit()
    field.setValidator(validator)
    field.setText(f"{1.0:.1f}")

    slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    slider.setRange(int(MIN_VAL * SCALE), int(MAX_VAL * SCALE))
    slider.setValue(int(1.0 * SCALE))

    def update_field(value: int) -> None:
        float_val = value / SCALE
        field.blockSignals(True)
        field.setText(f"{float_val:.1f}")
        field.blockSignals(False)

    slider.valueChanged.connect(update_field)

    def update_slider(text: str) -> None:
        if text and text != ".":
            try:
                val = float(text)
                if MIN_VAL <= val <= MAX_VAL:
                    slider.blockSignals(True)
                    slider.setValue(int(val * SCALE))
                    slider.blockSignals(False)
            except ValueError:
                pass

    field.textChanged.connect(update_slider)
    return [slider, field]


class PropRiggingUI(QtWidgets.QDialog):
    WINDOW_TITLE = "Automatic Prop Rigger"
    OBJECT_NAME = "AutomaticPropRigger"

    def __init__(self, parent=None):
        if parent is None:
            parent = get_maya_main_window()
        super().__init__(parent)

        self.setStyleSheet("""
            QCheckBox{
                color: white;
            }
            QPushButton {
                background-color: none;
                font-weight: bold;
                color: white;
            }
            QLabel{
                font-weight: bold;
                color: white;
            }
            QLabel[header="true"] {
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

        # ------------ CONTROL OPTIONS ------------------
        ctrl_options_label = QtWidgets.QLabel(text="Control Options")
        ctrl_options_label.setProperty("header", "true")
        ctrl_options_grid = QtWidgets.QGridLayout()

        ctrl_size_label = QtWidgets.QLabel("Control size:")
        ctrl_color_label = QtWidgets.QLabel("Control color:")

        self.ctrl_size_slider, self.ctrl_size_field = create_size_slider()

        self.ctrl_color_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.ctrl_color_slider.setRange(0, 255)
        self.ctrl_color_button = create_color_display(self.ctrl_color_slider)

        ctrl_options_grid.addWidget(ctrl_size_label, 0, 0)
        ctrl_options_grid.addWidget(self.ctrl_size_field, 0, 1)
        ctrl_options_grid.addWidget(self.ctrl_size_slider, 0, 2)
        ctrl_options_grid.addWidget(ctrl_color_label, 1, 0)
        ctrl_options_grid.addWidget(self.ctrl_color_button, 1, 1)
        ctrl_options_grid.addWidget(self.ctrl_color_slider, 1, 2)

        self.ctrl_size_field.setMaximumWidth(50)
        self.ctrl_color_button.setMaximumWidth(50)
        ctrl_options_grid.setColumnStretch(0, 0)
        ctrl_options_grid.setColumnStretch(1, 0)
        ctrl_options_grid.setColumnStretch(2, 1)

        box_layout.addWidget(ctrl_options_label)
        box_layout.addLayout(ctrl_options_grid)

        # ------------ CONTROL SHAPES ------------------
        ctrl_shapes_label = QtWidgets.QLabel(text="Control Shapes")
        ctrl_shapes_label.setProperty("header", "true")
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
        rig_options_label.setProperty("header", "true")
        rig_options_box = QtWidgets.QVBoxLayout()
        box_layout.addWidget(rig_options_label)

        self.makeRootCB = QtWidgets.QCheckBox("Make Root Joint")
        self.makeRootCB.setChecked(True)
        box_layout.addWidget(self.makeRootCB)
        self.fullRigBtn = QtWidgets.QPushButton("Full Rig")
        self.jointsOnlyBtn = QtWidgets.QPushButton("Joints Only")
        self.ctrlsOnlyBtn = QtWidgets.QPushButton("Controls Only")
        rig_options_box.addWidget(self.fullRigBtn)
        rig_options_box.addWidget(self.jointsOnlyBtn)
        rig_options_box.addWidget(self.ctrlsOnlyBtn)
        box_layout.addLayout(rig_options_box)

        self.fullRigBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Full Rig"))
        self.jointsOnlyBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Joints Only"))
        self.ctrlsOnlyBtn.clicked.connect(lambda: self.Rigging.build_rig(mode="Controls Only"))

        # ------------ MODIFY CONTROLS ------------------
        modify_ctrls_label = QtWidgets.QLabel(text="Modify Controls")
        modify_ctrls_label.setProperty("header", "true")
        modify_ctrls_grid = QtWidgets.QGridLayout()
        modify_ctrls_grid.setSpacing(4)
        box_layout.addWidget(modify_ctrls_label)
        box_layout.addLayout(modify_ctrls_grid)
        modify_scale_label = QtWidgets.QLabel(text="Scale:")
        modify_rotation_label = QtWidgets.QLabel(text="Rotate:")
        self.scale_field = QtWidgets.QLineEdit()
        self.scale_apply = QtWidgets.QPushButton("Apply")

        self.rotate_x_pos = QtWidgets.QPushButton("X: 90")
        self.rotate_x_pos.setStyleSheet("background-color: #e30000; color: white;")
        self.rotate_y_pos = QtWidgets.QPushButton("Y: 90")
        self.rotate_y_pos.setStyleSheet("background-color: green; color: white;")
        self.rotate_z_pos = QtWidgets.QPushButton("Z: 90")
        self.rotate_z_pos.setStyleSheet("background-color: blue; color: white;")

        self.rotate_x_neg = QtWidgets.QPushButton("X: -90")
        self.rotate_x_neg.setStyleSheet("background-color: #6e0000; color: white;")
        self.rotate_y_neg = QtWidgets.QPushButton("Y: -90")
        self.rotate_y_neg.setStyleSheet("background-color: #064000; color: white;")
        self.rotate_z_neg = QtWidgets.QPushButton("Z: -90")
        self.rotate_z_neg.setStyleSheet("background-color: #001840; color: white;")

        modify_ctrls_grid.addWidget(modify_scale_label, 0, 0)
        modify_ctrls_grid.addWidget(self.scale_field, 0, 1)
        modify_ctrls_grid.addWidget(self.scale_apply, 0, 2)
        modify_ctrls_grid.addWidget(modify_rotation_label, 1, 0)
        modify_ctrls_grid.addWidget(self.rotate_x_pos, 1, 1)
        modify_ctrls_grid.addWidget(self.rotate_y_pos, 1, 2)
        modify_ctrls_grid.addWidget(self.rotate_z_pos, 1, 3)
        modify_ctrls_grid.addWidget(self.rotate_x_neg, 2, 1)
        modify_ctrls_grid.addWidget(self.rotate_y_neg, 2, 2)
        modify_ctrls_grid.addWidget(self.rotate_z_neg, 2, 3)
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
