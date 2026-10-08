import maya.cmds as cmds
import adentk.maya.prop_rig_toolkit.controls as controls

from dataclasses import dataclass
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
    "root_jnt": "root_jnt"
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
        self.objects_list = cmds.ls(sl=True) or []
        self.mesh_xform_list =[
            obj for obj in self.objects_list
            if cmds.listRelatives(obj, type="mesh", path=True) is not None
        ]

        if makeRoot:
            cmds.select(clear=True)
            self.root_jnt = cmds.joint( n=NAMING["root_jnt"], sc=False )

        # Create Main Group and Sub-Groups
        self.main_grp = cmds.group( n=NAMING["main_grp"], em=True )
        self.geo_grp = cmds.group( n=NAMING["geo_grp"], em=True )
        self.jnt_grp = cmds.group( n=NAMING["jnt_grp"], em=True )
        self.ctrl_grp = cmds.group( n=NAMING["ctrl_grp"], em=True )

        cmds.parent([self.geo_grp, self.jnt_grp, self.ctrl_grp], self.main_grp)

        # Process & Rename Meshes, then Parent under geo_grp
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
        self.create_controls(shape, self.joints_list)

        # Lock and hide geo and joints
        for grp in [self.main_grp, self.geo_grp, self.jnt_grp]:
            if grp and cmds.objExists(grp):
                self.lock_and_hide(grp)

    def create_joints(self, makeRoot: bool = True):
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
            jnt = cmds.joint(n=obj + NAMING["jnt_sfx"], sc=False, position=pivot_pos[:3])

            if root_joint:
                jnt = cmds.parent(jnt, root_joint)[0]
            else:
                cmds.parent(jnt, self.jnt_grp)

            # Skin mesh to joint
            cmds.skinCluster(obj, jnt, toSelectedBones=True)
            self.joints_list.append(jnt)

    def create_controls(self, shape: str, joints: List):
        self.offset_control_list = []
        self.control_list = []

        cmds.select(clear=True)
        for jnt in joints:
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

    def lock_and_hide(self, node: str):
        channels = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
        for attr in channels:
            cmds.setAttr(f"{node}.{attr}", lock=True)
            cmds.setAttr(f"{node}.{attr}", keyable=False, channelBox=False)