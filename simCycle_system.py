import random
import maya.cmds as mc
import maya
import RigToolbox
import CfxToolbox
from CfxToolbox import Utils
from CfxToolbox.Utils import Defaults
import CfxToolbox.Utils.Dynamics as Dynamics
import CfxToolbox.Core.BuilderUtils as bu
from CfxToolbox.Utils import NCloth
import maya.mel as mel
import CfxToolbox
from CfxToolbox.Utils import Misc

#Misc.patchFromFaces(faces=[], patchName='test')


variantDict = { '1': 'red',
				'2': 'lime',
				'3': 'green',
				'4': 'lightBlue',
				'5': 'bronze',
				'6': 'purple',
				'7': 'orange',
				'8': 'brown',
				'9': 'teal',
				'10':'magenta',
				'11':'white',
				'12':'black',
				'13':'gold',
				'14':'lightGreen'
}


def createNConstraints(source, target, constraintType='slideOnSurface', name=None):
	"""Creates nConstraint between meshes.

	:param str source: Driven mesh name.
	:param str target: Driver mesh name.
	:param str constraintType: Which constraint type want to create.
	:param str name: Name for the constraint.
	:return str: Created constraint.
	"""
	mc.select(source, target)

	if constraintType == 'slideOnSurface':
		# MEL syntax: createNConstraint( string $constraintType, int $createSet )
		nConstShape = mel.eval("createNConstraint slideOnSurface 0")
		nConst = mc.listRelatives(nConstShape, parent=True)[0]
		nConst = mc.rename(nConst, name)
		nConstShape = mc.listRelatives(nConst, s=True)[0]
		# default settings
		mc.setAttr(nConstShape+'.constraintMethod', 2)
		mc.select(cl=True)
		return nConstShape

	if constraintType == 'componentToComponent':
	# MEL syntax: createNConstraint( string $constraintType, int $createSet )
		nConstShape = mel.eval("createNConstraint pointToPoint 0")
		nConst = mc.listRelatives(nConstShape, parent=True)
		if name:
			nConst = mc.rename(nConst,
			name.replace(name.split('_')[-1], 'C2C'))
		else:
			nConst = mc.rename(nConst,
			source.replace(source.split('_')[-1], 'C2C'))
		nConstShape = mc.listRelatives(nConst, s=True)[0]
		mc.parent(nConst, Defaults.Groups.cfxNConstraints)
		# default settings
		mc.setAttr(nConstShape+'.connectionMethod', 1) # withinMaxDistance
		mc.setAttr(nConstShape + '.maxDistance', 0.05)
		mc.select(cl=True)
		return nConstShape

	if constraintType == 'component':
	# MEL syntax: createNConstraint( string $constraintType, int $createSet )
		mel.eval("createComponentNConstraint 1 1 0 1")
		nConstShape = 'dynamicConstraintShape1'
		nConst = mc.listRelatives(nConstShape, parent=True)
		if name:
			nConst = mc.rename(nConst,
			name.replace(name.split('_')[-1], 'COM'))
		else:
			nConst = mc.rename(nConst,
			source.replace(source.split('_')[-1], 'COM'))
		nConstShape = mc.listRelatives(nConst, s=True)[0]
		mc.parent(nConst, Defaults.Groups.cfxNConstraints)
		# default settings
		# mc.setAttr(nConstShape+'.connectionMethod', 1) # withinMaxDistance
		# mc.setAttr(nConstShape + '.maxDistance', 0.05)
		mc.select(cl=True)
		return nConstShape

	if constraintType == 'pointToSurface':
	# MEL syntax: createNConstraint( string $constraintType, int $createSet )
  	nConstShape = mel.eval("createNConstraint pointToSurface 0")
		nConst = mc.listRelatives(nConstShape, parent=True)[0]
		nConst = mc.rename(nConst, name)
		if name:
			nConst = mc.rename(nConst,
			name.replace(name.split('_')[-1], 'P2S'))
		else:
			nConst = mc.rename(nConst,
			source.replace(source.split('_')[-1], 'P2S'))
		nConstShape = mc.listRelatives(nConst, s=True)[0]
		mc.select(cl=True)
		return nConstShape

	if constraintType == 'excludeCollide':
	# MEL syntax: createNConstraint collisionExclusion 0;
		mel.eval("createNConstraint collisionExclusion 0")
		nConstShape = 'dynamicConstraintShape1'
		if not mc.objExists(nConstShape):
			mc.warning('create constraint failed')
			return False
		nConst = mc.listRelatives(nConstShape, parent=True)
		if name:
			nConst = mc.rename(nConst,
			name.replace(name.split('_')[-1], 'EXC'))
		else:
			nConst = mc.rename(nConst,
			source.replace(source.split('_')[-1], 'EXC'))
		nConstShape = mc.listRelatives(nConst, s=True)[0]
		#mc.parent(nConst, Defaults.Groups.cfxNConstraints)
		# default settings
		mc.select(cl=True)
		return nConstShape
		# More constraint types come here..

	else:
		raise NotImplementedError



