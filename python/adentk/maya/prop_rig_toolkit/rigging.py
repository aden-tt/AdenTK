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
        self.ctrl_grp = None
        self.jnt_grp = None
        self.geo_grp = None
        self.root_jnt = None

        self.objects_list = []
        self.mesh_xform_list = []
        self.offset_control_list = []
        self.joints_list = []
        self.control_list = []

    def build_rig(self, mode: str = "Full Rig", makeRoot: bool = True):
        self.objects_list.append(cmds.ls(sl=True))
        self.mesh_xform_list.append([obj for obj in self.objects_list if cmds.listRelatives(obj, type="mesh", path=True) is not None])

        if makeRoot:
            cmds.select(clear=True)
            self.root_jnt = cmds.joint( n=NAMING["root_jnt"], sc=False )

        self.geo_grp = cmds.group( n=NAMING["geo_grp"], empty=True )
        self.jnt_grp = cmds.group( n=NAMING["jnt_grp"], empty=True )
        self.ctrl_grp = cmds.group( n=NAMING["ctrl_grp"], empty=True )

        #self.create_joints()
        #self.create_controls()



    def create_joints(self, makeRoot: bool = True):

        if makeRoot:
            cmds.select(clear=True)
            rootJoint = cmds.joint(name=NAMING["root_jnt"], sc=False)

        # Ensure the list contains only mesh objects
        if len(self.mesh_xform_list) == 0:
            cmds.error("Please select at least one mesh")

        for obj in self.mesh_xform_list:
            # Add a joint to pivot center of each selection, if root option is checked, parent all joins to it
            cmds.select(clear=True)

            # Create a joint at the mesh pivot location
            pivotPos = cmds.xform( obj, query=True, pivots=True, worldSpace=True )
            jnt = cmds.joint( name=obj + NAMING["jnt_sfx"], sc=False, position=[pivotPos[0], pivotPos[1], pivotPos[2]] )
            self.joints_list.append(jnt)


    def place_joints(self, objects: List):
        cmds.select(clear=True)
        for obj in objects:
            world_pivot = cmds.xform(obj, query=True, worldSpace=True)
            jnt = cmds.joint(name=obj.replace( NAMING["geo_sfx"], NAMING["jnt_sfx"] ), sc=False)

    def create_controls(self, joints: List):
        cmds.select(clear=True)
        for jnt in self.joints_list:
            offsetGrp = cmds.group(em=True, name=jnt.replace( NAMING["jnt_sfx"], NAMING["offset_sfx"] ))
            self.offset_control_list.append(offsetGrp)


    def create_parent_group(self, name: str, objects: List) -> str:
        pass


"""
    def OLD_createJoints(objectList, makeRoot=True):
        jntList = []
        rootJoint = None

        if makeRoot:
            cmds.select(clear=True)
            rootJoint = cmds.joint(name=naming.root_jnt, sc=False)

        # Ensure the list contains only mesh objects
        meshXformList = [obj for obj in objectList if cmds.listRelatives(obj, type="mesh", path=True) is not None]
        if len(meshXformList) == 0:
            cmds.error(" Please select at least one mesh")

        for obj in meshXformList:
            # Add a joint to pivot center of each selection, if root option is checked, parent all joins to it
            cmds.select(clear=True)

            # Create a joint at the mesh pivot location
            pivotPos = cmds.xform(obj, query=True, pivots=True, worldSpace=True)
            jnt = cmds.joint(name=obj + naming.jnt_suffix, sc=False, position=[pivotPos[0], pivotPos[1], pivotPos[2]])

            # Create an empty offset group
            offsetGroup = cmds.group(n=obj+naming.offset_suffix , empty=True)

            # Position offset group at joint
            jnt_pos = cmds.xform(jnt, query=True, translation=True, worldSpace=True)
            cmds.xform(offsetGroup, translation=jnt_pos, worldSpace=True)

            # Create control at joint location
            control = cmds.circle(n=obj+naming.ctrl_suffix)
            cmds.parent(control, offsetGroup)
            cmds.xform(control, translation=[0, 0, 0], rotation=[0, 0, 0])

            # Constrain joint to control
            cmds.parentConstraint(control, jnt, mo=True)

            # Skin the mesh geometry to the joint
            if makeRoot:
                jnt = cmds.parent(jnt, rootJoint)

            cmds.skinCluster(obj, jnt, toSelectedBones=True)
            jntList.append(jnt)

        if makeRoot:
            return jntList, rootJoint
        else:
            return jntList

"""
