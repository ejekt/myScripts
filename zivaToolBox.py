def zAttach(boneMeshName, muscleGeo, iGrow, endPoint):
	cmds.select(cl=1)
	cmds.select(muscleGeo)
	# create fiber to get end points
	z = cmds.ziva(f=1)[0]
	a = cmds.getAttr(z + '.endPoints')
	cmds.delete(z)
	pointcv = []
	# collect end points
	for g in range(len(a)):
		if a[g] == 0 or a[g] == 1:
			pointcv.append(g)
	cmds.select(cl=1)
	if endPoint == 'top':
		print 'endpoint', muscleGeo, '.vtx[', str(pointcv[1]), ']'
		cmds.select(muscleGeo + '.vtx[' + str(pointcv[1]) + ']')
		for s in range(iGrow):
			cmds.GrowPolygonSelectionRegion()
		cmds.select(boneMeshName, add=1)
		cmds.ziva(a=1)
	if endPoint == 'bottom':
		print 'endpoint', muscleGeo, '.vtx[', str(pointcv[0]), ']'
		cmds.select(muscleGeo + '.vtx[' + str(pointcv[0]) + ']')
		for s in range(iGrow):
			cmds.GrowPolygonSelectionRegion()
		cmds.select(boneMeshName, add=1)
		cmds.ziva(a=1)
	return True


zSetupDict = {'fermur001_L_IN': [
	{'bottom': ["backLeg001_L_02_SIM", "backLeg001_L_03_SIM", "backLeg001_L_05_SIM", "backLeg001_L_06_SIM",
				"backLeg001_L_09_SIM", "backLeg001_L_012_SIM", "backLeg001_L_013_SIM", "backLeg001_L_01_SIM",
				"backLeg001_L_02_SIM", ]},
	{'top': ["backLeg001_L_05_SIM", "backLeg001_L_06_SIM", "backLeg001_L_08_SIM", "backLeg001_L_07_SIM"]}, ],

	'pelvis001_C_IN': [
		{'top': ["backLeg001_L_02_SIM", "backLeg001_L_01_SIM", "backLeg001_L_03_SIM", "backLeg001_L_013_SIM",
				 "backLeg001_R_016_SIM"]},
		{'bottom': ["backLeg001_L_08_SIM", "backLeg001_L_09_SIM", "backLeg001_L_09_SIM", "backLeg001_R_04_SIM",
					"backLeg001_R_05_SIM", "backLeg001_R_06_SIM", "backLeg001_R_07_SIM", "backLeg001_R_017_SIM"]}, ],

	'fermur001_R_IN': [
		{'bottom': ["backLeg001_R_01_SIM", "backLeg001_R_08_SIM", "backLeg001_R_07_SIM", "backLeg001_R_06_SIM",
					"backLeg001_R_017_SIM", "backLeg001_R_016_SIM"]},
		{'top': ["backLeg001_R_01_SIM", "backLeg001_R_04_SIM", "backLeg001_R_05_SIM", ]}, ]
}

for bone in zSetupDict.keys():
	print bone
	for items in zSetupDict[bone]:
		for endPoint, muscles in items.iteritems():
			print endPoint, muscles
			for msc in muscles:
				mc.select(msc, r=1)
				makeZivaMuscle()
				try:
					zAttach(bone, msc, 2, endPoint)
				except:
					pass

import maya.cmds as cmds
#######################

def zAttach(boneMeshName, iGrow, endPoint):
	sel = cmds.ls(sl=1)
	cmds.select(cl=1)
	for obj in sel:
		cmds.select(obj)
		# make muscle
		if not makeZivaMuscle():
			print "couldn't make muscle"
			return False
		# create fiber to get end points
		z = cmds.ziva(f=1)[0]
		a = cmds.getAttr(z + '.endPoints')
		cmds.delete(z)
		pointcv = []
		# collect end points
		for g in range(len(a)):
			if a[g] == 0 or a[g] == 1:
				pointcv.append(g)
		cmds.select(cl=1)
		if endPoint == 'top':
			print 'endpoint', obj, '.vtx[', str(pointcv[1]), ']'
			cmds.select(obj + '.vtx[' + str(pointcv[1]) + ']')
			for s in range(iGrow):
				cmds.GrowPolygonSelectionRegion()
			cmds.select(boneMeshName, add=1)
			cmds.ziva(a=1)
	if endPoint == 'bottom':
		print 'endpoint', obj, '.vtx[', str(pointcv[0]), ']'
		cmds.select(obj + '.vtx[' + str(pointcv[0]) + ']')
		for s in range(iGrow):
			cmds.GrowPolygonSelectionRegion()
		cmds.select(boneMeshName, add=1)
		cmds.ziva(a=1)
	return True