class WightArmy(object):

	def __init__(self, baseName, count=10, bFormation=True):

		self.baseName = baseName
		self.bFormation = bFormation
		self.bRunners = False
		self.bUseNewNucleus = False

		# vtx IDs
		self.baseVtxCount = 125
		self.wightCount = count

		self.nucleusGrp = self.baseName + '_nucleus_GRP'
		self.collider = 'drogonHi_COL_NRG'
		self.drogonMover = 'drogon_mover_LOC'
		self.nRigids = []
		self.simCycleNClothPreset = 'jason3'


		# animation variations
		self.animChoice = 'climb'
		self.dAnimCacheEnds = {
				'climb':	29,
				'climb2': 29,
				'climb3': 88,
				'slashing':	618,
				'running':	42,
				'grabbing': 238,
		}

		self.checkForExistingArmy()
		self.baseFile = '/data/share/rigging/rigSandbox/alonz/simCycle_baseShotFile.mb'
		# /data/share/rigging/rigSandbox/alonz/simCycle_baseShotFile.mb


	def createSimCycleArmy(self):
		# create:
		self.layers()
		self.makeWightPlatoon()
		self.turnArmyIntoCloth()
		self.create_outputNetwork()

		#self.duplicateDragonCollider()


	def makeWightPlatoon(self):
		baseName = self.baseName
		count = self.wightCount

		if mc.ls(baseName+'_*:*'):
			mc.error('baseName nameSpace already exists')

		# create the wights
		self.populateWights(baseName, count)
		maxFrame = self.dAnimCacheEnds[self.animChoice]
		self.randomizeWightCache(self.wightList, maxFrame)
		if not self.bFormation:
			self.randomizTranslation(self.wightList)

		# wight army cog
		nf = RigToolbox.Core.NodeUtils.nodeFactory()
		cCtrl = nf.createControl(description=baseName + 'Master', shape='gear', color='black',
								 shapeRotOffset=[0, 0, 0], size=count * 3)
		baseCtrlZro = cCtrl.grp
		self.baseCtrl = cCtrl.hook
		self.baseCtrlGrp = cCtrl.grp

		# constrain army to cog
		moveZros = [zro + ':c_moveWight_ZRO' for zro in self.wightList]
		for zro in moveZros:
			mc.parentConstraint(self.baseCtrl, zro, mo=1)

		# combine the wights
		if self.wightCount > 1:
			combinedName = 'combined_' + baseName + '_wightArmy'
			balloonMen = [man + ':balloonMan' for man in self.wightList]
			self.combinedArmyMesh = self.unitePolys(balloonMen, combinedName)
		else:
			self.combinedArmyMesh = [man + ':balloonMan' for man in self.wightList][0]

		# organize
		wightTopGrps = [grp + ':wightGuy' for grp in self.wightList]
		self.allWightsGrp = mc.group(wightTopGrps, n=baseName + '_allGuys_GRP')
		self.topGrp = mc.group(self.allWightsGrp, n=baseName + '_top_GRP')
		mc.parent(self.baseCtrlGrp, self.topGrp)

		# clenaup
		RigToolbox.Core.AttributeUtils.lockAndHide(node=self.topGrp,
			attrs=['tx','ty','tz','rx','ry','rz','sx','sy','sz'],
			unlock=False, unhide=False, doNow=True,
			all=False, verbose=False)
		RigToolbox.Core.AttributeUtils.lockAndHide(node=self.baseCtrl,
			attrs=['rotationOrder','sx','sy','sz'],
			unlock=True, unhide=False, doNow=True,
                        all=False, verbose=False)
		mc.setAttr(self.baseCtrl+'.v', cb=True, l=0 )
		# custom attrs
		RigToolbox.Core.AttributeUtils.addAttr(node=self.baseCtrl, attrName='smallCtrlVis',
			attrType="long", default=1,
			min=0.0, max=1.0, lock=False, keyable=False, channelBox=True,
			attrNiceName=None, verbose=True)
		moveCtrls = [c + ':c_moveWight_CTRL' for c in self.wightList]
		for c in moveCtrls:
			mc.connectAttr(self.baseCtrl+'.smallCtrlVis', c+'.v', f=1)
		# connect all the anim cache nodes to a baseCtrl attr
		RigToolbox.Core.AttributeUtils.addAttr(node=self.baseCtrl, attrName='animCache',
			attrType="bool", default=True,
			lock=False, keyable=False, channelBox=True,
			attrNiceName=None, verbose=True)
		animCacheNode = self.animChoice + 'Cache1'
		animCacheNodes = [c+':'+animCacheNode for c in self.wightList]
		for a in animCacheNodes:
			mc.connectAttr(self.baseCtrl+'.animCache', a+'.enable', f=1)
		# anim speed attr
		RigToolbox.Core.AttributeUtils.addAttr(node=self.baseCtrl, attrName='cacheScale',
			attrType="float", default=1, min=0.25, max=2.0,
			lock=False, keyable=False, channelBox=True,
			attrNiceName=None, verbose=True)

		for wight in self.wightList:
			wightCtrl = wight + ':c_moveWight_CTRL'
			# mc.connectAttr(self.baseCtrl+'.cacheScale', wightCtrl+'.cacheScale')
			# first break connection in the referenced file to the cacheScale
			mdNode = mc.createNode('multiplyDivide', n=wight + '_cache_MD')
			mc.connectAttr(self.baseCtrl + '.cacheScale', mdNode+'.input1X')
			mc.connectAttr(wightCtrl + '.cacheScale', mdNode + '.input2X')
			cacheNode = wight + ':' + animCacheNode
			mc.connectAttr(mdNode +  '.outputX', cacheNode + '.scale')

		if mc.objExists(self.drogonMover):
			oldPosition = mc.xform(self.drogonMover, q=True, matrix=True, relative=True)
			mc.xform(baseCtrlZro, matrix=oldPosition)
			mc.scale(1,1,1, baseCtrlZro)
			mc.parentConstraint(self.drogonMover, baseCtrlZro)


	def deleteSimArmy(self):
		refFile = '/data/share/rigging/rigSandbox/alonz/simCycleSystem/nonDynWhiteSetup.mb'
		for w in self.wightList:
			mc.file(refFile, rr=1, f=1, rfn=w+'RN')
			try:
				mc.delete(w+'RNfosterParent1')
			except:
				pass
		if mc.objExists(self.baseName+':walkPath_top_GRP'):
			refFile = '/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-crowdCharge/maya/scenes/techanim/walkPlane_rig.mb'
			mc.file(refFile, rr=1, f=1, rfn=self.baseName+'RN')
			mc.delete(self.topGrp)
		if mc.objExists(self.baseName + '_wights_OUT_GRP'):
			mc.delete(self.baseName + '_wights_OUT_GRP')
		if mc.objExists(self.baseName + '_top_GRP'):
			mc.delete(self.baseName + '_top_GRP')

		
	def checkForExistingArmy(self):
		exists = False
		topGrp = self.baseName + '_top_GRP'
		if mc.objExists(topGrp):
			nClothTrans = 'combined_{}_wightArmySIM_NCL'.format(self.baseName)
			if mc.objExists(nClothTrans):
				# print 'simCycle nCloth found: {}  - Exists'.format(nClothTrans)
				self.nClothTrans = nClothTrans
				self.nClothNode = mc.listRelatives(self.nClothTrans, s=1)[0]
				exists = True
		if exists:
			self.initializeSimCycleObject()
			return True
		

	def initializeSimCycleObject(self):
		existingWights = mc.ls(self.baseName+'_*RN')
		if existingWights:
			self.wightList = [w[:-2] for w in existingWights]
			self.wightCount = len(self.wightList)
		self.topGrp = self.baseName + '_top_GRP'
		self.clothMesh = 'combined_{}_wightArmySIM'.format(self.baseName)
		nucConnections = mc.listConnections(self.nClothNode, type='nucleus')
		self.nucleusGrp = self.baseName + '_nucleus_GRP'
		self.nucleus = list(set(nucConnections))[0]
		self.baseCtrl = 'c_'+self.baseName+'Master_CTRL'
		self.allSimGrp = 'simCycle_ALL_SIM'
		self.allOutGrp = 'simCycle_ALL_OUT'
		self.allNucGrp = 'simCycle_ALL_NUCLEII'
		self.allConstGrp = 'simCycle_ALL_CONSTRAINTS'
		self.simLayer = 'sim_lyr'
		self.pathLayer = 'path_lyr'
		self.outLayer = 'out_lyr'
		

	def populateWights(self, baseName, count):
		refWight = '/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-crowdCharge/maya/scenes/techanim/nonDynWhiteSetup.mb'
		refPath = '/data/share/rigging/rigSandbox/alonz/simCycleSystem/'
		baseRefFileName = 'nonDynWhiteSetup'
		refWight = refPath + baseRefFileName + '_' + self.animChoice + '.mb'
		wights = []
		if baseName:
			baseName += '_wight'
		else:
			baseName = 'wight'
		# reference in X number of wights
		for c in range(count):
			idx = '{:0>3d}'.format(c)
			ns = baseName + idx
			mc.file(refWight, r=1, ns=ns)
			wights.append(ns)
		self.wightList = wights
		# move
		self.moveWight()
		print 'finished moving all the wights'
		return wights
	

	def moveWight(self, numPerRow=8):
		tx = 0
		tz = 0
		wightList = self.wightList
		print wightList
		for i in range(len(wightList)):
			wightCtrl = wightList[i] + ':c_moveWight_CTRL'
			if i % numPerRow == 0:
				tz += 10
				tx = 0
			else:
				tx += 10
			mc.move(tx, 0, tz, wightCtrl, localSpace=1)
		print 'done moving {} wights'.format(len(wightList))
		
		
	def randomizeWightCache(self, wightList, maxFrame):
		for w in wightList:
			wightCtrl = w + ':c_moveWight_CTRL'
			mc.setAttr(wightCtrl + '.cacheScale', random.uniform(0.5808, 0.808))
			mc.setAttr(wightCtrl + '.cacheStart', random.randint(1, maxFrame))
			
			
	def randomizTranslation(self, wightList):
		for w in wightList:
			wightCtrl = w + ':c_moveWight_CTRL'
			count = len(wightList)
			# count = 20
			# if count < 50:
			# 	tx, ty, tz = random.uniform(-count*2, count*2), random.uniform(-count*2, count*2), random.uniform(-count*2, count*2)
			# else:
			# 	tx, ty, tz = random.uniform(-count, count), random.uniform(-count, count), random.uniform(-count, count)
			tx, ty, tz = random.uniform(-50, 50), \
						 random.uniform(0, 100), \
						 random.uniform(-50, 50)
			rx, ry, rz = 33, 0, 0
			mc.move(tx, ty, tz, wightCtrl)
			mc.rotate(rx, ry, rz, wightCtrl)			


	def unitePolys(self, sepGeo, uniteName='combinedPolys', bConstructionHistory=True, sSuffix=None,
				   sSuffixToRemove=None):
		if sSuffixToRemove:
			if sSuffix:
				uniteName = uniteName.replace(sSuffixToRemove, sSuffix)
			uniteName = uniteName.replace(sSuffixToRemove, '')
		uniteNodes = mc.polyUnite(sepGeo, ch=bConstructionHistory, n=uniteName)
		mc.rename(uniteNodes[1], uniteName + '_polyUnite')
		return uniteName
	
	
	def duplicateMesh(self, mesh, name):
		newMesh = mc.duplicate(mesh, rr=True, n=name)[0]
		allShapes = mc.listRelatives(newMesh, s=True, pa=True)
		noInti = mc.listRelatives(newMesh, s=True, ni=True)
		for shape in allShapes:
			if shape not in noInti:
				print 'deleting ', shape
				mc.delete(shape)
		return newMesh
	
	
	def create_nCloth(self, drivenGeo, driverGeo='', description='', parent='', bDriveRest=False):
		# names
		if not description:
			description = drivenGeo
		driverGeoShape = mc.listRelatives(driverGeo, s=1)
		nClothName = RigToolbox.Core.NodeUtils.findUniqueName(
			description + '_' + RigToolbox.Core.Defaults.Suffixes.nCloth)
		inputMeshName = RigToolbox.Core.NodeUtils.findUniqueName(
			description + '_' + CfxToolbox.Utils.Defaults.Suffixes.dyn + CfxToolbox.Utils.Defaults.Suffixes.inputMesh)
		outputMeshName = RigToolbox.Core.NodeUtils.findUniqueName(
			description + '_' + CfxToolbox.Utils.Defaults.Suffixes.dyn + CfxToolbox.Utils.Defaults.Suffixes.outputMesh)

		# Select
		mc.select(drivenGeo)
		# Create
		nClothShp = maya.mel.eval('createNCloth 0;')
		nCloth = mc.rename(mc.listRelatives(nClothShp, p=True)[0], nClothName)
		# Rename Input Shape
		nClothShpNN = mc.listRelatives(nCloth, s=True)[0]
		self.nClothNode = nClothShpNN
		nputShape = mc.listConnections(nClothShpNN, source=True, destination=False,
				plugs=True, type='mesh')[0].split('.')[0]
		mc.rename(inputShape, inputMeshName)
		# Rename Mesh's Shape
		outMeshShape = (mc.connectionInfo(nClothShpNN + '.outputMesh', dfs=True)[0]).split('.')[0]
		mc.rename(outMeshShape, outputMeshName)

		if parent:
			mc.parent(nCloth, parent)

		if driverGeo:
			mc.connectAttr(driverGeo + '.worldMesh[0]', nClothName + '.inputMesh', f=1)
			mc.connectAttr(driverGeo + 'Shape.worldMesh[0]', nClothName + '.restShapeMesh', f=1)

		self.nClothTrans = nCloth
		
	
	def turnArmyIntoCloth(self):
		self.sharedGroups()
		self.clothMesh = self.duplicateMesh(self.combinedArmyMesh, self.combinedArmyMesh + CfxToolbox.Utils.Defaults.Suffixes.dyn)
		mc.setAttr(self.combinedArmyMesh + '.v', 0)
		self.create_nCloth(self.clothMesh, self.combinedArmyMesh)
		self.assignNucleus()
		self.applyPreset(objs=[self.clothMesh], presetName=self.simCycleNClothPreset)
		Utils.Meshes.randomShader([self.clothMesh])
		self.shaderSG = 'combined_' + self.baseName + '_wightArmySIM_LAMSG'
		# organize
		mc.parent([self.clothMesh, self.nClothTrans, self.combinedArmyMesh], self.topGrp)
		# parent nucleus and constraints
		try:
			mc.parent(self.nucleus, self.allNucGrp)
		except:
			pass
		mc.parent(self.topGrp, self.allSimGrp)
		# assign to layer
		mc.editDisplayLayerMembers(self.simLayer, self.topGrp)
		# extra setAttrs
		mc.setAttr(self.nClothNode+'.selfCollisionFlag', 4)

                	
	def makeMoshers(self):
		heelVerts = [83,20]
		chestVerts = [7]
		# create the gravitys
		mc.select(cl=1)
		downGravity = mc.gravity(pos=[0, 0, 0], m=1700, pv=1, att=0, dx=0, dy=-1, dz=0, mxd=4.2, n=self.baseName+'_downGravity')[0]
		mc.select(cl=1)
		upGravity = mc.gravity(pos=[0, 0, 0], m=2200, pv=1, att=0, dx=0, dy=1, dz=0, mxd=5.1, n=self.baseName+'_upGravity')[0]
		mc.select(cl=1)
		# assign the gravity to the verts
		verts = self.selectVertsOnAllWights(heelVerts)
		print downGravity
		mc.select(downGravity, add=1)
		maya.mel.eval("AttachSelectedAsSourceField;")
		# connectFields(verts, downGravity)
		mc.connectDynamic(self.nClothNode, f=upGravity)
		mc.select(cl=1)
		verts = self.selectVertsOnAllWights(chestVerts)
		mc.select(upGravity, add=1)
		maya.mel.eval("AttachSelectedAsSourceField;")
		# connectFields(verts, downGravity)
		mc.connectDynamic(self.nClothNode, f=downGravity)


	def addChestRadial(self):
		chestVerts = [7]
		chestRadial = mc.radial(pos=[0, 0, 0], m=3, pv=1, att=1, mxd=20, n=self.baseName+'_chest_radial')[0]
		mc.select(cl=1)
		# assign the gravity to the verts
		verts = self.selectVertsOnAllWights(chestVerts)
		mc.select(chestRadial, add=1)
		maya.mel.eval("AttachSelectedAsSourceField;")
		mc.connectDynamic(self.nClothNode, f=chestRadial)
		mc.select(cl=1)
		
		
	# selecting functions

	def selectHands(self, side='random'):
		leftHandVtx1 = 63
		leftHandVtx2 = 66
		rightHandVtx1 = 117
		rightHandVtx2 = 120
		allVtxs = []
		baseName = self.clothMesh
		if side != 'random':
			for i in range(len(self.wightList)):
				if side == 'both' and (i%3 ==0):
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in range(leftHandVtx1, leftHandVtx1+1)]
					allVtxs.extend(objectVerts)
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in range(rightHandVtx1, rightHandVtx1+1)]
					allVtxs.extend(objectVerts)
				elif side == 'left' and (i%2 == 0):
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in range(leftHandVtx1, leftHandVtx1+1)]
					allVtxs.extend(objectVerts)
				elif side == 'right' and i%2 != 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in range(rightHandVtx1, rightHandVtx1+1)]
					allVtxs.extend(objectVerts)
		if side == 'random':
			for i in range(len(self.wightList)):
				if i % 3 == 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(leftHandVtx1, leftHandVtx1 + 1)]
					allVtxs.extend(objectVerts)
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(rightHandVtx1, rightHandVtx1 + 1)]
					allVtxs.extend(objectVerts)
				elif i % 2 == 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(leftHandVtx1, leftHandVtx1 + 1)]
					allVtxs.extend(objectVerts)
				elif i % 2 != 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(rightHandVtx1, rightHandVtx1 + 1)]
					allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs
	
	
	def selectBackHead(self):
		vertsToSelect = [8,9,10,11,12,13,51,52,54,55,56,57,59,60,62,75,76,77,113,114,115]
		allVtxs = []
		for i in range(len(self.wightList)):
			objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in vertsToSelect]
			allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs
	
	
	def selectLeftSide(self):
		rSideVertsToSelect = [71,72,73]
		lSideVertsToSelect = [0, 2, 4]
		allVtxs = []
		for i in range(len(self.wightList)):
			objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in lSideVertsToSelect]
			allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs
	

	def selectRightSide(self):
		rSideVertsToSelect = [71,72,73]
		lSideVertsToSelect = [0, 2, 4]
		allVtxs = []
		for i in range(len(self.wightList)):
			objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in rSideVertsToSelect]
			allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs

	
	def selectButtSide(self):
		buttVertsToSelect = [14,15,78]
		allVtxs = []
		for i in range(len(self.wightList)):
			objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in buttVertsToSelect]
			allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs
	
	
	def selectFeet(self, side='both'):
		vertsToSelect = [20,21,30,31,83,84,93,94]
		if self.animChoice == 'slashing':
			vertsToSelect = [18,28,30,81,92,94]
		allVtxs = []
		leftFootVtx1 = 31
		rightFootVtx1 = 94
		for i in range(len(self.wightList)):
			if side == 'random':
				if i % 2 == 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(leftFootVtx1, leftFootVtx1 + 1)]
					allVtxs.extend(objectVerts)
				else:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(rightFootVtx1, rightFootVtx1 + 1)]
					allVtxs.extend(objectVerts)
			if side == 'both':
				objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in vertsToSelect]
				allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs

	
	def selectVertsOnAllWights(self, wight000VertList, side='both', iLeftSideVert=31, iRightSideVert=94):
		vertsToSelect = wight000VertList
		if self.animChoice == 'slashing':
			# can do something here for specific animation cycles
			pass
		allVtxs = []
		leftFootVtx1 = iLeftSideVert
		rightFootVtx1 = iRightSideVert
		baseName = self.clothMesh
		for i in range(len(self.wightList)):
			if side == 'random':
				if i % 2 == 0:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(leftFootVtx1, leftFootVtx1 + 1)]
					allVtxs.extend(objectVerts)
				else:
					objectVerts = ['%s.vtx[%d]' % (baseName, idx + i * self.baseVtxCount) for idx in
								   range(rightFootVtx1, rightFootVtx1 + 1)]
					allVtxs.extend(objectVerts)
			if side == 'both':
				objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in vertsToSelect]
				allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs
	
	
	def selectHandsHead(self):
		vertsToSelect = [54,64,117]
		allVtxs = []
		for i in range(len(self.wightList)):
			objectVerts = ['%s.vtx[%d]' % (self.clothMesh, idx + i * self.baseVtxCount) for idx in vertsToSelect]
			allVtxs.extend(objectVerts)
		mc.select(allVtxs)
		return allVtxs

	
	def setupRunningWights(self):
		# run after self.createSimCycleArmy so the wights are already in scene
		self.bRunners = True
		refWalkPlaneRig = '/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-crowdCharge/maya/scenes/techanim/walkPlane_rig.mb'
		mc.file(refWalkPlaneRig, r=1, ns=self.baseName)
		self.walkPlane = self.baseName + ':walkPathPlane'
		mc.setAttr(self.walkPlane+'.v', 0)
		self.l_walkPlane = self.baseName + ':l_walkPathPlane'
		self.r_walkPlane = self.baseName + ':r_walkPathPlane'
		self.bottom_walkPlane = self.baseName + ':floor_walkPathPlane'
		self.runnerTracks = [self.walkPlane, self.l_walkPlane, self.r_walkPlane, self.bottom_walkPlane]
		self.trackRootCtrl = self.baseName+':c_wightTrack1_CTRL'
		self.masterCtrl = 'c_'+self.baseName+'Master_CTRL'
		# organize
		walkPathGrp = self.baseName+':walkPath_top_GRP'
		mc.parent(walkPathGrp, self.allSimGrp)
		# assign to layer
		mc.editDisplayLayerMembers(self.pathLayer, walkPathGrp)

		# create new nucleus for walkers
		self.bUseNewNucleus = True
		self.assignNucleus()
		# Create nRigid on COL
		cascadeNode = 'c_cascade_INFO'
		if not mc.objExists(cascadeNode):
			mc.createNode('transform', n='c_cascade_INFO')
		else:
			mc.delete(cascadeNode)
			mc.createNode('transform', n='c_cascade_INFO')
		self.cdyn = Dynamics.CreateDynamics()
		this = mc.ls(self.walkPlane)
		self.nRigids = []
		nRigid = self.cdyn.nRigid(drivenObj = this, description='topWalkPlane',
								  parent=self.topGrp,
								  nucleus=self.nucleus)[0]
		mc.setAttr(nRigid+'Shape.collide', 0)
		self.nRigids.append(nRigid)
		this = mc.ls(self.l_walkPlane)
		nRigid = self.cdyn.nRigid(drivenObj=this, description='lWalkPlane',
								  parent=self.topGrp, side='left',
								  nucleus=self.nucleus)[0]
		mc.setAttr(nRigid + 'Shape.collide', 0)
		self.nRigids.append(nRigid)
		this = mc.ls(self.r_walkPlane)
		nRigid = self.cdyn.nRigid(drivenObj=this, description='rWalkPlane',
								  parent=self.topGrp, side='right',
								  nucleus=self.nucleus)[0]
		mc.setAttr(nRigid + 'Shape.collide', 0)
		self.nRigids.append(nRigid)
		this = mc.ls(self.bottom_walkPlane)
		nRigid = self.cdyn.nRigid(drivenObj=this, description='bottomWalkPlane',
								  parent=self.topGrp,
								  nucleus=self.nucleus)[0]
		mc.setAttr(nRigid + 'Shape.collide', 0)
		self.nRigids.append(nRigid)

		# duplicate ground collider
		groundGeo = 'winterfell001_C'
		self.groundGeo = ''
		if mc.objExists(groundGeo):
			self.groundGeo = mc.duplicate(groundGeo, n=self.baseName+':'+self.groundGeo)[0]
			groundGeo = mc.ls(self.groundGeo)
			nRigid = self.cdyn.nRigid(drivenObj = groundGeo, description='ground',
								  nucleus=self.nucleus)[0]
			nRigidShape = mc.listRelatives(nRigid, s=1)[0]
			mc.setAttr(nRigidShape+'.thickness', 0.01)
			self.runnerTracks.append(self.groundGeo)
			mc.setAttr(self.groundGeo+'.v', 0)
		# create nConstraints
		walkerConstraints = self.constrainRunners()
		# # add field
		self.setupRunnersField()
		# speed up wights
		ctrls = mc.ls('*:c_moveWight_CTRL', s=False)
		for ctrl in ctrls:
			mc.setAttr(ctrl + '.cacheScale', random.uniform(0.5, 1))
		# organize
		mc.parent(walkerConstraints, self.nucleusGrp)
		mc.parentConstraint(self.trackRootCtrl, self.nucleusGrp, mo=1)
		mc.parent(self.uniformField, self.nucleusGrp)
		mc.parent(self.masterCtrl, self.trackRootCtrl)
		mc.setAttr(self.masterCtrl+'.v', 0)


	def setupRunnersField(self):
		nf = RigToolbox.Core.NodeUtils.nodeFactory()
		if not mc.pluginInfo('matrixNodes', q=True, loaded=True):
			RigToolbox.Core.Check.loadPlugin('matrixNodes')

		# create the field
		mc.select(self.clothMesh, r=1)
		self.uniformField = mc.createNode('uniformField')
		mc.setAttr(self.uniformField+'.attenuation', 0)
		mc.setAttr(self.uniformField + '.magnitude', 320)
		mc.setAttr(self.uniformField + '.directionX', 0)
		mc.setAttr(self.uniformField + '.directionZ', 1)
		mc.connectDynamic(self.nClothNode, f=self.uniformField)
		# create a control to show the field direction
		oWindCtrl = nf.createControl(description='forceDirection', shape='arrow', color='yellow',
									 rotateBy=[0, 0, 0],
									 size=20,
									 lockAndHide=["s", "v", "ro"])
		windComposeMatrix = mc.createNode('composeMatrix', n='wind_composeMatrix')
		windVectorProduct = mc.createNode('vectorProduct', n='wind_vectorProduct')
		mc.setAttr(windVectorProduct + '.operation', 3)
		mc.setAttr(windVectorProduct + '.input1Z', 1)
		mc.connectAttr(oWindCtrl.control.transform + '.rotate', windComposeMatrix + '.inputRotate')
		mc.connectAttr(windComposeMatrix + '.outputMatrix', windVectorProduct + '.matrix')
		mc.connectAttr(windVectorProduct + '.output', self.uniformField + '.direction', force=True)
		# connect to the rig
		oWindCtrl.control.group.setParent(self.trackRootCtrl)
		mc.pointConstraint(self.trackRootCtrl, oWindCtrl.control.transform.name, mo=0)
		mc.aimConstraint(self.baseName+':c_wightTrack6_CTRL', oWindCtrl.control.transform.name, mo=1)
		mc.parent(oWindCtrl.control.group, self.topGrp)
		# custom attributes
		oWindCtrl.control.transform.addAttr('forceMag', attrType='float', min=-1000, max=10000, default=300)
		oWindCtrl.control.transform.forceMag.connect(self.uniformField + '.magnitude', force=True)


		RigToolbox.Core.AttributeUtils.lockAndHide(node=oWindCtrl.control.transform.name,
							   attrs=['tx','ty','tz','rx','ry','rz','sx','sy','sz'],
							   unlock=False, unhide=True, doNow=True,
							   all=False, verbose=False)
		mc.select(cl=1)

		
	def constrainRunners(self):
		# create nConstraints
		walkerConstraints = []
		verts = self.selectBackHead()
		const = createNConstraints(verts, self.walkPlane, 'slideOnSurface', name=self.baseName + '_top_SOS')
		mc.setAttr(const+'.strength', 200)
		walkerConstraints.append(const)
		verts = self.selectRightSide()
		const = createNConstraints(verts, self.r_walkPlane, 'slideOnSurface', name=self.baseName + '_r_SOS')
		mc.setAttr(const+'.strength', 200)
		walkerConstraints.append(const)
		verts = self.selectLeftSide()
		const = createNConstraints(verts, self.l_walkPlane, 'slideOnSurface', name=self.baseName + '_l_SOS')
		mc.setAttr(const+'.strength', 200)
		walkerConstraints.append(const)
		verts = self.selectButtSide()
		const = createNConstraints(verts, self.bottom_walkPlane, 'slideOnSurface', name=self.baseName + '_bot_SOS')
		mc.setAttr(const + '.strength', 200)
		walkerConstraints.append(const)

		return walkerConstraints

	
	
	def initClothSettings(self):
		ups = mc.internalVar(userPresetsDir=1)
		presetName = 'wight'
		presetFile = ups
		for f in mc.getFileList(folder=ups, filespec='*.mel'):
			if presetName in f:
				presetFile += f
		mc.eval('applyPresetToNode "%s" "" "" "%s" 1;' % (self.nClothNode, presetFile))


	def applyPreset(self, objs, presetName):
		for obj in objs:
			if mc.objectType(obj) != 'nCloth':
				objShape = Utils.MayaUtils.getShape(obj)
				nCloth_nodes = mc.listConnections(objShape, type='nCloth')
				for node in nCloth_nodes:
					mel.eval('applyPresetToNode "%s" "" "" "%s" 1;' % (Utils.MayaUtils.getShape(node), presetName))
			else:
				mel.eval('applyPresetToNode "%s" "" "" "%s" 1;' % (obj, presetName))


	def createPointToSurface(self, collider, verts=None):
		# check if collider is on the same nucleus
		if verts==None:
			verts = self.selectHands()
		mc.select(verts, collider, r=1)
		const = createNConstraints(verts, collider, 'pointToSurface', name=self.baseName+'_P2S')
		mc.setAttr(const+'.constraintMethod', 2)
		mc.setAttr(const+'.restLength', 0.1)
		mc.setAttr(const+'.restLengthScale', 0.1)
		mc.setAttr(const+'.bend', 1)
		mc.setAttr(const+'.bendBreakAngle', 90)
		mc.setAttr(const + '.strength', 2)
		mc.setAttr(const + '.glueStrength', 0.96)
		constTrans = mc.listRelatives(const, p=1)[0]
		mc.parent(constTrans, self.allConstGrp)

		
	def assignNucleus(self):
		# check for existing nucleus
		nucConnections = mc.listConnections(self.nClothNode, type='nucleus')
		existingNuc = list(set(nucConnections))[0]
		self.nucleus = existingNuc
		# if using existing, rename to keep
		if not self.bUseNewNucleus:
			self.nucleus = mc.rename(self.nucleus, self.baseName + '_NUC')
			mc.setAttr(self.nucleus + '.spaceScale', 0.1)
		# self.nucleus = mc.rename(existingNuc, self.baseName+'_NUC')
		# if using new, create new nucleus
		if self.bUseNewNucleus:
			# existingNuc = mc.rename(existingNuc, 'toDelete')
			self.nucleus = mc.createNode('nucleus', n=self.baseName + '_NUC')
			# mc.parent(self.nucleus, self.allNucGrp)
			mc.select(self.nClothNode, r=1)
			print 'Assigning {} to {}'.format(self.nClothNode, self.nucleus)
			maya.mel.eval('assignNSolver %s;' % self.nucleus)
			mc.connectAttr('time1.outTime', self.nucleus + '.currentTime', f=1)
		self.setNucleusSettings()


	def setNucleusSettings(self):
		mc.setAttr(self.nucleus + '.startFrame', 978)
		mc.setAttr(self.nucleus + '.spaceScale', 0.1)
		mc.setAttr(self.nucleus + '.subSteps', 5)
		mc.setAttr(self.nucleus + '.maxCollisionIterations', 10)


	def randomizeVariants(self, geo):
		wightID = random.randint(1, 14)
		shader =  variantDict[str(wightID)]
		# maya.cmds.sets(geo, e=1, forceElement=shadingSet)
		Utils.Meshes.cfxShader(geo=geo, shader=shader)
		attr = mc.addAttr(geo, ln='ieAttr_ID', at='double', dv=wightID)
		attr = mc.addAttr(geo, ln='ie_ID', at='double', dv=wightID)

		
	def create_outputNetwork(self):
		# create mesh copy
		self.outputPoly = mc.polySphere(n=self.baseName+'_wights_OUT')[0]
		outputPolyShape = Utils.MayaUtils.getShape(self.outputPoly)
		clothMeshShape = Utils.MayaUtils.getShape(self.clothMesh)
		mc.connectAttr(clothMeshShape+'.outMesh', outputPolyShape+'.inMesh', f=1)
		# poly separate
		outputPolyGrp = separatePolys(self.outputPoly, sRemoveExistingSuffix=False)

		mc.parent(outputPolyGrp, self.allOutGrp, absolute=1)
		# layers
		mc.editDisplayLayerMembers(self.outLayer, self.allOutGrp)
		# assign variant shaders and attrs
		# for wight in mc.listRelatives(outputPolyGrp, c=1, shapes=0):
		mc.sets(outputPolyGrp, e=1, forceElement=self.shaderSG)


	def sharedGroups(self):
		# create top sim grp
		if not mc.objExists('simCycle_ALL_SIM'):
			mc.group(n='simCycle_ALL_SIM', em=1)
		self.allSimGrp = 'simCycle_ALL_SIM'
		# create top output grp
		if not mc.objExists('simCycle_ALL_OUT'):
			mc.group(n='simCycle_ALL_OUT', em=1)
		self.allOutGrp = 'simCycle_ALL_OUT'
		# create top nucleus grp
		if not mc.objExists('simCycle_ALL_NUCLEII'):
			mc.group(n='simCycle_ALL_NUCLEII', em=1)
		self.allNucGrp = 'simCycle_ALL_NUCLEII'
		# create top nucleus grp
		if not mc.objExists('simCycle_ALL_CONSTRAINTS'):
			mc.group(n='simCycle_ALL_CONSTRAINTS', em=1)
		self.allConstGrp = 'simCycle_ALL_CONSTRAINTS'
		# create top nucleus grp
		if not mc.objExists('simCycle_ALL_COLLIDERS'):
			mc.group(n='simCycle_ALL_COLLIDERS', em=1)
		self.allCollGrp = 'simCycle_ALL_COLLIDERS'

		
	def duplicateDragonCollider(self):
		drogonHiColName = 'drogonHi_COL'

		if mc.objExists(drogonHiColName):
			# create collider copy
			self.collider = mc.polySphere(n=self.baseName+'_'+drogonHiColName)[0]
			colliderShape = Utils.MayaUtils.getShape(self.collider)
			drogonShape = Utils.MayaUtils.getShape(drogonHiColName)
			mc.connectAttr(drogonShape + '.outMesh', colliderShape + '.inMesh', f=1)
			oldPosition = mc.xform(animLoc, q=True, matrix=True, relative=True)
			mc.xform(self.collider, matrix=oldPosition)

		# make nRigid
		mc.select(self.collider, r=1)
		nRigid = maya.mel.eval('makeCollideNCloth;')
		nRigidTrans = mc.listRelatives(nRigid, p=1)[0]
		nRigidTrans = mc.rename(nRigidTrans, self.collider + '_NRG')
		nRigid = mc.listRelatives(nRigidTrans, s=1)[0]
		# organize
		mc.parent(self.collider, self.topGrp)
		mc.parent(nRigidTrans, self.topGrp)
		
		
	def createExcludeCollideConstraints(self):
		otherClothObjects = mc.ls(type='nCloth')
		for other in otherClothObjects:
			if other != self.nClothNode:
				print other


	def layers(self):
		self.simLayer = 'sim_lyr'
		self.pathLayer = 'path_lyr'
		self.outLayer = 'out_lyr'

		if not mc.objExists(self.simLayer):
			mc.createDisplayLayer(n=self.simLayer, e=1)
			mc.setAttr(self.simLayer + '.color', 13)

		if not mc.objExists(self.pathLayer):
			mc.createDisplayLayer(n=self.pathLayer, e=1)
			mc.setAttr(self.pathLayer + '.color', 1)

		if not mc.objExists(self.outLayer):
			mc.createDisplayLayer(n=self.outLayer, e=1)
			mc.setAttr(self.outLayer + '.color', 6)
			
			
	def setStartFrameAndStates(self):
		'''
		Script that sets the initial states on nCloth objects in scene and sets nucleus start frame
		to the current frame. Also adjusts playbackOptions.
		'''
		curTime = mc.currentTime(q=True)
		nuclei = mc.ls(type='nucleus')
		clothes = mc.ls(type='nCloth')
		for c in clothes:
			mc.nBase(c, e=True, stuffStart=True)
			print '## Set initial state on {0} to current frame'.format(c)
		for n in nuclei:
			mc.setAttr(n + '.startFrame', curTime)
			print '## Set startFrame on {0} to {1}'.format(n, curTime)
		mc.playbackOptions(e=True, minTime=curTime)
		mc.currentTime(curTime, u=True)


	def setInitialState(self, startTime=980):
		curTime = mc.currentTime(q=True)
		mc.nBase(self.nClothNode, e=True, stuffStart=True)
		# mc.playbackOptions(e=True, minTime=startTime)
		# mc.currentTime(startTime, u=True)
		
		
	def switchAnimCache(self, anim):
		animChoice = anim -1
		# mc.setAttr(self.baseCtrl + '.animChoice', animChoice)
		# for w in self.wightList:
		# 	cacheBlendNode = w+':cacheBlend1'
		# 	wightMoveCtrl = w+':c_moveWight_CTRL'
		# 	if animChoice == 0:		# climb anim
		# 		mc.setAttr(cacheBlendNode + '.climbCache1', 1)
		# 		mc.setAttr(cacheBlendNode + '.slashingCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.runningCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.grabbingCache1', 0)
		# 		maxFrame = self.dAnimCacheEnds['climb']
		# 	if animChoice == 1:		# slashing anim
		# 		mc.setAttr(cacheBlendNode + '.climbCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.slashingCache1', 1)
		# 		mc.setAttr(cacheBlendNode + '.runningCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.grabbingCache1', 0)
		# 		maxFrame = self.dAnimCacheEnds['slashing']
		# 	if animChoice == 2:		# running anim
		# 		mc.setAttr(cacheBlendNode + '.climbCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.slashingCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.runningCache1', 1)
		# 		mc.setAttr(cacheBlendNode + '.grabbingCache1', 0)
		# 		maxFrame = self.dAnimCacheEnds['running']
		# 	if animChoice == 3:		# grabbing anim
		# 		mc.setAttr(cacheBlendNode + '.climbCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.slashingCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.runningCache1', 0)
		# 		mc.setAttr(cacheBlendNode + '.grabbingCache1', 1)
		# 		maxFrame = self.dAnimCacheEnds['grabbing']
		maxFrame = self.dAnimCacheEnds[self.animChoice]
		self.randomizeWightCache(self.wightList, maxFrame)




		
		
		
		
