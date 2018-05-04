'''HSBuild_RIG'''
import pymel.core as pymel

from python.libs import build_ctrls
from python.libs import general_utils
from python.libs import joint_utils
from python.libs import lib_network, naming_utils, virtual_classes

reload(lib_network)
reload(build_ctrls)
reload(joint_utils)
reload(naming_utils)
reload(general_utils)
reload(virtual_classes)

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def delete_rig():
    for net in pymel.ls(type='network'):
        try:
            pymel.delete(net.getCtrlRig())

        except Exception as ex:
            log.warning(ex)
            pass

    pymel.delete(pymel.ls(type='network'))

    for jnt in pymel.ls():
        if jnt.hasAttr('_class'):
            jnt.deleteAttr('_class')


def build_ikfk_limb(jnts, net=None, fk_size=2.0, fk_shape='Circle', ik_size=1.0, ik_shape='Cube01', pole_size=1.0, pole_shape='Cube01', ikfk_size=1.0, ikfk_shape='IKFK', region='', side=''):

    """
    :param jnts:
    :param net:
    :param fk_size:
    :param fk_shape:
    :param ik_size:
    :param ik_shape:
    :param pole_size:
    :param pole_shape:
    :param ikfk_size:
    :param ikfk_shape:
    :param region:
    :param side:
    :return:
    """

    #NET NODE
    if not net:
        net = virtual_classes.LimbNode()
        naming_utils.add_tags(net, tags={'Region': region, 'Side': side})
        naming_utils.add_message_attr(net, attributes=['JOINTS',
                                                       'IK_JOINTS',
                                                       'FK_JOINTS',
                                                       'IK_CTRL',
                                                       'FK_CTRL',
                                                       'POLE',
                                                       'ANNO',
                                                       'IK_HANDLE',
                                                       'SWITCH',
                                                       'ORIENTCONSTRAINT',
                                                       'POINTCONSTRAINT'])

    assert isinstance(net, virtual_classes.LimbNode)

    jnts = joint_utils.get_joint_chain(jnts)

    # Attach virtual class
    for idx, jnt in enumerate(jnts):
        try:
            jnts[idx] = virtual_classes.attach_class(jnt, net=net)
            jnt.message.connect(net.jntsAttr[idx])
            jnts[idx].add_network_tag()

        except Exception as ex:
            log.warning(ex)

    # IK FK
    fk_jnts, ik_jnts = joint_utils.build_ik_fk_joints(jnts, net)

    log.info('Building IK FK:')

    # FK CTRLS
    for idx, fk_jnt in enumerate(fk_jnts):
        ctrl_name = naming_utils.concatenate([net.Side.get(),
                                              net.jnts[idx].name_info.base_name,
                                              net.jnts[idx].name_info.joint_name,
                                              net.jnts[idx].name_info.index,
                                              'FK',
                                              'CTRL'])
        ctrl_tags = {'Type': 'CTRL', 'Utility': 'FK'}
        log.info('Building FK CTRL for : {}'.format(fk_jnt))
        ctrl = build_ctrls.create_ctrl(jnt=fk_jnt, name=ctrl_name, network=net, tags=ctrl_tags, size=fk_size, shape=fk_shape, axis='z')
        ctrl.message.connect(net.FK_CTRLS[idx])

    for idx, fk in enumerate(net.fk_ctrls):
        if idx > 0:
            fk.setParent(net.fk_ctrls[idx-1])

    for fk, jnt in zip(net.fk_ctrls, net.fk_jnts):
        parent_constraint = pymel.parentConstraint(fk, jnt)
        naming_utils.add_tags(parent_constraint, tags={'Network': net.name()})

    # Create offsets
    joint_utils.create_offset_groups([x for x in net.fk_ctrls], net)

    # IK CTRLS
    ikhandle_name = naming_utils.concatenate([net.jnts[2].name_info.side,
                                              net.jnts[2].name_info.base_name,
                                              net.jnts[2].name_info.joint_name,
                                              net.jnts[2].name_info.index, 'IK', 'HDL'])

    ikhandle = pymel.ikHandle(startJoint=net.ik_jnts[0], endEffector=net.ik_jnts[2], name=ikhandle_name)[0]
    ikhandle.message.connect(net.ikHandlesAttr[0])
    log.info('Building IK CTRLS: {}, {}'.format(ikhandle_name, type(ikhandle)))
    ik_offset = joint_utils.create_offset_groups(ikhandle, net)

    # Ik Ctrl
    ik_ctrl_name = naming_utils.concatenate([net.Side.get(),
                                             jnts[2].name_info.base_name,
                                             jnts[2].name_info.joint_name,
                                             'IK', 'CTRL'])
    ikctrl = build_ctrls.create_ctrl(name=ik_ctrl_name, network=net, shape=ik_shape, size=ik_size, tags={'Network': net.name(), 'Type': 'CTRL', 'Utility': 'IK'}, axis='Y')
    ikctrl.setTranslation(net.jnts[2].getTranslation(worldSpace=True), worldSpace=True)
    virtual_classes.attach_class(ikctrl, net)
    # pymel.orientConstraint([ikctrl, net.ik_jnts[2]], maintainOffset=True)

    # IK Loc
    ik_loc = pymel.spaceLocator()
    ik_loc.message.connect(net.IK_SNAP_LOC[0])
    naming_utils.add_tags(ik_loc, {'Network': net.name()})
    pymel.pointConstraint([net.jnts[2], ik_loc])
    pymel.orientConstraint([net.jnts[2], ik_loc], maintainOffset=True)

    ikctrl.message.connect(net.ikCtrlsAttr[0])
    pymel.pointConstraint(ikctrl, ik_offset)
    orient_constraint = pymel.orientConstraint(ikctrl, ik_offset, maintainOffset=True)
    naming_utils.add_tags(orient_constraint, {'Network': net.name()})
    joint_utils.create_offset_groups(ikctrl, net)

    # POLE Ctrl
    pos, rot = joint_utils.get_pole_position(fk_jnts)
    pole_name = naming_utils.concatenate([net.jnts[2].name_info.base_name,
                                          net.jnts[2].name_info.joint_name,
                                          net.jnts[2].name_info.side,
                                          'Pole',
                                          'CTRL'])
    pole_tags = {'Network': net.name(), 'Type': 'CTRL', 'Utility': 'IK'}
    pole = build_ctrls.create_ctrl(name=pole_name, jnt=ik_jnts[2], network=net, shape=pole_shape, size=pole_size, tags=pole_tags)
    pole.setTranslation(pos, space='world')
    pole.setRotation(rot)
    pole.message.connect(net.POLE[0])
    joint_utils.create_offset_groups(pole, name='Offset', net=net)
    pymel.poleVectorConstraint(pole, ikhandle)

    # Annotation. Line between pole and mid ik_jnts joint
    anno_name = naming_utils.concatenate([net.jnts[1].name_info.base_name, net.jnts[1].name_info.joint_name])
    annotation, anno_parent, locator, point_constraint_a, point_constraint_b = general_utils.build_annotation(pole, net.ik_jnts[1], net=net, name=anno_name)
    for grp in [annotation, anno_parent, locator, point_constraint_a]:
        naming_utils.add_tags(grp, tags={'Network': net.name()})
    annotation.message.connect(net.ANNO[0])
    anno_parent.message.connect(net.ANNO[1])

    # Switch CTRL
    switch_name = naming_utils.concatenate([net.jnts[2].name_info.base_name, net.jnts[2].name_info.joint_name, 'IKFK', 'CTRL'])
    switch_tags = {'Network': net.name(), 'Type': 'Switch', 'Utility': 'IKFK'}
    switch = build_ctrls.create_ctrl(jnt=net.jnts[2], name=switch_name, network=net, tags=switch_tags, shape=ikfk_shape, size=ikfk_size)
    switch.message.connect(net.SWITCH[0])
    pymel.parentConstraint(jnts[2], switch)

    # plusMinusAverage
    switch_util = general_utils.make_switch_utility(switch, tags={'Network': net.name(), 'Type': 'Switch', 'Utility': 'IKFK'})
    for orient, point in zip(net.ORIENTCONSTRAINT.listConnections(), net.POINTCONSTRAINT.listConnections()):
        switch_util.output1D.connect(point.w0)
        switch_util.output1D.connect(orient.w0)
    for orient, point in zip(net.ORIENTCONSTRAINT.listConnections(), net.POINTCONSTRAINT.listConnections()):
        switch.IKFK.connect(point.w1)
        switch.IKFK.connect(orient.w1)

    # FK Vis Condition
    fk_vis_condition = general_utils.make_condition(secondTerm=1.0)
    naming_utils.add_tags(fk_vis_condition, tags={'Network': net.name()})
    switch_util.output1D.connect(fk_vis_condition.firstTerm)
    for fk_ctrl, fk_joint in zip(net.fk_ctrls, net.fk_jnts):
        fk_vis_condition.outColorR.connect(fk_ctrl.visibility)
        fk_vis_condition.outColorR.connect(fk_joint.visibility)

    # IK Vis Condition
    ik_vis_condition = general_utils.make_condition(secondTerm=1.0)
    naming_utils.add_tags(ik_vis_condition, tags={'Network': net.name()})
    switch.IKFK.connect(ik_vis_condition.firstTerm)

    for ik_ctrl, pole, annotation in zip(net.ik_ctrls, net.POLE.connections(), net.ANNO.connections()):
        ik_vis_condition.outColorR.connect(ik_ctrl.visibility)
        ik_vis_condition.outColorR.connect(pole.visibility)
        ik_vis_condition.outColorR.connect(annotation.visibility)

    for ik_jnt in net.ik_jnts:
        ik_vis_condition.outColorR.connect(ik_jnt.visibility)

    log.info('Grouping CTRLS')
    # LimbGRP
    limb_grp_name = naming_utils.concatenate([net.side, net.region, 'GRP'])
    limb_grp = pymel.group(empty=True, name=limb_grp_name)
    limb_grp.setMatrix(net.jnts[0].getMatrix(worldSpace=True), worldSpace=True)
    limb_grp = virtual_classes.attach_class(limb_grp, net)
    naming_utils.add_tags(limb_grp, {'Network': net.name()})

    # Group
    for node in net.getCtrlRig():
        root = joint_utils.get_root(node)

        if root and root != limb_grp and root not in net.jnts and root != 'JNT':  # Todo: Simplify this logic
            print root
            root.setParent(limb_grp)


