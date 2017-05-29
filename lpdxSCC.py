#!/usr/bin/python

import os, sys, math
from optparse import OptionParser

sys.path.append('..' + os.sep + 'lib')

from lpdxDataStr import *
from lpdxSCTools import *
from lpdxTools import *
from lpdxUITools import *
from lpdxParser import *

#  -c / --csv          : the comma separated file for output
#  -d / --dump         : the scan dump file

def main():

	optParser = OptionParser(usage="Usage: lpdxSCC.py <subcommand> [options] [args]\n\n\
Availible subcommands:\n\
\t msc (mass to sum composition) [mass] [sf-constraint]\n\
\t scm (sum composition to mass) [sum composition]\n\
\t sfsc (sf-constraint to sum composition) [sum composition]\n\
\t corrDP (compare 2 mass spectra with the dot-product correlation) [*.csv1] [*.csv2] [tolerance in ppm]\n\
\t corrPC (compare 2 mass spectra with the Pearson correlation) [*.csv1] [*.csv2] [tolerance in ppm]\n")

	optParser.add_option("-a", "--accuracy", dest="accuracy",
                  help="Set accuracy for sum composition calculation. Default is 5 ppm")

	(options, args) = optParser.parse_args()

	# open input mfql file
	if len(args) > 0:

		if options.accuracy:
				accuracy = 1000000 / float(options.accuracy)
		else:
			accuracy = 1000000 / 5

		if not args[0] or not args[1]:
			print "You forgot the arguments/subcommands!"
		else:
			if args[0] == "msc":
				elscp = parseElemSeq(args[2])
				rslt = lpdxSCTools.calcSFbyMass(float(args[1]), elscp, accuracy)
				rsltlist = []
				for i in rslt:
					rsltlist.append((i.getWeight(), i))
				#	rsltlist = sorted(rsltlist)
				if rsltlist == []:
					print "No sum composition found for %s with m/z %2.f" % (elscp, float(args[1]))
				for mass, scp in rsltlist:
					print "%.4f" % mass, scp, "error: %.4f" % (float(args[1]) - scp.getWeight())

			elif args[0] == "scm":
				print "Check, if you did not forget to add the charge!"
				elscp = parseElemSeq(args[1])
				rslt = elscp.getWeight()
				print "Weight is:", rslt, "; Double Bounds are:", elscp.get_DB()

			elif args[0] == "sfsc":
				elscp = parseElemSeq(args[1])
				for i in elscp.get_norangeElemSeq():
					print i, i.getWeight()

			elif args[0] == "corrDP":

				res = 1000000 / float(args[3])

				# open the spectra files
				s1 = open(args[1], 'r')
				spec1 = []
				for line in s1.readlines():
					spec1.append([float(line.split(',')[0]), float(line.split(',')[1])])
				s1.close()
				s2 = open(args[2], 'r')
				spec2 = []
				for line in s2.readlines():
					spec2.append([float(line.split(',')[0]), float(line.split(',')[1])])
				s2.close()

				# match both spectra. The result are vectors VSpec1/2 with the same dimension
				spec1.sort(cmp = lambda x, y: cmp(x[0], y[0]), reverse = False)
				spec2.sort(cmp = lambda x, y: cmp(x[0], y[0]), reverse = False)

				vSpec1 = []
				vSpec2 = []
				
				sum = 0
				peak = 0
				while peak < max(len(spec1), len(spec2)) - 1:
					
					t = spec1[peak][0] / res

					if spec2[peak][0] - t < spec1[peak][0] and spec1[peak][0] < spec2[peak][0] + t:
						if peak < len(spec1) - 1 and peak < len(spec2) - 1:
							if not (spec2[peak][0] - t < spec1[peak + 1][0] and spec1[peak + 1][0] < spec2[peak][0] + t):
								vSpec1.append(spec1[peak])
								vSpec2.append(spec2[peak])

							else:
								if abs(spec1[peak][0] - spec2[peak][0]) > abs(spec1[peak + 1][0] - spec2[peak][0]):
									vSpec1.append(spec1[peak])
									vSpec2.append([0.0, 0.0])
									spec2.insert(peak, [0.0, 0.0])

								else:
									vSpec1.append(spec1[peak])
									vSpec2.append(spec2[peak])

					elif spec1[peak][0] < spec2[peak][0]:
						vSpec1.append(spec1[peak])
						vSpec2.append([0.0, 0.0])
						spec2.insert(peak, [0.0, 0.0])

					elif spec1[peak][0] > spec2[peak][0]:
						vSpec1.append([0.0, 0.0])
						vSpec2.append(spec2[peak])
						spec1.insert(peak, [0.0, 0.0])

					sum += abs(spec1[peak][0] - spec2[peak][0])
					peak += 1

				# calc mean of vectors vSpec1/2 (which is the expectation value)
				sumInt = 0.0
				for p in vSpec1:
					sumInt += p[1]
				meanVSpec1 = sumInt / len(vSpec1)

				sumInt = 0.0
				for p in vSpec2:
					sumInt += p[1]
				meanVSpec2 = sumInt / len(vSpec2)

				# substract mean from the intensities of vSpec1/2 to center the 2 vectors
				for p in vSpec1:
					p[1] = p[1] - meanVSpec1

				for p in vSpec2:
					p[1] = p[1] - meanVSpec2
				
				# calc geometrical length of vectors vSpec1/2
				sum = 0.0
				for p in vSpec1:
					sum += p[1] * p[1]
				lenghtVSpec1 = math.sqrt(sum)

				sum = 0.0
				for p in vSpec2:
					sum += p[1] * p[1]
				lenghtVSpec2 = math.sqrt(sum)

				# calc the dot product
				sum = 0.0
				for index in range(len(vSpec1)):
					sum += vSpec1[index][1] * vSpec2[index][1]

				# calc the ankle
				phi = math.acos(sum / (lenghtVSpec1 * lenghtVSpec2))
				
				print 'dot product: %.4f, similarity: %.2f %%' % (sum, 100 - (phi * 100) / math.pi)

			elif args[0] == "corrPC":

				res = 1000000 / float(args[3])

				# open the spectra files
				s1 = open(args[1], 'r')
				spec1 = []
				for line in s1.readlines():
					spec1.append([float(line.split(',')[0]), float(line.split(',')[1])])
				s1.close()
				s2 = open(args[2], 'r')
				spec2 = []
				for line in s2.readlines():
					spec2.append([float(line.split(',')[0]), float(line.split(',')[1])])
				s2.close()

				# match both spectra. The result are vectors VSpec1/2 with the same dimension
				spec1.sort(cmp = lambda x, y: cmp(x[0], y[0]), reverse = False)
				spec2.sort(cmp = lambda x, y: cmp(x[0], y[0]), reverse = False)

				vSpec1 = []
				vSpec2 = []
				
				sum = 0
				peak = 0
				while peak < max(len(spec1), len(spec2)) - 1:
					
					t = spec1[peak][0] / res

					if spec2[peak][0] - t < spec1[peak][0] and spec1[peak][0] < spec2[peak][0] + t:
						if peak < len(spec1) - 1 and peak < len(spec2) - 1:
							if not (spec2[peak][0] - t < spec1[peak + 1][0] and spec1[peak + 1][0] < spec2[peak][0] + t):
								vSpec1.append(spec1[peak])
								vSpec2.append(spec2[peak])

							else:
								if abs(spec1[peak][0] - spec2[peak][0]) > abs(spec1[peak + 1][0] - spec2[peak][0]):
									vSpec1.append(spec1[peak])
									vSpec2.append([0.0, 0.0])
									spec2.insert(peak, [0.0, 0.0])

								else:
									vSpec1.append(spec1[peak])
									vSpec2.append(spec2[peak])

					elif spec1[peak][0] < spec2[peak][0]:
						vSpec1.append(spec1[peak])
						vSpec2.append([0.0, 0.0])
						spec2.insert(peak, [0.0, 0.0])

					elif spec1[peak][0] > spec2[peak][0]:
						vSpec1.append([0.0, 0.0])
						vSpec2.append(spec2[peak])
						spec1.insert(peak, [0.0, 0.0])

					sum += abs(spec1[peak][0] - spec2[peak][0])
					peak += 1

				# calc mean of vectors vSpec1/2 (which is the expectation value)
				sumVSpec1 = 0.0
				for p in vSpec1:
					sumVSpec1 += p[1]
				meanVSpec1 = sumVSpec1 / len(vSpec1)

				sumVSpec2 = 0.0
				for p in vSpec2:
					sumVSpec2 += p[1]
				meanVSpec2 = sumVSpec2 / len(vSpec2)

				# calc standard deviation sVSpec
				sumVSpec1quad = 0.0
				for p in vSpec1:
					sumVSpec1quad += p[1] * p[1]
				
				sumVSpec2quad = 0.0
				for p in vSpec2:
					sumVSpec2quad += p[1] * p[1]

				sVSpec1 = math.sqrt(len(vSpec1) * sumVSpec1quad - (sumVSpec1 * sumVSpec1))
				sVSpec2 = math.sqrt(len(vSpec2) * sumVSpec2quad - (sumVSpec2 * sumVSpec2))

				# substract mean from the intensities of vSpec1/2 to center the 2 vectors
				for p in vSpec1:
					p[1] = p[1] - meanVSpec1

				for p in vSpec2:
					p[1] = p[1] - meanVSpec2
				
				# calc the dot product
				sumDP = 0.0
				for index in range(len(vSpec1)):
					sumDP += vSpec1[index][1] * vSpec2[index][1]

				# calc Pearson correlation
				r = sumDP / ((len(vSpec1) - 1) * sVSpec1 * sVSpec2)

				# significance test
				t = r * math.sqrt((len(vSpec1) - 2) / math.sqrt(1 - (r * r)))

				print 'correlation r: %.4f,\nsignificance t: %.4f' % (r, t)
			else:
				print "No valid command:", args[0]

if __name__ == "__main__":
	main()	