def connectFields(sel, fields=[]):
	if not sel:
		sel = mc.ls(sl=True)
	for each in sel:
		s = mc.listRelatives(each, s=True)[0]
		nc = mc.listRelatives(mc.listConnections(s, type='nCloth')[0], s=True)
		conns = mc.listConnections(nc, type='field')
		fields.extend(conns)
		mc.connectDynamic(each, fields=fields)


def addCacheScaleAttrs():
	# anim speed attr
	if not mc.attributeQuery('cacheScale', exists=1, n=self.baseCtrl):
		RigToolbox.Core.AttributeUtils.addAttr(node=self.baseCtrl, attrName='cacheScale',
							   attrType="long", default=1,
							   lock=False, keyable=True, channelBox=True,
							   attrNiceName=None, verbose=True)

	
def create_nRigid(drivenGeo, nucleus='', description='', parent='', bDriveRest=False):
	cdyn = Dynamics.CreateDynamics()
	nRigid = cdyn.nRigid(drivenObj = drivenGeo, description=description,
							  parent=parent,
							  nucleus=nucleus)[0]
	mc.select(nRigid, r=1)
	if nucleus and mc.objectType(nucleus)=='nucleus':
		maya.mel.eval('assignNSolver %s;' % nucleus)
	if parent:
		mc.parent(nRigid, parent)
	return nRigid
	
	
