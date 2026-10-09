import os

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide6 import QtWidgets, QtGui, QtCore
from shiboken6 import wrapInstance

import adentk.maya.prop_rig_toolkit.controls as controls
import adentk.maya.prop_rig_toolkit.rigging as rigging

DEV_ROOT = r"D:\_dev\adentk"
ICONS_DIR = os.path.join(DEV_ROOT, "maya", "icons")
DOCS_URL = "https://github.com"

def get_maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)

def make_header(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setProperty("header", "true")
    return label


def create_color_display(slider: QtWidgets.QSlider) -> QtWidgets.QPushButton:
    color_display = QtWidgets.QPushButton()
    color_display.setEnabled(False)
    color_display.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def update_color(color_index: int) -> None:
        rgb_floats = cmds.colorIndex(color_index, q=True)
        r, g, b = rgb_floats

        # Create Qt color using float values
        color = QtGui.QColor.fromRgbF(r, g, b)

        color_display.setStyleSheet(
            f"background-color: {color.name()}; "
        )

    slider.valueChanged.connect(update_color)
    update_color(slider.value())
    return color_display


def create_slider_grp(min_val: float, max_val: float, default: float = 1.0, decimals: int = 1) -> tuple[QtWidgets.QSlider, QtWidgets.QLineEdit]:
    scale = 10 ** decimals # Multiplier factor (10 for 1 decimal place)

    validator = QtGui.QDoubleValidator(min_val, max_val, decimals) # show 1 decimal place
    validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)

    field = QtWidgets.QLineEdit()
    field.setValidator(validator)
    field.setText(f"{default:.{decimals}f}")

    slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    slider.setRange(int(min_val * scale), int(max_val * scale))
    slider.setValue(int(1.0 * scale))

    def update_field(int_val: int) -> None:
        float_val = int_val / scale
        field.blockSignals(True)
        field.setText(f"{float_val:.{decimals}f}")
        field.blockSignals(False)

    def update_slider(text: str) -> None:
        if not text or text.strip() in (".", "-"):
            return

        try:
            val = float(text)
            # Clamp value to slider range
            val = max(min_val, min(max_val, val))

            slider.blockSignals(True)
            slider.setValue(int(val * scale))
            slider.blockSignals(False)
        except ValueError:
            pass

    def on_editing_finished() -> None:
        """Format the line edit to a clean decimal representation on defocus/enter"""
        try:
            val = float(field.text())
            val = max(min_val, min(max_val, val))
            field.setText(f"{val:.{decimals}f}")
        except ValueError:
            field.setText(f"{default:.{decimals}f}")

    field.textChanged.connect(update_slider)
    field.editingFinished.connect(on_editing_finished)
    slider.valueChanged.connect(update_field)

    return slider, field

def float_from_field(field: QtWidgets.QLineEdit, default: float) -> float:
    """Reads a float from a QLineEdit, falling back to a default on bad input"""
    try:
        return float(field.text())
    except ValueError:
        return default


