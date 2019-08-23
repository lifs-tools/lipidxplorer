import os
import re

from optparse import OptionParser
#import ConfigParser

from lx.exceptions import LipidXException
from lx.project import Project
from lx.options import Options

from lx.lxMain import startMFQL

def lpdxImportCLI(projpath = None):

	######################################################
	###              collect the options               ###

	#confParse = ConfigParser.ConfigParser()

	optParser = OptionParser(usage="Usage: lxrun.py [options] masterscan.sc [output.csv]\n")

	# import part
	optParser.add_option("-p", "--prj", dest="prj",
					help="path of the project file", metavar = "FILE")
	optParser.add_option("-i", "--ini", dest="ini",
					 help="path of the *.ini FILE if different from './lpdxImportSettings.ini'", metavar = "FILE")
	optParser.add_option("-s", "--setting", dest="setting",
					 help="section of a setting from *.ini file")
	optParser.add_option("-r", "--resultfile", dest="resultFile",
					 help="the name of the output file")
	#optParser.add_option("-m", "--masterscan", dest="masterScan",
	#				 help="the name of the output file")
	#optParser.add_option("-d", "--dump", dest="dumpMasterScanFile",
	#				 help="the name of the output file")

	# mfql part
	#optParser.add_option("-m", "--masterscan", dest="masterScanFile",
	#           	  	help="import MasterScan from FILE", metavar="FILE")
	optParser.add_option("-d", "--dump", dest="dumpMasterScan", action="store_true",
					 help="switch for dumping the content of the MasterScan", default=False)
	#optParser.add_option("-o", "--output", dest="output",
	#				 help="output the results with default settings to FILE", metavar="FILE")
	optParser.add_option("-c", "--complement", dest="complementMasterScan", action="store_true",
					 help="generates the complement MasterScan and saves it in the origin directory", default=False)
	optParser.add_option("-q", "--queries", dest="queries", type = "string", metavar = "ARG",
					help='the list of queries to run. Format is "query1.mfql, query2.mfql, ..."', default = "")
	optParser.add_option("--tab", dest="tabLimited", action="store_true", default=False,
					 help="output format is tab-limited")
	optParser.add_option("--compress", dest="compress", action="store_true", default=False,
					 help="no output of script names")
	optParser.add_option("--nohead", dest="noHead", action="store_true", default=False,
					 help="no output of tables head")
	optParser.add_option("--noPermutations", dest="noPermutations", action="store_true", default=False,
					 help="no permutations")
	optParser.add_option("--intensityCorrection", dest="intensityCorrection", action="store_true", default=False,
					 help="intensity correction")
	optParser.add_option("--isocorrectMS", dest="isotopicCorrectionMS", action = "store_true",
					 help="switch isotopic correction on", default = False)
	optParser.add_option("--isocorrectMSMS", dest="isotopicCorrectionMSMS", action = "store_true",
					 help="switch isotopic correction on", default = False)

	# import settings
	optParser.add_option("--MStolerance", dest="MStolerance",
					 help="overwrites/specifies 'MStolerance' of the *.ini file", metavar = "ARG")

	optParser.add_option("--MSMStolerance", dest="MSMStolerance",
					 help="overwrites/specifies 'MSMStolerance' of the *.ini file", metavar = "ARG")

	optParser.add_option("--MStoleranceType", dest="MStoleranceType",
					 help="overwrites/specifies 'MStoleranceType' of the *.ini file", metavar = "ARG")

	optParser.add_option("--MSMStoleranceType", dest="MSMStoleranceType",
					 help="overwrites/specifies 'MSMStoleranceType' of the *.ini file", metavar = "ARG")

	optParser.add_option("--MSfilter", dest="MSfilter",
				     help="overwrites/specifies 'MSfilter' of the *.ini file, minimum filter threshold for repeated ions in MS1, between 0 and 1", metavar = "ARG")

	optParser.add_option("--MSMSfilter", dest="MSMSfilter",
						 help="overwrites/specifies 'MSMSfilter' of the *.ini file, minimum filter threshold for repeated ions in MS2, between 0 and 1", metavar="ARG")

	optParser.add_option("--statistics", dest="statistics", action = "store_true", default = False,
					 help="statistics")

	optParser.add_option("--masterScanInSQL", dest="masterScanInSQL", action = "store_true", default = False,
					 help="masterScanInSQL")

	(cliOptions, args) = optParser.parse_args()

	if cliOptions.prj is None and projpath is None:
		if len(args) < 2:
			raise LipidXException("Wrong number of arguments")

	options = {}
	dictMFQL = {}
	project = Project()
	# the order of the following if-statements integrates prioraties


	project.options['masterScan'] = args[0]
		

	# if the settings are comming from the project file
	if projpath is not None:
		project.load(projpath)
		project.testOptions()
	elif not cliOptions.prj is None:
		project.load(cliOptions.prj)
		project.testOptions()
		#options = project.getOptions()

		dictMFQL = project.mfql

	else: # standard values

		project.options['setting'] = "command line"
		project.options['loopNr'] = 3
		project.options['alignmentMethodMS'] = "linear"
		project.options['alignmentMethodMSMS'] = "linear"
		project.options['scanAveragingMethod'] = "linear"

		project.options['masterScanRun'] = args[0]
		project.options['dumpMasterScanFile'] = os.path.splitext(args[0])[0] + '-dump.csv'
		project.options['importMSMS'] = True
		project.options['mzXML'] = True


	# optional option
	if cliOptions.resultFile is None:
		try:
			project.options['resultFile'] = args[1]
		except IndexError:
			print "ERROR: The result file was not specified. Use the option",
			print " -r."
	else:
		project.options['resultFile'] = cliOptions.resultFile

	# if the settings are used from the *.ini file
	if not cliOptions.ini is None:
		opts = Options()
		opts.initialize("%s" % cliOptions.ini)
		opts.setCurrentConfiguration(cliOptions.setting)
		opts.readConfiguration()
		for opt in opts.options.keys():
			project.options[opt] = opts.options[opt]

	# the settings come only from the command line (they overwrite existing options)
	if not cliOptions.dumpMasterScan is None:
		project.options['dumpMasterScan'] = cliOptions.dumpMasterScan
		project.options['dumpMasterScanFile'] = project.options['masterScan'].split('.')[0] + '-dump.csv'

	# the mfql files are comming from the commandline
	if cliOptions.__dict__.has_key("queries"):
		for q in cliOptions.queries.split(','):
			mfql_file = q.strip()
			if os.path.isdir(mfql_file): # collect the queries from the directory
				for root, dirs, files in os.walk(mfql_file):
					for f in files:
						if re.match('(.*\.mfql$)', f):
							n = os.path.join(root, f)
							l = n.split(os.sep)
							dictMFQL[l[-1]] = n
			else: # collect the queries from the string
				l = mfql_file.split(os.sep)
				dictMFQL[l[-1]] = mfql_file

	for opt in cliOptions.__dict__.keys():
		if not cliOptions.__dict__[opt] is None:
			project.options[opt] = cliOptions.__dict__[opt]

	project.options['queries'] = dictMFQL

	project.formatOptions()

	options = project.getOptions()

	# something is wrong with the result file, so I copy it again
	options['resultFile'] = project.options['resultFile']

	# overwrite the masterScanImport if given at the CLI
	#if 'masterScan' in cliOptions.__dict__.keys():
	#	options['masterScan'] = cliOptions.__dict__['masterScan']

	# print the options
	for k in sorted(options.keys()):
		if not options.isEmpty(k):
			print "{0:24} : {1:12}".format(k, str(options[k]))

	for m in sorted(dictMFQL.keys()):
		print "{0:24} : {1}".format(m, dictMFQL[m])

	###              collect the options               ###
	######################################################

	### start identification
	startMFQL(options = options, queries = dictMFQL)

if __name__ == "__main__":
	lpdxImportCLI()
	#(options, scan, importDir, output) = lpdxImportCLI()