def build_spine(jnts, net=None):
    assert isinstance(net, virtual_classes.SplineIKNet)

    info = naming_utils.ItemInfo(jnts[0])
    new_name = naming_utils.concatenate([info.side,
                                         info.base_name,
                                         info.joint_name,
                                         info.index,
                                         ])

    for idx, jnt in enumerate(jnts):
        virtual_classes.attach_class(jnt, net)

    points = [x.getTranslation(worldSpace=True) for x in jnts]
    spine_curve = pymel.curve(p=points, degree=1)
    naming_utils.add_tags(spine_curve, {'Network': net.name()})

    ikhandle, effector = pymel.ikHandle(startJoint=jnts[0],
                                        endEffector=jnts[-1],
                                        solver='ikSplineSolver',
                                        createCurve=False,
                                        curve=spine_curve,
                                        rootOnCurve=True,
                                        parentCurve=False,
                                        rootTwistMode=False)
    naming_utils.add_tags(ikhandle, {'Network': net.name()})
    naming_utils.add_tags(effector, {'Network': net.name()})

    for i in spine_curve.cv.indices():
        cluster, cluster_handle = pymel.cluster(spine_curve.cv[i])
        cluster_handle.message.connect(net.CLUSTER_HANDLE[i])
        virtual_classes.attach_class(cluster_handle, net=net)
        naming_utils.add_tags(cluster_handle, {'Network': net.name()})
        naming_utils.add_tags(cluster, {'Network': net.name()})
        offset = joint_utils.create_offset_groups(cluster_handle)[0]
        offset.setPivots(cluster_handle.getRotatePivot())
        naming_utils.add_tags(offset, {'Network': net.name()})

    naming_utils.add_tags(ikhandle, {'Network': net.name()})
    ikhandle.message.connect(net.IK_HANDLE[0])

    def make_ctrl(jnt, children=None, shape='Cube01'):
        """

        :param jnt:
        :param children: list of clusters to parent to ctrl
        :param shape:
        :return:
        """
        name = naming_utils.concatenate([jnt.name_info.joint_name,
                                         jnt.name_info.index,
                                         'CTRL'])
        ctrl = build_ctrls.create_ctrl(name=name, axis='y', shape=shape, network=net)
        ctrl.setTranslation(jnt.getTranslation(worldSpace=True))

        for cluster in children:
            cluster.getRoot().setParent(ctrl)
        return ctrl

    # Pelvis CTRL
    pelvis_ctrl = make_ctrl(net.jnts[1], children=net.clusters[0:2], shape='Oval')
    pelvis_ctrl.message.connect(net.ikCtrlsAttr[0])

    # Mid CTRL
    mid_ctrl = make_ctrl(net.jnts[2], children=net.clusters[2:3], shape='Oval')
    mid_ctrl.message.connect(net.ikCtrlsAttr[1])

    # Chest CTRL
    chest_ctrl = make_ctrl(net.jnts[3], children=net.clusters[3:5], shape='Chest')
    chest_ctrl.message.connect(net.ikCtrlsAttr[2])

    # COG
    cog = build_ctrls.create_ctrl(jnt=net.jnts[1], network=net, shape='Circle', size=5)
    chest_ctrl.message.connect(net.ikCtrlsAttr[3])

    chest_ctrl.setParent(mid_ctrl)
    mid_ctrl.setParent(cog)
    pelvis_ctrl.setParent(cog)


    # Ik Spline Twist
    net.ik_handles[0].dTwistControlEnable.set(1)
    net.ik_handles[0].dWorldUpType.set(4)
    net.ik_handles[0].dForwardAxis.set(1)

    net.ik_ctrls[0].worldMatrix[0].connect(net.ik_handles[0].dWorldUpMatrix)
    net.ik_ctrls[2].worldMatrix[0].connect(net.ik_handles[0].dWorldUpMatrixEnd)

    net.ik_handles[0].dWorldUpAxis.set(3)

    net.ik_handles[0].dWorldUpVector.set(0, 0, 1)
    net.ik_handles[0].dWorldUpVectorEnd.set(0, 0, 1)




    # pymel.parentConstraint([mid_ctrl.object, chest_ctrl.object], skipRotate=('x', 'y', 'z'), maintainOffset=True)

    # pymel.mel.eval('ikHandle -sol ikSplineSolver -ccv false;')