def makeZivaMuscle():
	# need muscle selected
	if len(mc.ls(sl=1)) > 1:
		print 'Select only one mesh to make into muscle'
		return False
	simGeo = mc.ls(sl=1)[0]
	# try creating muscle, if fails average vtx and try again
	mc.select(simGeo, r=1)
	try:
		zNodes = mc.ziva(t=1)
	# print '\t! created zNodes on ', zNodes

	except:
		# print '\t!', simGeo, 'ziva muscle failed. Averaging vtx and trying again'
		mc.polyAverageVertex(simGeo)
		try:
			zNodes = mc.ziva(t=1)
			print '\t! created zMuscle on ', simGeo
		except:
			return False
	zGeo = zNodes[0]
	zTissue = zNodes[1]
	zTet = zNodes[2]
	zMaterial = zNodes[3]

	return zNodes

# if geo:
# 	name = geo.replace('SIM', 'z')
# 	zGeo = mc.rename(zGeo,name+'Geo')
# 	zTissue= mc.rename(zTissue, name + 'Tissue')
# 	zMaterial = mc.rename(zMaterial, name + 'Mat')

###########33 from the web
def Attach(SkeletonMeshName, GROW):
	n = cmds.ls(sl=1)
	mesh = SkeletonMeshName
	cmds.select(cl=1)
	for l in n:
		cmds.select(l)
		cmds.ziva(t=1)
		z = cmds.ziva(f=1)[0]
		a = cmds.getAttr(z + '.endPoints')
		cmds.delete(z)
		pointcv = []
		for g in range(len(a)):

			if a[g] == 0 or a[g] == 1:
				pointcv.append(g)
		cmds.select(cl=1)
		cmds.select(l + '.vtx[' + str(pointcv[0]) + ']', l + '.vtx[' + str(pointcv[1]) + ']')
		for s in range(GROW):
			cmds.GrowPolygonSelectionRegion()
		cmds.select(SkeletonMeshName, add=1)
		cmds.ziva(a=1)


def LOA(SkeletonMeshName):
	sel = cmds.ls(sl=1)
	zBoneMesh = SkeletonMeshName
	zBoneShape = cmds.listRelatives(zBoneMesh, s=1)[0]
	cmds.select(cl=1)
	for l in sel:
		cmds.select(l)
		z = cmds.ziva(f=1)[0]
		a = cmds.getAttr(z + '.endPoints')
		pointcv = []
		for g in range(len(a)):

			if a[g] == 0 or a[g] == 1:
				pointcv.append(g)
		poscv1 = cmds.pointPosition(l + '.vtx[' + str(pointcv[0]) + ']')
		poscv2 = cmds.pointPosition(l + '.vtx[' + str(pointcv[1]) + ']')
		curves = cmds.curve(n=l + '_loa', d=1, p=[(poscv1[0], poscv1[1], poscv1[2]), (poscv2[0], poscv2[1], poscv2[2])],
							k=[0, 1])

		cmds.select(l, curves)
		cmds.ziva(loa=1)

		joints = []
		for l in range(2):
			cmds.select(cl=1)
			pos = cmds.pointPosition(curves + '.cv[' + str(l) + ']')
			Joint = cmds.joint(p=pos, n=curves + str(l))
			joints.append(Joint)
			closest = cmds.createNode('closestPointOnMesh')
			cmds.connectAttr(zBoneShape + '.worldMatrix[0]', closest + '.inputMatrix')
			cmds.connectAttr(zBoneShape + '.worldMesh[0]', closest + '.inMesh')
			cmds.setAttr(closest + '.inPosition', pos[0], pos[1], pos[2], type='double3')

			follicle = cmds.createNode('follicle')
			fol_tNode = cmds.listRelatives(follicle, p=1)[0]
			cmds.connectAttr(zBoneShape + '.worldMatrix[0]', follicle + '.inputWorldMatrix')
			cmds.connectAttr(zBoneShape + '.worldMesh[0]', follicle + '.inputMesh')
			cmds.connectAttr(closest + '.parameterU', follicle + '.parameterU')
			cmds.connectAttr(closest + '.parameterV', follicle + '.parameterV')

			cmds.connectAttr(follicle + '.outRotate', fol_tNode + '.rotate')
			cmds.connectAttr(follicle + '.outTranslate', fol_tNode + '.translate')
			cmds.parent(Joint, fol_tNode)
			cmds.delete(closest)
		cmds.select(joints, curves)
		cmds.SmoothBindSkin()