def separatePolys(geo, bConstructionHistory=1, sSuffix=None, sRemoveExistingSuffix=True):
	sepGeos = mc.polySeparate(geo, ch=bConstructionHistory)
	sepGeoGrps = []
	oldSuffix = ''
	for sepGeo in sepGeos:
		geoShortName = geo.split('|')[-1]
		oldSuffix = geoShortName.split('_')[-1]
		geoNiceName = mc.rename(sepGeo, geoShortName + '_01')
		if sRemoveExistingSuffix:
			mc.rename(geoNiceName,geoNiceName.replace('_'+oldSuffix, ''))
	grpShortName = geo.split('|')[-1]
	geoGrp = mc.rename(geo, grpShortName+'_GRP')
	if sSuffix:
		for sepGeo in mc.listRelatives(geoGrp, c=1):
			geoNiceName = mc.rename(sepGeo, sepGeo + '_' + sSuffix)

	if sRemoveExistingSuffix:
		geoGrp = mc.rename(geoGrp, geoGrp.replace('_'+oldSuffix, ''))

	for g in sepGeos:
		Utils.Meshes.cfxShader(geo=g, shader='blue')

	return geoGrp




def createBlendShapes(targets=[],
					  mesh='',
					  frontOfChain=False,
					  parallel=False,
					  customBsSuffix=''):
	bs = ''
	if targets:
		mc.select(targets[0], r=True)
		mc.select(mesh, add=True)
		if '|' in targets[0]:
			bsName = targets[0].split('|')[-1] + '_BSH'
		else:
			bsName = targets[0] + '_BSH'
		if customBsSuffix:
			bsName = bsName.replace('BSH', customBsSuffix + '_BSH')
		bs = mc.blendShape(tc=0, parallel=parallel, frontOfChain=frontOfChain, name=bsName)[0]
		for i in range(1, len(targets)):
			mc.select(targets[i], r=True)
			mc.select(mesh, add=True)
			mc.blendShape(bs, e=True, tc=1, t=[mesh, i, targets[i], 1])
	mc.select(cl=True)
	mc.setAttr(bs+'.w[0]', 1)
	return bs



