
from lx.mfql.runtimeStatic import TypeSFConstraint, TypeElementSequence
from lx.spectraContainer import SurveyEntry
from lx.spectraTools import saveSC

### generate a MasterScan from a MFQL file ###

def genMasterScan(mfqlObj):

	ms = mfqlObj.sc

	for varname in list(mfqlObj.dictDefinitionTable[mfqlObj.queryName].keys()):
		var = mfqlObj.dictDefinitionTable[mfqlObj.queryName][varname]

		if var.__class__ == TypeSFConstraint:
			for sc in var.elementSequence.get_norangeElemSeq():
				ms.listSurveyEntry.append(
					SurveyEntry(
						msmass = sc.getWeight(),
						smpl = {'Generated' : 1},
						peaks = [],
						charge = var.elementSequence.charge,
						polarity = var.elementSequence.charge,
						dictScans = {'Generated' : 1},
						msms = None,
						dictBasePeakIntensity = {'Generated' : 1},
						noise = 0,
						resolution = 100000.0,
						dictNoise = {'Generated' : 0},
						dictResolution = {'Generated' : 100000.0}
						)
					)


def saveMasterScan(mfqlObj):
	saveSC(mfqlObj.sc, mfqlObj.options['masterScanFile'])