def build_reverse_foot_rig(net=None):

    assert isinstance(net, virtual_classes.LimbNode)
    #Set attrs
    foot_ik_ctrl = net.ik_ctrls[0]
    foot_ik_ctrl.addAttr('Ankle_Roll', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Ball_Roll', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Ball_Twist', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Toe_Roll', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Toe_Twist', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Toe_Wiggle', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Left_Bank', at='float', keyable=True)
    foot_ik_ctrl.addAttr('Right_Bank', at='float', keyable=True)

    # Build Foot IK Handles
    ikhandle_name = naming_utils.concatenate([net.jnts[3].name_info.side,
                                              net.jnts[3].name_info.base_name,
                                              net.jnts[3].name_info.joint_name,
                                              net.jnts[3].name_info.index, 'IK', 'HDL'])
    ikhandle_a = pymel.ikHandle(startJoint=net.ik_jnts[2], endEffector=net.ik_jnts[3], name=ikhandle_name)[0]
    ikhandle_a.message.connect(net.IK_HANDLE[1])
    ikhandle_name = naming_utils.concatenate([net.jnts[4].name_info.side,
                                              net.jnts[4].name_info.base_name,
                                              net.jnts[4].name_info.joint_name,
                                              net.jnts[4].name_info.index, 'IK', 'HDL'])
    ikhandle_b = pymel.ikHandle(startJoint=net.ik_jnts[3], endEffector=net.ik_jnts[4], name=ikhandle_name)[0]
    ikhandle_b.message.connect(net.IK_HANDLE[2])

    # Storing Ankle IK Handle parent for later.
    ankle_ik_grp = net.ik_handles[0].getParent()

    def build_grp(transform=None, children=None, name=None, net=None):
        grp_name = naming_utils.concatenate([net.side, net.region, name, 'GRP'])
        grp = pymel.group(empty=True, name=grp_name)
        grp.setMatrix(transform.getMatrix(worldSpace=True), worldSpace=True)
        pymel.makeIdentity(grp, apply=True)
        for child in children:
            child.setParent(grp)
        virtual_classes.attach_class(grp, net=net)
        return grp

    # Ball Roll
    ball_roll_grp = build_grp(name='BallRoll', transform=net.jnts[3], children=[net.ik_handles[0], net.ik_handles[1]], net=net)
    foot_ik_ctrl.Ball_Roll.connect(ball_roll_grp.rotateX)

    # Toe Wiggle
    toe_wiggle_grp = build_grp(name='ToeWiggle', transform=net.jnts[3], children=[net.ik_handles[2]], net=net)
    foot_ik_ctrl.Toe_Wiggle.connect(toe_wiggle_grp.rotateX)

    # Toe Pivot
    toe_roll_grp = build_grp(name='ToeRoll', transform=net.jnts[4], children=[ball_roll_grp, toe_wiggle_grp], net=net)
    foot_ik_ctrl.Toe_Roll.connect(toe_roll_grp.rotateX)
    foot_ik_ctrl.Toe_Twist.connect(toe_roll_grp.rotateY)

    # Ball Twist
    ball_twist_grp = build_grp(name='BallTwist', transform=net.jnts[3], children=[toe_roll_grp], net=net)
    foot_ik_ctrl.Ball_Twist.connect(ball_twist_grp.rotateY)

    # Left Bank
    left_bank_grp = build_grp(name='LeftBank', transform=net.jnts[3], children=[ball_twist_grp], net=net)
    foot_ik_ctrl.Left_Bank.connect(left_bank_grp.rotateZ)

    # Right Bank
    right_bank_grp = build_grp(name='RightBank', transform=net.jnts[3], children=[left_bank_grp], net=net)
    foot_ik_ctrl.Right_Bank.connect(right_bank_grp.rotateZ)

    # Ankle Roll
    ankle_roll_grp = build_grp(name='AnkleRoll', transform=net.jnts[2], children=[right_bank_grp], net=net)
    foot_ik_ctrl.Ankle_Roll.connect(ankle_roll_grp.rotateX)

    pymel.parent(ankle_roll_grp, ankle_ik_grp)