def duplicateAndConnect(oldObj, newName='', bConstrain=True):
	dupe = mc.polyDuplicateAndConnect(oldObj, rc=1)[0]
	if bConstrain:
		mc.parentConstraint(oldObj, dupe)
	if newName:
		dupe = mc.rename(dupe, newName)
	return dupe


def getNrigidAssignedNucleus(obj):
	nuc = ''
	if mc.objectType(obj) == 'transform':
		objShp = mc.listRelatives(obj, s=1)[1]
		n = mc.listConnections(objShp, type='nRigid')[0]
		nShp = mc.listRelatives(n, s=1)[0]
		if mc.objectType(nShp) == 'nRigid':
			print nShp
			nuc = mc.listConnections(nShp, type='nucleus')[0]
	if nuc:
		return nuc
	else:
		return False


def getNclothAssignedNucleus(obj):
	nuc = ''
	if mc.objectType(obj) == 'transform':
		objShp = mc.listRelatives(obj, s=1)[1]
		n = mc.listConnections(objShp, d=1,type='nCloth')[0]
		nShp = mc.listRelatives(n, s=1)[0]
		return nShp


	
###############33		sim cycle shot setup functions
def setup_simCycleDragonBs():
	wightsTechAnimPath = '/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-CrowdWights/maya/scenes/techanim/'
	wightBaseFile = '/data/share/rigging/rigSandbox/alonz/simCycle_baseShotFile.mb'
	dragonGeoFile = 'drogon_REN.mb'
	drogonLoColName = 'drogonLo_COL'
	drogonHiColName = 'drogonHi_COL'
	animDrogon = 'C_body001Hi_REN'
	animTopGrp = 'drogon_001Geo'
	drogonMover = 'drogon_simCycle_COL'

	# import the file
	if not mc.objExists(drogonMover):
		mc.file(wightBaseFile, i=True, pr=1)

	if mc.objExists(animTopGrp):
		bu.expandSceneShapes(convertToGeo=1)
		# create blendshape
		cd = RigToolbox.Core.DeformerUtils.CreateDeformer()
		bsh = cd.blendShape(deformedGeo=drogonMover, loadMap=False, targetsOn=True,
							description='', driverGeo=animDrogon)
		# snap rigid drogon to animation world space
		mc.select('C_body001Hi_REN.f[88961]', r=True)
		animLoc = RigToolbox.Core.GeoUtils.stickyTransform(locDescription='anim')
		oldPosition = mc.xform(animLoc, q=True, matrix=True, relative=True)
		mc.xform(drogonMover, matrix=oldPosition)


