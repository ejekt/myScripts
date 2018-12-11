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


