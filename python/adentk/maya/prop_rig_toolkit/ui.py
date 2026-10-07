import adentk.maya.prop_rig_toolkit.controls as controls
import adentk.maya.prop_rig_toolkit.rigging as rigging
import maya.cmds as cmds

class PropRigUI:

    def __init__(self):
        self.window = None
        self.main_layout = None
        self.main_grp_field = None
        self.geo_suffix_field = None
        self.jnt_suffix_field = None
        self.ctrl_suffix_field = None
        self.offset_suffix_field = None
        self.root_jnt_field = None
        self.make_root_jnt_checkbox = None
        self.ctrl_size_slider = None
        self.ctrl_shape_menu = None
        self.ctrl_color_slider = None

    def show(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

        self.build_ui()
        cmds.showWindow(self.window)

    def build_ui(self):
        if cmds.window("AutomaticPropRigger", exists=True):
            cmds.deleteUI("AutomaticPropRigger")

        self.window = cmds.window("AutomaticPropRigger", title="Automatic Prop Rigger", menuBar=True, widthHeight=(350, 420))

        # --- Help & Documentation ----
        cmds.menu(label='Help', tearOff=False)
        cmds.menuItem(label='Documentation')
        cmds.menu(label='Preferences', tearOff=False)
        cmds.menuItem(label='Save')
        cmds.menuItem(label='Load')

        # --- Main Outer Layout ----
        self.main_layout = cmds.columnLayout(adjustableColumn=True)

        # --- Control Options ----
        cmds.text(label='Control Options', font='boldLabelFont', align='center')
        cmds.separator(height=5, style='none')

        self.ctrl_size_slider = cmds.floatSliderGrp(
            label='Control Size',
            field=True,
            minValue=0.1,
            maxValue=100,
            value=1.0,
            step=1,
            columnWidth=[(1, 90), (2, 50), (3, 150)]
        )

        self.ctrl_color_slider = cmds.colorSliderGrp(
            label='Control Color',
            hsv=(120, 1, 1),
            columnWidth=[(1, 90), (2, 50), (3, 150)]
        )

        cmds.separator(height=15, style='single')
        cmds.text(label='Control Shapes', font='boldLabelFont', align='center')
        cmds.separator(height=5, style='none')

        self.ctrl_shape_menu = cmds.rowColumnLayout(
            numberOfColumns=3,
            columnAttach=[(1, 'both', 2), (2, 'both', 2), (3, 'both', 2)],
            columnWidth=[(1, 110), (2, 110), (3, 110)],
            rowSpacing=[(1, 4), (2, 4), (3, 4)]
        )

        cmds.button(label='Box')
        cmds.button(label='Circle')
        cmds.button(label='Sphere')
        cmds.button(label='Cross')
        cmds.button(label='Square')
        cmds.button(label='Pointer')
        cmds.button(label='Custom')

        cmds.setParent(self.main_layout)
        cmds.separator(height=25, style='single')

        # --- Rig Options ----
        cmds.text(label='Rig Options', font='boldLabelFont', align='center')
        cmds.separator(height=5, style='none')

        cmds.rowColumnLayout(
            numberOfColumns=3,
            columnAttach=[(1, 'both', 2), (2, 'both', 2), (3, 'both', 2)],
            columnWidth=[(1, 110), (2, 110), (3, 110)],
            rowSpacing=[(1, 4)]
        )

        self.make_root_jnt_checkbox = cmds.checkBox(label='Make Root Joint')
        cmds.text(label='')
        cmds.text(label='')

        cmds.button(label='Full Rig')
        cmds.button(label='Joints Only')
        cmds.button(label='Controls Only')
        cmds.setParent(self.main_layout)  # Exit back to main layout

        cmds.separator(height=15, style='none')

        # --- Naming Settings ---
        cmds.frameLayout(label='Naming Conventions', collapsable=True, marginWidth=5, marginHeight=5)
        cmds.rowColumnLayout(
            numberOfColumns=2,
            columnAttach=[(1, 'right', 5), (2, 'both', 0)],
            columnWidth=[(1, 120), (2, 1)],
            adj=2
        )

        cmds.text(label='Main Group Name')
        self.main_grp_field = cmds.textField()

        cmds.text(label='Root Joint Name')
        self.root_jnt_field = cmds.textField()

        cmds.text(label='Geometry Suffix')
        self.geo_suffix_field = cmds.textField()

        cmds.text(label='Joint Suffix')
        self.jnt_suffix_field = cmds.textField()

        cmds.text(label='Offset Suffix')
        self.offset_suffix_field = cmds.textField()

        cmds.text(label='Control Suffix')
        self.ctrl_suffix_field = cmds.textField()

        cmds.setParent(self.main_layout)  # Return to main layout

    def on_build_rig(self, *args):
        naming_input = rigging.NamingConventions(
            main_grp = cmds.textField(self.main_grp_field, query=True, text=True),
            geo_suffix = cmds.textField(self.geo_suffix_field, query=True, text=True),
            jnt_suffix = cmds.textField(self.jnt_suffix_field, query=True, text=True),
            ctrl_suffix = cmds.textField(self.ctrl_suffix_field, query=True, text=True),
            offset_suffix = cmds.textField(self.offset_suffix_field, query=True, text=True),
            root_jnt = cmds.textField(self.root_jnt_field, query=True, text=True)
        )

        make_root = cmds.checkBox(self.make_root_jnt_checkbox, query=True, value=True)
        selection = cmds.ls(selection=True)
        rigging.createJoints(naming_input, selection, make_root)

