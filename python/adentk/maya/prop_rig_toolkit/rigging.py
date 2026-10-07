import maya.cmds as cmds
from dataclasses import dataclass

@dataclass
class NamingConventions:
    main_grp: str
    geo_suffix: str
    jnt_suffix: str
    ctrl_suffix: str
    offset_suffix: str
    root_jnt: str


def createJoints(naming: NamingConventions, objectList, makeRoot=True):
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