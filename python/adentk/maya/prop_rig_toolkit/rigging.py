import maya.cmds as cmds
import adentk.maya.prop_rig_toolkit.controls as controls
from dataclasses import dataclass, field
from typing import List, Tuple, Any


@dataclass(frozen=True)
class NamingConfig:
    main_grp: str = "main_grp"
    jnt_grp: str = "jnt_grp"
    ctrl_grp: str = "ctrl_grp"
    geo_grp: str = "geo_grp"
    geo_sfx: str = "_geo"
    jnt_sfx: str = "_jnt"
    ctrl_sfx: str = "_ctrl"
    off_sfx: str = "_offset"
    root_jnt: str = "root_jnt"
    jnt_layer: str = "JNT_layer"
    geo_layer: str = "GEO_layer"
    ctrl_layer: str = "CTRL_layer"

NAMING = NamingConfig()

@dataclass
class RigConfig:
    make_root: bool = True
    create_display_layers: bool = True
    build_mode: str = "FullRig" # Options: "FullRig", "ControlsOnly", "JointsOnly"
    ctrl_shape: str = "Circle"
    ctrl_size: float = 1.0
    ctrl_thickness: float = 1.0
    ctrl_color: int = 1

@dataclass
class Rig:
    """Container holding created scene nodes for a built rig"""
    main_grp: str = None
    ctrl_grp: str = None
    jnt_grp: str = None
    geo_grp: str = None
    root_jnt: str = None
    objects_list: List[str] = field(default_factory=list)
    mesh_xform_list: List[str] = field(default_factory=list)
    offset_control_list: List[str] = field(default_factory=list)
    joints_list: List[str] = field(default_factory=list)
    ctrl_list: List[str] = field(default_factory=list)



# TODO when replace shape, transfer thickness and color options
def replace_controls(new_shape, selection) -> None:
    """Replaces the shape of selected controls with a new curve shape"""
    temp_curve = controls.draw_curve(curve=new_shape)

    for sel in selection:
        old_thickness = None
        old_color = None

        if cmds.attributeQuery("lineWidth", node=sel, exists=True):
            old_thickness = cmds.getAttr(f"{sel}.lineWidth")
        if cmds.attributeQuery("overrideColor", node=sel, exists=True):
            old_color = cmds.getAttr(f"{sel}.overrideColor")


        ctrl_name = sel if sel.endswith(NAMING.ctrl_sfx) else f"{sel}{NAMING.ctrl_sfx}"
        controls.replace_shape(target=sel, replacement=temp_curve, mirror=False)
        controls.apply_color(ctrl_name, old_color)
        controls.apply_thickness(ctrl_name, old_thickness)

        if cmds.objExists(sel) and sel != ctrl_name:
            cmds.rename(sel, ctrl_name)

    if cmds.objExists(temp_curve):
        cmds.delete(temp_curve)


def lock_and_hide(node: str) -> None:
    """Locks and disables keying for translate, rotate, and scale attributes on a node"""
    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
        cmds.setAttr(f"{node}.{attr}", l=1, k=0)


def lock_and_hide_grp(grp: str) -> None:
    """Locks and hides transform attributes for all children groups"""
    if grp and cmds.objExists(grp):
        lock_and_hide(grp)
        children = cmds.listRelatives(grp, allDescendents=True, fullPath=True, type="transform") or []
        for child in children:
            lock_and_hide(child)


def build_rig(config: RigConfig) -> Rig:
    """Executes the full rigging pipeline for the selected mesh objects."""
    rig = Rig()
    rig.objects_list = cmds.ls(sl=True) or []
    rig.mesh_xform_list = [
        obj for obj in rig.objects_list
        if cmds.listRelatives(obj, type="mesh", path=True) is not None
    ]

    create_groups(rig)
    prepare_geometry(rig)
    create_joints(rig, make_root=config.make_root)

    if config.build_mode != "JointsOnly":
        create_controls(rig, config)
        lock_and_hide_grp(rig.geo_grp)
        lock_and_hide_grp(rig.jnt_grp)

        if config.create_display_layers:
            setup_display_layers(rig)

        ctrls = cmds.select(rig.ctrl_list, replace=True)
        controls.apply_color(sel=ctrls,color=config.ctrl_color)

    return rig


def create_groups(rig: Rig) -> None:
    """Creates the main group and its geo/joint/control subgroups."""
    rig.main_grp = cmds.group(n=NAMING.main_grp, em=True)
    rig.geo_grp = cmds.group(n=NAMING.geo_grp, em=True)
    rig.jnt_grp = cmds.group(n=NAMING.jnt_grp, em=True)
    rig.ctrl_grp = cmds.group(n=NAMING.ctrl_grp, em=True)

    cmds.parent([rig.geo_grp, rig.jnt_grp, rig.ctrl_grp], rig.main_grp)


