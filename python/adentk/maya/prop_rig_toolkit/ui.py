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
DOCS_URL = "https://github.com"

def get_maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


def create_color_display(slider: QtWidgets.QSlider) -> QtWidgets.QPushButton:
    color_display = QtWidgets.QPushButton()
    color_display.setEnabled(False)
    color_display.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def update_color(value: int) -> None:
        # Query RGB floats (0.0 to 1.0) directly from Maya
        rgb_floats = cmds.colorIndex(value, q=True)
        r, g, b = rgb_floats

        # Create Qt color using float values
        color = QtGui.QColor.fromRgbF(r, g, b)

        color_display.setStyleSheet(
            f"background-color: {color.name()}; "
        )

    slider.valueChanged.connect(update_color)
    update_color(slider.value())
    return color_display


def create_slider_grp() -> tuple[QtWidgets.QSlider, QtWidgets.QLineEdit]:
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

        self.ctrl_color = None

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
                qproperty-alignment:  AlignRight;
                qproperty-alignment: AlignVCenter;
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
        self.resize(350, 600)

        box_layout = QtWidgets.QVBoxLayout(self)
        box_layout.setContentsMargins(10, 10, 10, 10)
        box_layout.setSpacing(6)

        # ------------ MENU BAR ------------------
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.help_menu = self.menu_bar.addMenu("Help")

        self.doc_action = QtGui.QAction("Documentation", self)
        self.doc_action.triggered.connect(self.on_open_documentation)
        self.help_menu.addAction(self.doc_action)

        box_layout.setMenuBar(self.menu_bar)

        # Container layout padding below menu bar
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(10, 0, 10, 0)
        content_layout.setSpacing(6)
        box_layout.addLayout(content_layout)

        # ------------ CONTROL OPTIONS ------------------
        ctrl_options_label = QtWidgets.QLabel(text="Control Options")
        ctrl_options_label.setProperty("header", "true")
        ctrl_options_grid = QtWidgets.QGridLayout()

        ctrl_size_label = QtWidgets.QLabel("Size:")
        ctrl_color_label = QtWidgets.QLabel("Color:")
        ctrl_thickness_label = QtWidgets.QLabel("Thickness:")

        self.ctrl_size_slider, self.ctrl_size_field = create_slider_grp()
        self.ctrl_thickness_slider, self.ctrl_thickness_field = create_slider_grp()
        self.ctrl_thickness_apply = QtWidgets.QPushButton("Re-Apply")

        self.ctrl_color_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.ctrl_color_slider.setRange(0, 31)
        self.ctrl_color_slider.setValue(17)  # Default index (17 = Yellow)
        self.ctrl_color_display = create_color_display(self.ctrl_color_slider)


        self.color_apply_btn = QtWidgets.QPushButton("Re-Apply")
        self.color_apply_btn.clicked.connect(self.on_apply_color)
        self.ctrl_thickness_apply.clicked.connect(self.on_apply_thickness)

        self.ctrl_color_slider.valueChanged.connect(self.on_color_changed)
        self.ctrl_color_slider.sliderMoved.connect(self.on_color_changed)

        ctrl_options_grid.addWidget(ctrl_size_label, 0, 0)
        ctrl_options_grid.addWidget(self.ctrl_size_field, 0, 1)
        ctrl_options_grid.addWidget(self.ctrl_size_slider, 0, 2, 1, 2)

        ctrl_options_grid.addWidget(ctrl_thickness_label, 1, 0)
        ctrl_options_grid.addWidget(self.ctrl_thickness_field, 1, 1)
        ctrl_options_grid.addWidget(self.ctrl_thickness_slider, 1, 2)
        ctrl_options_grid.addWidget(self.ctrl_thickness_apply, 1, 3)

        ctrl_options_grid.addWidget(ctrl_color_label, 2, 0)
        ctrl_options_grid.addWidget(self.ctrl_color_display, 2, 1)
        ctrl_options_grid.addWidget(self.ctrl_color_slider, 2, 2)
        ctrl_options_grid.addWidget(self.color_apply_btn, 2, 3)

        self.ctrl_size_field.setMaximumWidth(50)
        self.ctrl_thickness_field.setMaximumWidth(50)
        self.ctrl_color_display.setMaximumWidth(50)
        ctrl_options_grid.setColumnStretch(0, 0)
        ctrl_options_grid.setColumnStretch(1, 0)
        ctrl_options_grid.setColumnStretch(2, 1)
        ctrl_options_grid.setColumnStretch(3, 0)

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

        columns = 5
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
        self.scale_up = QtWidgets.QPushButton("Scale Up")
        self.scale_down = QtWidgets.QPushButton("Scale Down")
        self.scale_up.clicked.connect(self.on_scale_ctrl)

        self.rotate_x_pos = QtWidgets.QPushButton("X: 90")
        self.rotate_x_pos.setStyleSheet("background-color: #e30000; color: white; padding: 10px;")
        self.rotate_x_pos.clicked.connect(lambda: self.on_rotate_ctrl( [90,0,0] ))

        self.rotate_y_pos = QtWidgets.QPushButton("Y: 90")
        self.rotate_y_pos.setStyleSheet("background-color: green; color: white; padding: 10px;")
        self.rotate_y_pos.clicked.connect(lambda: self.on_rotate_ctrl( [0,90,0] ))

        self.rotate_z_pos = QtWidgets.QPushButton("Z: 90")
        self.rotate_z_pos.setStyleSheet("background-color: blue; color: white; padding: 10px;")
        self.rotate_z_pos.clicked.connect(lambda: self.on_rotate_ctrl( [0,0,90] ))

        self.rotate_x_neg = QtWidgets.QPushButton("X: -90")
        self.rotate_x_neg.setStyleSheet("background-color: #6e0000; color: white; padding: 10px;")
        self.rotate_x_neg.clicked.connect(lambda: self.on_rotate_ctrl( [-90,0,0] ))

        self.rotate_y_neg = QtWidgets.QPushButton("Y: -90")
        self.rotate_y_neg.setStyleSheet("background-color: #064000; color: white; padding: 10px;")
        self.rotate_y_neg.clicked.connect(lambda: self.on_rotate_ctrl( [0,-90,0] ))

        self.rotate_z_neg = QtWidgets.QPushButton("Z: -90")
        self.rotate_z_neg.setStyleSheet("background-color: #001840; color: white; padding: 10px;")
        self.rotate_z_neg.clicked.connect(lambda: self.on_rotate_ctrl( [0,0,-90] ))

        modify_ctrls_grid.addWidget(modify_scale_label, 0, 0)
        modify_ctrls_grid.addWidget(self.scale_field, 0, 1)
        modify_ctrls_grid.addWidget(self.scale_up, 0, 2)
        modify_ctrls_grid.addWidget(self.scale_down, 0, 3)

        modify_ctrls_grid.addWidget(modify_rotation_label, 1, 0)
        modify_ctrls_grid.addWidget(self.rotate_x_pos, 1, 1)
        modify_ctrls_grid.addWidget(self.rotate_y_pos, 1, 2)
        modify_ctrls_grid.addWidget(self.rotate_z_pos, 1, 3)
        modify_ctrls_grid.addWidget(self.rotate_x_neg, 2, 1)
        modify_ctrls_grid.addWidget(self.rotate_y_neg, 2, 2)
        modify_ctrls_grid.addWidget(self.rotate_z_neg, 2, 3)

        modify_ctrls_grid.setColumnStretch(1, 1)
        modify_ctrls_grid.setColumnStretch(2, 1)
        modify_ctrls_grid.setColumnStretch(3, 1)

        modify_ctrls_grid.setRowMinimumHeight(0, 50)

        # ------------ RIGGING OPTIONS ------------------
        rig_options_label = QtWidgets.QLabel(text="Rig Options")
        rig_options_label.setProperty("header", "true")
        rig_options_box = QtWidgets.QVBoxLayout()
        box_layout.addWidget(rig_options_label)

        self.makeRootCB = QtWidgets.QCheckBox("Make Root Joint")
        self.makeRootCB.setChecked(True)
        self.jntRefCB = QtWidgets.QCheckBox("Create Display Layers")
        self.jntRefCB.setChecked(True)
        box_layout.addWidget(self.makeRootCB)
        box_layout.addWidget(self.jntRefCB)
        self.fullRigBtn = QtWidgets.QPushButton("Full Rig")
        self.jointsOnlyBtn = QtWidgets.QPushButton("Joints Only")
        self.ctrlsOnlyBtn = QtWidgets.QPushButton("Controls Only")

        rig_options_box.addWidget(self.fullRigBtn)
        rig_options_box.addWidget(self.jointsOnlyBtn)
        rig_options_box.addWidget(self.ctrlsOnlyBtn)
        box_layout.addLayout(rig_options_box)

        self.fullRigBtn.clicked.connect(
            lambda: self.Rigging.build_rig(
                color=self.ctrl_color,
                scale=self.control_size(),
                shape=self.selected_shape,
                mode="FullRig",
                makeRoot=self.makeRootCB.isChecked()
            )
        )
        self.jointsOnlyBtn.clicked.connect(
            lambda: self.Rigging.build_rig(
                color=self.ctrl_color,
                scale=self.control_size(),
                shape=self.selected_shape,
                mode="JointsOnly",
                makeRoot=self.makeRootCB.isChecked()
            )
        )
        self.ctrlsOnlyBtn.clicked.connect(
            lambda: self.Rigging.build_rig(
                color=self.ctrl_color,
                scale=self.control_size(),
                shape=self.selected_shape,
                mode="ControlsOnly",
                makeRoot=self.makeRootCB.isChecked()
            )
        )

        # ----- CLEAR RIG ------
        clear_rig_label = QtWidgets.QLabel(text="Advanced")
        clear_rig_label.setProperty("header", "true")
        clear_rig_box = QtWidgets.QVBoxLayout()
        box_layout.addWidget(clear_rig_label)
        self.clearRigBtn = QtWidgets.QPushButton("Clear Rig")
        self.clearRigBtn.setStyleSheet("background-color: #9e0909")
        clear_rig_box.addWidget(self.clearRigBtn)
        box_layout.addLayout(clear_rig_box)

        # Make widget compact
        box_layout.addStretch()

    def on_open_documentation(self) -> None:
        """Opens the specified documentation link in the default browser/viewer."""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(DOCS_URL))

    def on_apply_thickness(self):
        thickness = self.ctrl_thickness_slider.value()
        selection = cmds.ls(sl=True, l=True)
        if thickness > 1.0:
            controls.apply_thickness_to_selected(sel=selection, thickness=thickness)


    def on_scale_ctrl(self):
        selection = cmds.ls(sl=True, l=True)
        scale = float(self.scale_field.text())
        controls.apply_scale_to_selected(ctrls=selection, scale=scale)

    def on_apply_color(self, color_index: int) -> None:
        selection = cmds.ls(sl=True, l=True)
        if selection:
            self.ControlUtils.bsSetIndex(color_index)

    def on_color_changed(self, color_index: int) -> None:
        """Triggers when slider moves/changes to apply color to viewport selection"""
        self.ctrl_color = color_index

    def control_size(self):
        """Helper function to get scale input, guards against empty input"""
        try:
            return float(self.ctrl_size_field.text())
        except ValueError:
            return 1.0

    def on_select_shape(self, shape: str, clicked_btn: QtWidgets.QPushButton):
        # toggle active/inactive button modes
        self.selected_shape_btn.setStyleSheet("background-color: none")
        clicked_btn.setStyleSheet("background-color: red")

        self.selected_shape_btn = clicked_btn
        self.selected_shape = shape

        selection = cmds.ls(sl=True, l=True)
        if not selection:
            return

        # replace curve with new shape
        self.Rigging.replaceControls(shape, selection)

    def on_rotate_ctrl(self, rotate=(0,0,0)):
        controls.apply_rotation_to_selected(rotate)


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
