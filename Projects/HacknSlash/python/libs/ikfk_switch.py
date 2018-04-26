import pymel.core as pymel

from python.libs import joint_utils, virtual_classes

reload(joint_utils)
reload(virtual_classes)


def to_ik(net):
    switch = net.SWITCH.connections()[0]

    # Get Switch weight
    if switch.IKFK.get() == 1:
        pole = net.POLE.connections()[0]

        distance = joint_utils.get_distance(net.ik_jnts[0],
                                            net.ik_jnts[1])

        pos, rot = joint_utils.get_pole_position(net.IK_JOINTS.connections(), pole_dist=distance * 0.5)
        pole.setTranslation(pos, space='world')
        pole.setRotation(rot, space='world')

        return

    # Match FK POS
    ik_snap_target = net.IK_SNAP_LOC.connections()[0].getMatrix(worldSpace=True)

    ik_ctrl = net.ik_ctrls[0]
    ik_ctrl.setMatrix(ik_snap_target, worldSpace=True)

    # Set Pole POS
    distance = joint_utils.get_distance(net.FK_JOINTS.connections()[0],
                                        net.FK_JOINTS.connections()[1])

    pole = net.POLE.connections()[0]
    pos, rot = joint_utils.get_pole_position(net.FK_JOINTS.connections(), pole_dist=distance * 0.5)
    pole.setTranslation(pos, space='world')
    pole.setRotation(rot, space='world')

    # Set Constraint Weight
    switch.IKFK.set(1)


def to_fk(net):

    # Set Constraint Weight
    switch = net.SWITCH.connections()[0]

    # Get Switch weight
    if switch.IKFK.get() == 0:
        return

    jnt_matrices = [jnt.getMatrix(worldSpace=True) for jnt in net.jnts]

    switch.IKFK.set(0)

    for ctrl, matrix in zip(net.fk_ctrls, jnt_matrices):
        ctrl.setMatrix(matrix, worldSpace=True)


def switch_to_ik():
    for sel in pymel.selected():
        to_ik(sel.network)


def switch_to_fk():
    for sel in pymel.selected():
        to_fk(sel.network)