def prepare_geometry(rig: Rig) -> None:
    """Renames meshes with the geo suffix and parents them under geo_grp."""
    processed_geo_list = []
    for obj in rig.mesh_xform_list:
        geo_name = obj
        # Add suffix if it doesn't already end with geo_sfx
        if not obj.endswith(NAMING.geo_sfx):
            geo_name = cmds.rename(obj, obj + NAMING.geo_sfx)

        cmds.parent(geo_name, rig.geo_grp)
        processed_geo_list.append(geo_name)

    rig.mesh_xform_list = processed_geo_list


def create_joints(rig: Rig, make_root: bool = True) -> None:
    """Creates joints at mesh pivots and binds each mesh to its joint."""
    rig.joints_list = []
    root_joint = None

    if make_root:
        cmds.select(clear=True)
        root_joint = cmds.joint(n=NAMING.root_jnt, sc=False)
        cmds.parent(root_joint, rig.jnt_grp)
        rig.root_jnt = root_joint

    for obj in rig.mesh_xform_list:
        cmds.select(clear=True)

        # Create joint at object pivot
        pivot_pos = cmds.xform(obj, query=True, pivots=True, worldSpace=True)
        jnt_name = obj.replace(NAMING.geo_sfx, NAMING.jnt_sfx)
        jnt = cmds.joint(n=jnt_name, sc=False, position=pivot_pos[:3])

        if root_joint:
            jnt = cmds.parent(jnt, root_joint)[0]
        else:
            jnt = cmds.parent(jnt, rig.jnt_grp)[0]

        # Skin mesh to joint
        cmds.skinCluster(obj, jnt, toSelectedBones=True)
        rig.joints_list.append(jnt)


def create_controls(rig: Rig, config: RigConfig) -> None:
    """Generates offset groups and control curves for each joint"""
    rig.offset_control_list = []
    rig.ctrl_list = []

    cmds.select(clear=True)

    # TODO create root control

    for jnt in rig.joints_list:
        ctrl_name = jnt.replace(NAMING.jnt_sfx, NAMING.ctrl_sfx)
        off_name = jnt.replace(NAMING.jnt_sfx, NAMING.off_sfx)

        # Create offset group and match joint position
        offset_grp = cmds.group(em=True, n=off_name)
        rig.offset_control_list.append(offset_grp)

        jnt_pos = cmds.xform(jnt, query=True, translation=True, worldSpace=True)
        cmds.xform(offset_grp, translation=jnt_pos, worldSpace=True)

        # Create control curve and parent under offset group
        ctrl = controls.draw_curve(curve=config.ctrl_shape, thickness=config.ctrl_thickness, size=config.ctrl_size)
        controls.apply_color(ctrl, config.ctrl_color)
        ctrl = cmds.rename(ctrl, ctrl_name)

        cmds.parent(ctrl, offset_grp)
        cmds.xform(ctrl, translation=[0, 0, 0], rotation=[0, 0, 0])
        cmds.parent(offset_grp, rig.ctrl_grp)

        # Constrain joint to control
        cmds.parentConstraint(ctrl, jnt, mo=True)
        rig.ctrl_list.append(ctrl)


def _make_display_layer(name: str, members: str, **kwargs) -> str:
    """Recreates a display layer by name and adds members to it."""
    if cmds.objExists(name):
        cmds.delete(name)
    layer = cmds.createDisplayLayer(name=name, number=1, empty=True)
    cmds.editDisplayLayerMembers(layer, members, **kwargs)
    return layer


def setup_display_layers(rig: Rig) -> None:
    """Creates display layers for geometry, controls, and joints."""
    # Geometry: reference mode so geo cannot be selected in the viewport
    geo_layer = _make_display_layer(NAMING.geo_layer, rig.geo_grp)
    cmds.setAttr(f"{geo_layer}.displayType", 2)

    # Controls: visible
    _make_display_layer(NAMING.ctrl_layer, rig.ctrl_grp, noRecurse=True)

    # Joints: hidden by default, reference mode
    jnt_layer = _make_display_layer(NAMING.jnt_layer, rig.jnt_grp)
    cmds.setAttr(f"{jnt_layer}.displayType", 2)
    cmds.setAttr(f"{jnt_layer}.visibility", 0)


def clear_rig(rig: Rig) -> None:
    # TODO Implement clear rig - delete joints and controls, reset constraints, ungroup objects
    pass