#################################################################################3

class simCycleUi(object):

	# On initialize, create the UI and show it.
	def __init__(self):
		"""Initialize"""
		if mc.window('simCycleUI', exists=True):
			mc.deleteUI('simCycleUI', window=True)

		self.dUIElements = {}
		self.createWindow()
		self.initializeList()
		self.cArmy = object


		
	def createWindow(self):
		"""This function creates the window."""

		# Create the window element
		self.dUIElements['window'] = 		mc.window('simCycleUI', title='Sim Cycle UI')
		self.dUIElements['main_layout'] = 	mc.columnLayout(adjustableColumn=True, cal='left')
		mc.rowLayout(nc=2, p=self.dUIElements['main_layout'])
		#-----						##
		mc.text(label="Once anim has been brought in. Press this >>",
				w=200, ww=1)
		self.dUIElements['btnShotSetup'] = 	mc.button(label="ShotSetup", width=100, c=self.shotSetup)
		mc.setParent('..')

		#-----						##
		mc.separator(h=10)
		mc.frameLayout(label='Sim Cycle Group Creation')
		# mc.text(label='    Sim Cycle Group Creation')
		self.dUIElements['txtName'] = 		mc.textFieldGrp('txtName', label='Name', text="wightz",
										 cw=[(1, 50), (2, 200)])
		self.dUIElements['txtCount'] = 		mc.textFieldGrp('txtCount', label='Count', text=10,
										 cw=[(1, 50), (2, 200)])



		mc.rowLayout(nc=3)
		self.dUIElements['rdoAnimChoice'] = mc.radioCollection('rdoAnimChoice')
		rb1 = mc.radioButton('climb', label='Climb1', sl=1)
		rb2 = mc.radioButton('climb2', label='Climb2')
		rb3 = mc.radioButton('climb3', label='Climb3')
		mc.setParent('..')
		mc.rowLayout(nc=3)
		rb1 = mc.radioButton('slashing', label='Slashing')
		rb2 = mc.radioButton('grabbing', label='Grabbing')
		rb3 = mc.radioButton('running', label='Running')
		mc.rowLayout(nc=3, p=self.dUIElements['main_layout'])
		self.dUIElements['boxFormation'] = 	mc.checkBox('boxFormation', label='formation', value=1)
		# self.dUIElements['boxNewNucleus'] = mc.checkBox('boxNewNucleus', label='new nucleus', value=1)
		self.dUIElements['btnCreate'] = 	mc.button(label="Create", width=100, c=self.createArmy)		# CREATE
		mc.setParent('..')
		mc.separator(h=10)

		#-----						##
		# list existing armies
		mc.frameLayout(label='List of existing simCycle groups')
		# mc.text(label='List of existing simCycle groups')
		self.dUIElements['armyList'] = mc.textScrollList('armyList',
						  numberOfRows=12,
						  allowMultiSelection=True,
						  append=[],
						  dcc=self.getSelected)
		#-----						##
		# BUTTONS
		mc.rowLayout(nc=3, p=self.dUIElements['main_layout'])
		self.dUIElements['btnDelete'] = mc.button(label="Delete", width=100, c=self.deleteArmy)
		self.dUIElements['btnRefresh'] = mc.button(label="Refresh", width=100, c=self.refresh)
		self.dUIElements['btnSelectBase'] = mc.button(label="Select baseCtrl", width=100, c=self.selectBaseCtrl)

		mc.rowLayout(nc=3, p=self.dUIElements['main_layout'])
		self.dUIElements['btnMakeRunners'] = mc.button(label="Make Runners", width=100, c=self.makeRunners)
		self.dUIElements['btnMakeMoshers'] = mc.button(label="Make Moshers", width=100, c=self.makeMoshers)
		self.dUIElements['btnChestRadial'] = mc.button(label="Add Chest Radial", width=100, c=self.addChestRadial)

		#-----						##
		# CONSTRAINTS
		mc.setParent('..')
		mc.separator(h=10)
		mc.frameLayout(label='Selecting')
		mc.rowLayout(nc=3)
		self.dUIElements['btnSlHands'] = mc.button(label="Hands", width=100, c=self.selectHands)
		self.dUIElements['btnSlFeet'] = mc.button(label="Feet", width=100, c=self.selectFeet)
		self.dUIElements['btnSlHandsHead'] = mc.button(label="Hands+Heads", width=100, c=self.selectHandsHead)
		mc.setParent('..')
		mc.rowLayout(nc=3)
		self.dUIElements['btnSlChest'] = mc.button(label="Chest", width=100, c=self.selectChest, io=0)
		self.dUIElements['btnSlHeels'] = mc.button(label="Heels", width=100, c=self.selectHeels, io=0)
		self.dUIElements['btnSlWhatever'] = mc.button(label="Verts", width=100, c=self.selectVerts, enable=False)

		mc.frameLayout(label='Constraints & Colliders', p=self.dUIElements['main_layout'])
		mc.rowLayout(nc=1, p=self.dUIElements['main_layout'])
		self.dUIElements['txtNucleus'] = mc.textFieldButtonGrp(label="Nucleus",
								buttonLabel='< <',
								bc=self.setNucleus,
								cw=[(1, 110), (2, 150)])
		mc.rowLayout(nc=1, p=self.dUIElements['main_layout'])
