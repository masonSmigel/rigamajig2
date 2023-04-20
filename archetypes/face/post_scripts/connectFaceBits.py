"""
Connect some miscelanous face bits
"""

import maya.cmds as cmds 
from rigamajig2.maya import transform 



from rigamajig2.maya import attr 
# blend the cheekPuffs 
transform.blendedOffsetParentMatrix("muppet_bind", "jaw_bind", "cheekPuff_l_orig", mo=True, blend=0.5)
transform.blendedOffsetParentMatrix("muppet_bind", "jaw_bind", "cheekPuff_r_orig", mo=True, blend=0.5)


# move the corner pinning stuff to the mouth corners 

for side in "lr": 
    lipControl = "lips_{}_corner".format(side)
    jawControl = "jawCorner_{}".format(side)
    attr.addSeparator(lipControl, "----")
    attr.moveAttribute("pin", source=jawControl, target=lipControl)
    


# setup the nostril flare 
for side in 'lr': 
    
    nostrilFlare = "nostrilFlare_{}".format(side)
    nostril = "nostril_{}".format(side)
    
    shapes = cmds.listRelatives(nostrilFlare, s=True)
    if shapes:
        cmds.delete(shapes)
    
    attr.addSeparator(nostril, "----" )
    flareAttr = attr.createAttr(nostril, "flare", "float", value=0)
    
    cmds.connectAttr(flareAttr, "{}.tx".format(nostrilFlare))
    attr.lock(nostrilFlare, attr.TRANSFORMS)
    
# setup the nose follow. This will keep the nose following a little bit with the upper lip 
offset = cmds.createNode("transform", name="noseBase_follow_trs_offset", parent="nose_spaces")
noseFollowTrs = cmds.createNode("transform", name="noseBase_follow_trs", parent=offset)
transform.matchTransform("noseBase", offset)
transform.matchRotate("lips_c_upper_0_bind", offset)


for attr in ['tx', 'ty', 'tz']: 
    cmds.connectAttr("{}.{}".format("lips_c_upper_0_bind", attr),"{}.{}".format(noseFollowTrs, attr))


transform.blendedOffsetParentMatrix('noseBase_orig', noseFollowTrs, 'noseBase_trs', mo=True, t=True, r=False, s=False, sh=False, blend=0.1)
transform.blendedOffsetParentMatrix('noseBase_orig', 'lips_bind', offset, mo=True, t=True, r=False, s=False, sh=False, blend=0.1)