def build_clavicle(jnts, net=None):

    ctrl = build_ctrls.create_ctrl(jnt=jnts[0], network=net, shape='Circle')
    offset = joint_utils.create_offset_groups(ctrl, net=net)
    pymel.parentConstraint([ctrl, jnts[0]])
    print jnts, "CLAVICLE"


def build_humanoid_rig(mirror=True):

    jnt_dict = {}
    for jnt in pymel.ls(type='joint'):
        info = naming_utils.ItemInfo(jnt)
        key = naming_utils.concatenate([info.side, info.region])

        if key in jnt_dict:
            jnt_dict[key].append(jnt)
        elif info.region:
            jnt_dict[key] = [jnt]

    # Create Main
    main = virtual_classes.MainNode()

    # Create Network Nodes
    for key in jnt_dict.keys():
        info = naming_utils.ItemInfo(key)
        if info.region == 'Spine':
            net = virtual_classes.SplineIKNet()
            net.message.connect()
        else:
            net = virtual_classes.LimbNode()

        pymel.rename(net, naming_utils.concatenate([key, 'Net']))
        naming_utils.add_tags(net, tags={'Type': 'IKFK', 'Region': info.region, 'Side': info.side})

        # Connect Joints
        for idx, jnt in enumerate(joint_utils.get_joint_chain(jnt_dict[key])):
            jnt.message.connect(net.jntsAttr[idx])
            virtual_classes.attach_class(jnt, net)

    # Build Arms
    for net in pymel.ls(type=virtual_classes.LimbNode):
        if net.region == 'Arm':
            build_ikfk_limb(jnts=net.jnts, net=net, ik_shape='Cube01')
            pymel.orientConstraint([net.ik_ctrls[0], net.ik_jnts[2]], maintainOffset=True)

    # Build Legs
    for net in pymel.ls(type='network'):
        if net.region == 'Leg':
            build_ikfk_limb(jnts=net.jnts, net=net, ik_shape='FootCube01')  # todo: add support for mirrored joints
            build_reverse_foot_rig(net=net)

    # Build IK Spline
    for net in pymel.ls(type='network'):
        if net.region == 'Spine':
            build_spine(jnts=net.jnts, net=net)

    # Build Clavicle
    for net in pymel.ls(type='network'):
        if net.region == 'Clavicle':
            build_clavicle(jnts=net.jnts, net=net)






"""TEST CODE"""

if __name__ == '__main__':

    delete_rig()
    build_humanoid_rig()

    """Example"""
    # import pymel.core as pymel
    # from python.modules import build_rig
    # reload(build_rig)
    #
    # build_rig.build_ikfk_limb(jnts=pymel.selected(),
    #                           ik_shape='Cube01',
    #                           ik_size=0.3,
    #                           fk_size=0.3,
    #                           pole_size=0.3,
    #                           ikfk_size=0.3)