self.dUIElements['txtVerts'] = mc.textFieldButtonGrp(label="Verts",
								buttonLabel='< <',
								bc=self.setVerts,
								cw=[(1, 110), (2, 150)])
		mc.rowLayout(nc=1, p=self.dUIElements['main_layout'])
		self.dUIElements['txtCollider'] = mc.textFieldButtonGrp(label="Collider",
								buttonLabel='< <',
								bc=self.setCollider,
								cw=[(1, 110), (2, 150)])
		# mc.rowLayout(nc=2, p=self.dUIElements['main_layout'])
		# mc.text(label="Set nucleus first. Select nCloth or nRigid. Then >>",
		# 		w=200, ww=1)
		# self.dUIElements['btnAssignNuc'] = mc.button(label="Assign Nucleus", width=100, c=self.assignNucleus)
		mc.setParent('..')
		mc.separator(h=10)

		mc.rowLayout(nc=2, p=self.dUIElements['main_layout'])
		mc.text(label="Make sure set collider is on the same nucleus as the"
					  " simCycle group. Then...",
				w=200, ww=1)
		self.dUIElements['btnAttach'] = 	mc.button(label="Attach Hands", width=100, c=self.attachHands)
		mc.setParent('..')
		mc.separator(h=10)
	
		mc.rowLayout(nc=2, p=self.dUIElements['main_layout'])
		#-----						##
		mc.text(label="Select 2 items. Exclude Collide >>",
				w=200, ww=1)
		self.dUIElements['btnExcludeCollide'] = 	mc.button(label="Exclude Collide", width=100, c=self.excludeCollide)
		mc.setParent('..')
		mc.separator(h=10)

		mc.rowLayout(nc=2, p=self.dUIElements['main_layout'])
		mc.text(label="Set nucleus first. This will dupe Drogon, and assign it to whats set >>",
				w=200, ww=1)
		self.dUIElements['btnDupCollider'] = mc.button(label="Dupe Colliders", width=100, c=self.duplicateDrogonCollider)
		# -----						##
		# COLLIDERS
		# mc.setParent('..')
		# mc.frameLayout(label='Collidors', p=self.dUIElements['main_layout'])
		# self.dUIElements['menuNucleii'] = mc.optionMenu('nucList', label='Nucleii') #changeCommand=printNewMenuItem)
		# mc.menuItem(label='NOT IN USE YET')

		# Show the window.
		mc.showWindow(self.dUIElements['window'])


	def assignNucleus(self, *args):
		setNuc = mc.textFieldButtonGrp(self.dUIElements['txtNucleus'], q=1, text=True)
		if not setNuc:
			mc.warning('Set a nucleus first. Then select nCloth or nRigid you want assigned to it.')
		sel = mc.ls(sl=1)
		for s in sel:
			if mc.objectType(s)=='nCloth' or \
				mc.objectType(s) == 'nRigid' or \
					mc.objectType(s) == 'transform':
				print 'Assigning {} to {}'.format(s, setNuc)
				maya.mel.eval('assignNSolver %s;' % setNuc)
		if self.cArmy:
			try:
				self.initializeClass()
				self.cArmy.assignNucleus(nucleus=setNuc)
			except:
				pass


	def listNucleii(self, *args):
		nucleii = mc.ls(type='nucleus')
		for n in nucleii:
			mc.optionMenu(self.dUIElements['menuNucleii'], e=1)
			mc.menuItem(label=n)


	def remapAnimationToGroup(self, *args):
		self.initializeClass()
		# leeT
		sel = cmds.ls(sl=True)
		for each in sel:
			mc.file('/data/share/rigging/rigSandbox/alonz/simCycleSystem/nonDynWhiteSetup_climb3.mb',
					  loadReference=each, type='mayaBinary', options='v=0')


	def duplicateCollider(self, *args):
		# duplicate and connect collider
		collider = mc.textFieldButtonGrp(self.dUIElements['txtCollider'], q=1, text=True)
		# if nucleus set, create nRigid out of it assigned to the set nucleus
		setNuc = mc.textFieldButtonGrp(self.dUIElements['txtNucleus'], q=1, text=True)
		mc.setAttr(newCollider+'.v', 0)
		if setNuc:
			newNucBaseName = setNuc.split('_')[0]
			newCollider = duplicateAndConnect(collider, 'newCol')
			newCollider = mc.rename(newCollider,
									collider.replace('_simCycle','_'+newNucBaseName+'_simCycle'))
			newCollider = mc.rename(newCollider,
									newCollider.replace(newCollider.split('_')[-1], 'COL'))
			# Create nRigid on newCollider
			cascadeNode = 'c_cascade_INFO'
			if not mc.objExists(cascadeNode):
				mc.createNode('transform', n='c_cascade_INFO')
			mc.select(newCollider, r=1)
			nrg = create_nRigid(newCollider, setNuc)
			if 'COL' in newCollider:
				nrg = mc.rename(nrg, newCollider.replace('COL','NRG'))
			mc.parent(nrg, 'simCycle_ALL_COLLIDERS')
			nrgShp = mc.listRelatives(nrg, s=1)[0]
			mc.setAttr(nrgShp+'.thickness', 0.1)
			# print 'Assigning {} to {}'.format(newCollider, setNuc)
			# maya.mel.eval('assignNSolver %s;' % setNuc)

	
	def duplicateDrogonCollider(self, *args):
		collider = 'drogon_simCycle_COL'
		groundCollider = 'ground_simCycle_COL'
		colliders = [collider, groundCollider]
		for collider in colliders:
			# make new name based on set nucleus
			setNuc = mc.textFieldButtonGrp(self.dUIElements['txtNucleus'], q=1, text=True)
			newNucBaseName = setNuc.split('_')[0]
			newColliderName = collider.replace('_simCycle', '_' + newNucBaseName + '_simCycle')
			# duplicate and connect collider
			newCollider = duplicateAndConnect(collider, newColliderName, 0)
			# if nucleus set, create nRigid out of it assigned to the set nucleus
			mc.setAttr(newCollider+'.v', 0)
			if setNuc:
				# Create nRigid on newCollider
				cascadeNode = 'c_cascade_INFO'
				if not mc.objExists(cascadeNode):
					mc.createNode('transform', n='c_cascade_INFO')
				mc.select(newCollider, r=1)
				nrg = create_nRigid(newCollider, setNuc)
				nrg = mc.rename(nrg, newColliderName.replace('COL','NRG'))
				mc.parent(nrg, 'simCycle_ALL_COLLIDERS')
				nrgShp = mc.listRelatives(nrg, s=1)[0]
				mc.setAttr(nrgShp+'.thickness', 0.1)
				# set collider field to new collider
				mc.textFieldButtonGrp(self.dUIElements['txtCollider'], e=1, text=newColliderName)
				# cleanup
				colGrpName = newNucBaseName + '_COL_GRP'
				if not mc.objExists(colGrpName):
					mc.group(em=1, n=colGrpName, p='simCycle_ALL_COLLIDERS')
					mc.parent([newColliderName, nrg], colGrpName)
				else:
					mc.parent([newColliderName, nrg], colGrpName)
				if mc.objExists('nucleus1'):
					mc.delete('nucleus1')



	def selectHands(self, *args):
		self.initializeClass()
		self.cArmy.selectHands()

	
	def selectHandsHead(self, *args):
		self.initializeClass()
		self.cArmy.selectHandsHead()


	def selectFeet(self, *args):
		self.initializeClass()
		animations = ['climb', 'climb2', 'climb3', 'slashing', 'running', 'grabbing']
		animChoice = mc.radioCollection(self.dUIElements['rdoAnimChoice'], q=1, sl=1)
		self.cArmy.animChoice = animChoice
		self.cArmy.selectFeet()

	def selectChest(self, *args):
		self.initializeClass()
		self.cArmy.selectVertsOnAllWights([7])



	def selectHeels(self, *args):
		self.initializeClass()
		self.cArmy.selectVertsOnAllWights([83,20])



	
	
	

	def selectVerts(self, *args):
		self.initializeClass()
		sel = mc.ls(sl=1)
		if sel:
			self.cArmy.selectVertsOnAllWights(sel)





	def toggleAnim(self, *args):
		animChoice = mc.radioCollection(self.dUIElements['rdoAnimChoice'], q=1, sl=1)
		self.initializeClass()
		self.cArmy.switchAnimCache(animChoice)


	def setNucleus(self, *args):
		sel = mc.ls(sl=1)
		if sel:
			if mc.objectType(sel[0]) == 'nucleus':
				mc.textFieldButtonGrp(self.dUIElements['txtNucleus'], e=1, text=sel[0])
			else:
				mc.warning('Select only one nucleus, please.')


	def setVerts(self, *args):
		sel = mc.ls(sl=1)
		verts = []
		if sel:
			filteredVertList = mc.filterExpand(sel, sm=31)
			if filteredVertList:
				mc.textFieldButtonGrp(self.dUIElements['txtVerts'], e=1, text=str(filteredVertList))
			else:
				mc.warning('Select only verts, please.')

		# import pymel.core as pm
		# sel = pm.ls(sl=True, fl=True)
		# for s in sel:
		# print s.index()


	def setCollider(self, *args):
		sel = mc.ls(sl=1)
		if sel:
			if mc.objectType(sel[0]) == 'nRigid' or mc.objectType(sel[0]) == 'mesh' or mc.objectType(sel[0]) == 'transform':
				mc.textFieldButtonGrp(self.dUIElements['txtCollider'], e=1, text=sel[0])
			else:
				mc.warning('Select only one collider mesh, please.')


	
	def refresh(self, *args):
		self.initializeList()


	def selectBaseCtrl(self, *args):
		baseName = self.getSelected()
		try:
			mc.select(self.cArmy.baseCtrl)
			print self.cArmy.baseCtrl
		except:
			pass


	def initializeList(self, *args):
		mc.textScrollList(self.dUIElements['armyList'], e=1, removeAll=1)
		existingReferences = mc.ls('*_wight*RN')
		existingBaseNames = []
		for rn in existingReferences:
			existingBaseNames.append(rn.split('_')[0])
		existingBaseNames = list(set(existingBaseNames))
		# sort list alphabetically
		sortedList = sorted(existingBaseNames)
		# populate textScrollList
		for baseName in sortedList:
			mc.textScrollList(self.dUIElements['armyList'], e=1, append=baseName)

	
	def initializeClass(self, *args):
		listedName = mc.textScrollList(self.dUIElements['armyList'], q=1, si=1)
		print 'intiializing item from list: ', listedName[0]
		userDefinedName = listedName[0]
		#wightCount = int(mc.textFieldGrp(self.dUIElements['txtCount'], q=1, text=1))
		wightCount = len(mc.ls(userDefinedName+'_*RN'))
		bFormation = mc.checkBox(self.dUIElements['boxFormation'], q=1, v=1)
		self.cArmy = WightArmy(userDefinedName, wightCount, bFormation)
		self.cArmy.initializeSimCycleObject()


	def getSelected(self, *args):
		'''Run when list item is double clicked.'''
		listedName = mc.textScrollList(self.dUIElements['armyList'], q=1, si=1)
		if listedName:
			print 'list item ', listedName
			userDefinedName = listedName[0]
			#wightCount = int(mc.textFieldGrp(self.dUIElements['txtCount'], q=1, text=1))
			wightCount = len(mc.ls(userDefinedName+'_*RN'))
			bFormation = mc.checkBox(self.dUIElements['boxFormation'], q=1, v=1)
			self.cArmy = WightArmy(userDefinedName, wightCount, bFormation)
			self.cArmy.initializeSimCycleObject()
			try:
				mc.select(self.cArmy.clothMesh, r=1)
				mc.textFieldButtonGrp(self.dUIElements['txtNucleus'], e=1, text=self.cArmy.nucleus)
			except:
				pass
			return userDefinedName


	def createArmy(self, *args):
		animations = ['climb', 'climb2', 'climb3', 'slashing', 'grabbing']
		# gather creation parameters
		userDefinedName = mc.textFieldGrp(self.dUIElements['txtName'], q=1, text=1 )
		wightCount = int(mc.textFieldGrp(self.dUIElements['txtCount'], q=1, text=1))
		bFormation = mc.checkBox(self.dUIElements['boxFormation'], q=1, v=1)
		animChoice = mc.radioCollection(self.dUIElements['rdoAnimChoice'], q=1, sl=1)
		#bNewNucleus = mc.checkBox(self.dUIElements['boxNewNucleus'], q=1, v=1)
		# init army group and create
		self.cArmy = WightArmy(userDefinedName, wightCount, bFormation)
		#self.cArmy.bUseNewNucleus = True
		#self.cArmy.animChoice = animations[animChoice]
		self.cArmy.animChoice = animChoice
		self.cArmy.createSimCycleArmy()
		mc.textScrollList(self.dUIElements['armyList'], e=1, append=userDefinedName)


	def attachHands(self, *args):
		self.initializeClass()
		collider = mc.textFieldButtonGrp(self.dUIElements['txtCollider'], q=1, text=True)
		print 'Attaching hands to collider set to: ', collider
		verts = None
		if mc.textFieldButtonGrp(self.dUIElements['txtVerts'], q=1, text=True):
			verts = mc.ls(mc.textFieldButtonGrp(self.dUIElements['txtVerts'], q=1, text=True))
		self.cArmy.createPointToSurface(collider, verts)


	def excludeCollide(self, *args):
		sel = mc.ls(sl=True)
		if len(sel) == 2:
			name = '{}_{}'.format(sel[0].split('_')[1], ''.join(sel[1].split('_')[1]))
			const = createNConstraints(sel[0], sel[1], 'excludeCollide', name=name+'_P2S')
			if not const:
				return False
			constTrans = mc.listRelatives(const, p=1)[0]
			mc.parent(constTrans, 'simCycle_ALL_CONSTRAINTS')
		else:
			mc.warning('Improper selection! Select only 2 pbjects and try again.')


	def makeRunners(self, *args):
		self.initializeClass()
		self.cArmy.setupRunningWights()


	def makeMoshers(self, *args):
		self.initializeClass()
		self.cArmy.makeMoshers()


	def addChestRadial(self, *args):
		self.initializeClass()
		self.cArmy.addChestRadial()


	def setInitial(self, *args):
		self.cArmy.setInitialState()


	def deleteArmy(self, *args):
		self.initializeClass()
		self.cArmy.deleteSimArmy()
		# reset the list
		self.initializeList()


	def shotSetup(self, *args):
		setup_simCycleDragonBs()
		mc.button(self.dUIElements['btnShotSetup'], edit=1, enable=0)


	