class PropRiggingUI(QtWidgets.QDialog):
    WINDOW_TITLE = "Automatic Prop Rigger"
    OBJECT_NAME = "AutomaticPropRigger"

    DEFAULT_COLOR_INDEX = 6  # Blue
    ACTIVE_BTN_STYLE = "background-color: red"
    INACTIVE_BTN_STYLE = "background-color: none"

    STYLESHEET = """
        QCheckBox {
            color: white;
        }
        QPushButton {
            background-color: none;
            font-weight: bold;
            color: white;
        }
        QLabel {
            font-weight: bold;
            color: white;
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
    """

    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.on_reset_tool = None
        self.ctrl_color = self.DEFAULT_COLOR_INDEX
        self.rig = None

        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setStyleSheet(self.STYLESHEET)
        self.resize(350, 600)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(6)

        self._build_menu_bar()
        self._build_control_options()
        self._build_control_shapes()
        self._build_modify_controls()
        self._build_rig_options()
        self._build_advanced()
        self.main_layout.addStretch()


    def _build_menu_bar(self) -> None:
        menu_bar = QtWidgets.QMenuBar(self)
        help_menu = menu_bar.addMenu("Help")
        edit_menu = menu_bar.addMenu("Edit")

        doc_action = QtGui.QAction("Documentation", self)
        doc_action.triggered.connect(self.on_open_documentation)
        help_menu.addAction(doc_action)

        reset_action = QtGui.QAction("Reset Tool", self)
        reset_action.triggered.connect(self.on_reset_tool)
        edit_menu.addAction(reset_action)

        self.main_layout.setMenuBar(menu_bar)


    def _build_control_options(self) -> None:
        self.main_layout.addWidget(make_header("Control Options"))
        grid = QtWidgets.QGridLayout()

        self.ctrl_size_slider, self.ctrl_size_field = create_slider_grp(min_val=1.0, max_val=20.0, default=1.0)
        self.ctrl_thickness_slider, self.ctrl_thickness_field = create_slider_grp(min_val=1.0, max_val=20.0, default=1.0)

        self.ctrl_color_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.ctrl_color_slider.setRange(0, 31)
        self.ctrl_color_slider.setValue(self.DEFAULT_COLOR_INDEX)
        self.ctrl_color_display = create_color_display(self.ctrl_color_slider)
        self.ctrl_color_slider.valueChanged.connect(self.on_color_changed)

        self.ctrl_thickness_apply = QtWidgets.QPushButton("Re-Apply")
        self.ctrl_thickness_apply.clicked.connect(self.on_apply_thickness)
        self.color_apply_btn = QtWidgets.QPushButton("Re-Apply")
        self.color_apply_btn.clicked.connect(self.on_apply_color)

        grid.addWidget(QtWidgets.QLabel("Size:"), 0, 0)
        grid.addWidget(self.ctrl_size_field, 0, 1)
        grid.addWidget(self.ctrl_size_slider, 0, 2, 1, 2)

        grid.addWidget(QtWidgets.QLabel("Thickness:"), 1, 0)
        grid.addWidget(self.ctrl_thickness_field, 1, 1)
        grid.addWidget(self.ctrl_thickness_slider, 1, 2)
        grid.addWidget(self.ctrl_thickness_apply, 1, 3)

        grid.addWidget(QtWidgets.QLabel("Color:"), 2, 0)
        grid.addWidget(self.ctrl_color_display, 2, 1)
        grid.addWidget(self.ctrl_color_slider, 2, 2)
        grid.addWidget(self.color_apply_btn, 2, 3)

        for widget in (self.ctrl_size_field, self.ctrl_thickness_field, self.ctrl_color_display):
            widget.setMaximumWidth(50)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 0)

        self.main_layout.addLayout(grid)


    def _build_control_shapes(self) -> None:
        self.main_layout.addWidget(make_header("Control Shapes"))
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(4)

        # ( controls.ControlShapes.cvTuples KEY, icon filename )
        SHAPE_BUTTONS = [
            ("Circle", "circle.png"),
            ("Square", "square.png"),
            ("Triangle", "triangle.png"),
            ("Sphere", "sphere.png"),
            ("Box", "Box.png"),
            ("Pyramid", "pyramid.png"),
            ("Diamond", "diamond.png"),
            ("Circle Pin", "circle_pin.png"),
            ("Circle Dumbbell", "circle_dumbbell.png"),
            ("Four Arrows", "four_arrows.png"),
            ("Curved Four Arrows", "curved_four_arrows.png"),
            ("Two Arrows", "two_arrows.png"),
            ("Curved Two Arrows", "curved_two_arrows.png"),
            ("Circle One Arrow", "circle_one_arrow.png"),
            ("Circle Two Arrows", "circle_two_arrows.png"),
            ("Circle Four Arrows", "circle_four_arrows.png"),
            ("Gear", "gear.png"),
        ]

        SHAPE_GRID_COLUMNS = 5

        self.shape_buttons = {}
        for i, (shape, icon_filename) in enumerate(SHAPE_BUTTONS):
            btn = QtWidgets.QPushButton()
            btn.setToolTip(shape)
            btn.setIconSize(QtCore.QSize(60, 60))
            btn.setMaximumSize(70, 70)
            btn.setIcon(QtGui.QIcon(os.path.join(ICONS_DIR, icon_filename)))

            btn.clicked.connect(
                lambda checked=False, s=shape, b=btn: self.on_select_shape(s, b)
            )

            grid.addWidget(btn, i // SHAPE_GRID_COLUMNS, i % SHAPE_GRID_COLUMNS)
            self.shape_buttons[shape] = btn

        # Default selected shape
        self.active_shape = SHAPE_BUTTONS[0][0]
        self.active_shape_btn = self.shape_buttons[self.active_shape]
        self.active_shape_btn.setStyleSheet(self.ACTIVE_BTN_STYLE)

        self.main_layout.addLayout(grid)


    def _build_modify_controls(self) -> None:
        self.main_layout.addWidget(make_header("Transform Controls"))
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(4)

        self.scale_field = QtWidgets.QLineEdit("1.1")
        self.scale_up = QtWidgets.QPushButton("Scale Up")
        self.scale_down = QtWidgets.QPushButton("Scale Down")
        self.scale_up.clicked.connect(lambda: self.on_scale_ctrl(invert=False))
        self.scale_down.clicked.connect(lambda: self.on_scale_ctrl(invert=True))

        grid.addWidget(QtWidgets.QLabel("Scale:"), 0, 0)
        grid.addWidget(self.scale_field, 0, 1)
        grid.addWidget(self.scale_up, 0, 2)
        grid.addWidget(self.scale_down, 0, 3)

        # (label, rotation, stylesheet color, grid row, grid column)
        ROTATE_BUTTONS = [
            ("X: 90", (90, 0, 0), "#e30000", 1, 1),
            ("Y: 90", (0, 90, 0), "green", 1, 2),
            ("Z: 90", (0, 0, 90), "blue", 1, 3),
            ("X: -90", (-90, 0, 0), "#6e0000", 2, 1),
            ("Y: -90", (0, -90, 0), "#064000", 2, 2),
            ("Z: -90", (0, 0, -90), "#001840", 2, 3),
        ]

        grid.addWidget(QtWidgets.QLabel("Rotate:"), 1, 0)
        for label, rotation, color, row, col in ROTATE_BUTTONS:
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet(f"background-color: {color}; color: white; padding: 10px;")
            btn.clicked.connect(lambda checked=False, r=rotation: self.on_rotate_ctrl(r))
            grid.addWidget(btn, row, col)

        for col in (1, 2, 3):
            grid.setColumnStretch(col, 1)
        grid.setRowMinimumHeight(0, 50)

        self.main_layout.addLayout(grid)


    def _build_rig_options(self) -> None:
        self.main_layout.addWidget(make_header("Rig Options"))
        self.make_root_cb = QtWidgets.QCheckBox("Make Root Joint")
        self.make_root_cb.setChecked(True)
        self.display_layers_cb = QtWidgets.QCheckBox("Create Display Layers")
        self.display_layers_cb.setChecked(True)
        self.main_layout.addWidget(self.make_root_cb)
        self.main_layout.addWidget(self.display_layers_cb)

        # (button text, RigConfig.build_mode)
        BUILD_BUTTONS = [
            ("Full Rig", "FullRig"),
            ("Joints Only", "JointsOnly"),
            ("Controls Only", "ControlsOnly"),
        ]

        for text, mode in BUILD_BUTTONS:
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(lambda checked=False, m=mode: self.on_build_rig(m))
            self.main_layout.addWidget(btn)

    def _build_advanced(self) -> None:
        self.main_layout.addWidget(make_header("Advanced"))

        self.clear_rig_btn = QtWidgets.QPushButton("Clear Rig")
        self.clear_rig_btn.setStyleSheet("background-color: #9e0909")
        self.main_layout.addWidget(self.clear_rig_btn)
        self.clear_rig_btn.clicked.connect(self.on_clear_rig)
    def on_build_rig(self, mode):
        config = rigging.RigConfig()
        # Get user input settings
        config.ctrl_thickness = float_from_field(self.ctrl_thickness_field, default=1.0)
        config.ctrl_shape = self.active_shape
        config.build_mode = mode
        config.ctrl_color = self.ctrl_color_slider.value()
        config.ctrl_size = float_from_field(self.ctrl_size_field, default=1.0)

        self.rig = rigging.build_rig(config)

    def on_clear_rig(self):
        if not self.rig:
            cmds.warning("No rig instance found to clear.")
            return

        # Create confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Clear Rig",
            "Are you sure you want to clear the rig? This action cannot be undone.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No  # Default focused button
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            rigging.clear_rig(self.rig)
            self.rig = None

    def on_color_changed(self, color_index: int) -> None:
        """Triggers when slider moves/changes to apply color to viewport selection"""
        self.ctrl_color = color_index

    def on_open_documentation(self) -> None:
        """Opens the specified documentation link in the default browser/viewer."""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(DOCS_URL))

    def on_apply_thickness(self):
        selection = cmds.ls(sl=True, l=True)
        thickness = float_from_field(self.ctrl_thickness_field, default=1.0)
        if thickness > 1.0:
            controls.apply_thickness(sel=selection, thickness=thickness)

    def on_scale_ctrl(self, invert: bool) -> None:
        selection = cmds.ls(sl=True, l=True)
        scale = float(self.scale_field.text())

        if invert:
            scale = 1/scale  # Scale down

        controls.apply_scale(ctrls=selection, scale=scale)

    def on_apply_color(self) -> None:
        selection = cmds.ls(sl=True, l=True)
        color_index = self.ctrl_color_slider.value()
        if selection:
            controls.apply_color(sel=selection, color=color_index)

    def on_select_shape(self, shape: str, clicked_btn: QtWidgets.QPushButton) -> None:
        self.active_shape_btn.setStyleSheet(self.INACTIVE_BTN_STYLE)
        clicked_btn.setStyleSheet(self.ACTIVE_BTN_STYLE)

        self.active_shape_btn = clicked_btn
        self.active_shape = shape

        selection = cmds.ls(sl=True, l=True)
        curve_selection = [obj for obj in selection if cmds.listRelatives(obj, shapes=True, type="nurbsCurve", fullPath=True)]

        if not curve_selection:
            return

        # replace curve with new shape
        rigging.replace_controls(shape, selection, self.ctrl_color)

    def on_rotate_ctrl(self, rotate=(0, 0, 0)) -> None:
        selection = cmds.ls(sl=True, l=True)
        if selection:
            controls.apply_rotation(ctrls=selection, rotate=rotate)

def show_ui():
    maya_window = get_maya_main_window()
    existing_window = maya_window.findChild(QtWidgets.QDialog, PropRiggingUI.OBJECT_NAME)
    if existing_window:
        existing_window.close()
        existing_window.deleteLater()

    qt_window = PropRiggingUI()
    qt_window.show()

show_ui()
