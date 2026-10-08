import maya.cmds as cmds
import adentk.maya.prop_rig_toolkit.controls as controls

from typing import List

NAMING = {
    "main_grp": "main_grp",
    "jnt_grp":  "jnt_grp",
    "ctrl_grp": "ctrl_grp",
    "geo_grp": "geo_grp",
    "geo_sfx":  "_geo",
    "jnt_sfx":  "_jnt",
    "ctrl_sfx": "_ctrl",
    "off_sfx":  "_offset",
    "root_jnt": "root_jnt",
    "geo_layer": "GEO_layer",
    "ctrl_layer": "CTRL_layer"
}


class RiggingToolkit:
    def __init__(self):
        self.utils = controls.BSControlsUtils()
        self.main_grp = None
        self.ctrl_grp = None
        self.jnt_grp = None
        self.geo_grp = None
        self.root_jnt = None

        self.objects_list = []
        self.mesh_xform_list = []
        self.offset_control_list = []
        self.joints_list = []
        self.control_list = []

    def build_rig(self, shape: str, mode: str = "FullRig", makeRoot: bool = True):
        """Executes the full rigging pipeline for selected mesh objects"""
        self.objects_list = cmds.ls(sl=True) or []
        self.mesh_xform_list =[
            obj for obj in self.objects_list
            if cmds.listRelatives(obj, type="mesh", path=True) is not None
        ]

        # Create Main Group and sub-groups
        self.main_grp = cmds.group( n=NAMING["main_grp"], em=True )
        self.geo_grp = cmds.group( n=NAMING["geo_grp"], em=True )
        self.jnt_grp = cmds.group( n=NAMING["jnt_grp"], em=True )
        self.ctrl_grp = cmds.group( n=NAMING["ctrl_grp"], em=True )

        cmds.parent([self.geo_grp, self.jnt_grp, self.ctrl_grp], self.main_grp)

        # Process and rename meshes, then parent under geo_grp
        processed_geo_list = []
        for obj in self.mesh_xform_list:
            geo_name = obj
            # Add suffix if it doesn't already end with geo_sfx
            if not obj.endswith(NAMING["geo_sfx"]):
                geo_name = cmds.rename(obj, obj + NAMING["geo_sfx"])

            # Parent under geo_grp
            cmds.parent(geo_name, self.geo_grp)
            processed_geo_list.append(geo_name)

        self.mesh_xform_list = processed_geo_list

        self.create_joints()
        if not mode == "JointsOnly":
            self.create_controls(shape, self.joints_list)

        # Lock and hide geo and joints
        self.lock_and_hide_grp(self.geo_grp, self.jnt_grp)
        self.setup_display_layers()


    def create_joints(self, makeRoot: bool = True):
        """Creates joints at mesh pivots and binds them to skin"""
        self.joints_list = []
        root_joint = None

        if makeRoot:
            cmds.select(clear=True)
            root_joint = cmds.joint(n=NAMING["root_jnt"], sc=False)
            cmds.parent(root_joint, self.jnt_grp)
            self.root_jnt = root_joint

        for obj in self.mesh_xform_list:
            cmds.select(clear=True)

            # Create joint at object pivot
            pivot_pos = cmds.xform(obj, query=True, pivots=True, worldSpace=True)
            jnt_name = obj.replace(NAMING["geo_sfx"], NAMING["jnt_sfx"])
            jnt = cmds.joint(n=jnt_name, sc=False, position=pivot_pos[:3])

            if root_joint:
                jnt = cmds.parent(jnt, root_joint)[0]
            else:
                cmds.parent(jnt, self.jnt_grp)

            # Skin mesh to joint
            cmds.skinCluster(obj, jnt, toSelectedBones=True)
            self.joints_list.append(jnt)

    def create_controls(self, shape: str, joints: List):
        """Generates offset groups and control curves for each joint"""
        self.offset_control_list = []
        self.control_list = []

        cmds.select(clear=True)
        for jnt in joints:
            # Create offset group
            off_name = jnt.replace(NAMING["jnt_sfx"], NAMING["off_sfx"])
            offset_grp = cmds.group(em=True, n=off_name)
            self.offset_control_list.append(offset_grp)

            # Match joint transform
            jnt_pos = cmds.xform(jnt, query=True, translation=True, worldSpace=True)
            cmds.xform(offset_grp, translation=jnt_pos, worldSpace=True)

            # Create control curve and parent under offset group
            ctrl = self.utils.bsDrawCurve(curve=shape, thickness=1.0)
            cmds.parent(ctrl, offset_grp)
            cmds.xform(ctrl, translation=[0, 0, 0], rotation=[0, 0, 0])
            cmds.parent(offset_grp, self.ctrl_grp)

            # Constrain joint to control
            cmds.parentConstraint(ctrl, jnt, mo=True)
            self.control_list.append(ctrl)

    def lock_and_hide_grp(self, geo, jnt):
        """Locks and hides transform attributes for all children in geometry and joint groups"""
        for grp in [geo, jnt]:
            if grp and cmds.objExists(grp):
                # Lock the group itself
                self.lock_and_hide(grp)

                # Lock all children under the group
                children = cmds.listRelatives(grp, allDescendents=True, fullPath=True, type="transform") or []
                for child in children:
                    self.lock_and_hide(child)

    def lock_and_hide(self, node: str):
        """Locks and disables keying translate, rotate, and scale attributes on a node"""
        cmds.setAttr(node + '.tx', l=1, k=0)
        cmds.setAttr(node + '.ty', l=1, k=0)
        cmds.setAttr(node + '.tz', l=1, k=0)
        cmds.setAttr(node + '.rx', l=1, k=0)
        cmds.setAttr(node + '.ry', l=1, k=0)
        cmds.setAttr(node + '.rz', l=1, k=0)
        cmds.setAttr(node + '.sx', l=1, k=0)
        cmds.setAttr(node + '.sy', l=1, k=0)
        cmds.setAttr(node + '.sz', l=1, k=0)

    def setup_display_layers(self):
        """Creates Display Layers for geometry, controls, and joints."""

        # Geometry Layer (Reference mode so geo cannot be selected in viewport)
        if cmds.objExists(NAMING["geo_layer"]):
            cmds.delete(NAMING["geo_layer"])
        geo_layer = cmds.createDisplayLayer(name=NAMING["geo_layer"], number=1, empty=True)
        cmds.editDisplayLayerMembers(geo_layer, self.geo_grp)
        cmds.setAttr(f"{geo_layer}.displayType", 2)

        # Controls Layer (Visible)
        if cmds.objExists(NAMING["ctrl_layer"]):
            cmds.delete(NAMING["ctrl_layer"])
        ctrl_layer = cmds.createDisplayLayer(name=NAMING["ctrl_layer"], number=1, empty=True)
        cmds.editDisplayLayerMembers(ctrl_layer, self.ctrl_grp)

        # Joints Layer (Hidden by default, set to Reference mode)
        jnt_layer_name = NAMING.get("jnt_layer", "JNT_layer")
        if cmds.objExists(jnt_layer_name):
            cmds.delete(jnt_layer_name)
        jnt_layer = cmds.createDisplayLayer(name=jnt_layer_name, number=1, empty=True)
        cmds.editDisplayLayerMembers(jnt_layer, self.jnt_grp)
        cmds.setAttr(f"{jnt_layer}.displayType", 2)
        cmds.setAttr(f"{jnt_layer}.visibility", 0)