######################################################################
simCycleUi()
############

	
		
'''
#
#
#######		usage examples

# init class
oArmy = WightArmy('wightz', 24, 1)
# create the group
oArmy.createSimCycleArmy()

oArmy.checkForExistingArmy()


# for making a pile - once the pile is settled run this
oArmy.setInitialState()

# create a group with formation set to True, then run the following to make runners
oArmy.setupRunningWights()


oArmy.deleteSimArmy()


# attach - make sure collider and are under the same solver
col = 'drogonHi_COL'
oArmy.createPointToSurface(col)





refFile = '/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-crowdCharge/maya/scenes/techanim/nonDynWhiteSetup.mb'

for i in mc.ls(sl=1):
	mc.file(refFile, rr=1, f=1, rfn=i)

mc.select('DROGON', hi=1)
selHi = mc.ls(sl=1)
modelGeoList = mc.ls(selHi, exactType='transform')
mc.select(modelGeoList, r=1)
for stuff in modelGeoList:
		try:
			mc.select(stuff, r=1)
		except:
			pass
		for obj in mc.ls(sl=1):
			if self.driverGeo not in obj:
				mc.setAttr(obj + '.v', 0)



import maya.mel as mm

createSculptAtPoint()

faces = ['drogon_simCycle_COL.f[83551]', 'drogon_simCycle_COL.f[121948]']


##

def createLocOnMesh(faces=None, sMesh=None):
	# rig.createFollicle(name='follicle', surface='', obj='', driver='follicle', connectType='', UV=[], parent='')
	# get one item selected
	sel = getSel(iMaxSel=1)
	if sel and 'vtx' in sel[0]:
		vtx = sel[0]
		sMesh = mc.ls(vtx, o=True)[0]
	else:
		mc.error('!!! Select only one vertex.')

	if not sLoc:
		sLoc = mc.spaceLocator(name='loc_vtx_01')[0]
	# Create stickies
	cmds.select(face01, r=True)
	sticky01 = RigToolbox.Core.GeoUtils.stickyTransform(locSide=side, locDescription=simGeoBaseName)
	sticky01 = cmds.rename(sticky01, sticky01 + '_01')


def createSculptDeformer(sParentTo=None):
	mc.select(cl=True)
	sSculptNodes = mc.sculpt(groupWithLocator=True)
	sSculpt = sSculptNodes[1]
	sSculptGrp = mc.listRelatives(sSculpt, parent=True)[0]
	mc.xform(sSculptGrp, cp=True)
	mc.select(sSculptGrp, r=True)
	return sSculptGrp


def createSculptAtPoint():

	# To use: select vert and run command. Then move and scale the sculpt nodes as needed, and assign members
	# using Edit Deformer Membership Tool.

	sLoc = createLocOnMesh()
	sSculptGrp = createSculptDeformer()
	mc.delete(mc.parentConstraint(sLoc, sSculptGrp, mo=False))
	mc.parent(sSculptGrp, sLoc)


def getSel(iMaxSel=1, bMultiSel=False):
	sel = mc.ls(sl=True)
	if not bMultiSel:
		if len(sel) == iMaxSel:
			return sel
		else:
			mc.warning(
				'\t !!! Wrong selection. Please select %i number of elements and re-run the tool. !!! ( %i objects were selected.)' % (
					iMaxSel, len(sel)))
	else:
		return sel
	
	
# to create exclude collide
from CfxToolbox.Utils import NCloth

sel = cmds.ls(sl=True)

#name = '{}_{}'.format(sel[0].split('_')[1], sel[1].split('_')[1])
name = '{}_{}'.format(sel[0].split('_')[1], ''.join(sel[1].split('_')))
NCloth.createNConstraints(sel, constraintType='excludeCollision', name=name)


New animations:
/home/jasons/maya/projects/default/cache/simCycles
/data/jobs/GT8/sequences/testShots/shots/GT8-testShots-crowdCharge/maya/scenes/techanim/nonDynWhiteSetup.mb
/data/share/rigging/rigSandbox/alonz/simCycle_baseShotFile.mb
/data/share/rigging/rigSandbox/alonz/simCycleSystem

'''
