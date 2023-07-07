from copy import deepcopy

from lx.clustering import HierarchicalClustering
from lx.mfql.runtimeStatic import TypeTolerance
from lx.spectraContainer import (
    SurveyEntry,
    MSMS,
    MSMSEntry,
    MSMass,
    set_PrecurmassFromMSMS,
)
from lx.tools import sortDictKeys
from lx.exceptions import LipidXException
from math import sqrt
from statistics import mean


# peakCluster for merging peaks
class peakCluster:
    def __init__(
        self,
        mass=None,
        dictIntensity=None,
        polarity=None,
        charge=None,
        dictScans=None,
    ):
        self.mass = mass
        self.dictIntensity = dictIntensity
        self.charge = charge
        self.polarity = polarity
        self.peakList = []
        self.dictScans = dictScans

    def __repr__(self):
        return repr(self.mass) + " \n -> " + repr(self.peakList)

    def __cmp__(self, other):
        return self.cmp(self.mass, other.mass)

    # https://stackoverflow.com/questions/8276983/why-cant-i-use-the-method-cmp-in-python-3-as-for-python-2
    @staticmethod
    def cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    # def findPeak(self, mass = None, key = None):
    def findPeak(self, key=None):
        """Find and return a the peak with the given sample
        name (key) from the peakList."""

        if key:
            for i in self.peakList:
                for k in list(i[1].keys()):
                    if k == key:
                        return i
            return None


class specMSMSEntry:
    def __init__(self, precurmass, listMSMS, scanCount=1):
        self.precurmass = precurmass
        self.listMSMS = listMSMS
        self.scanCount = scanCount

    def __repr__(self):
        return "%.4f -> %s" % (self.precurmass, repr(self.listMSMS))

    def __cmp__(self, other):
        return self.cmp(self.precurmass, other.precurmass)
        # https://stackoverflow.com/questions/8276983/why-cant-i-use-the-method-cmp-in-python-3-as-for-python-2

    @staticmethod
    def cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0


class specMSEntry:
    def __init__(self, avgPrecurmass, sample, listMSMS):
        self.avgPrecurmass = avgPrecurmass
        # self.dictSample = {sample : listMSMS}
        self.listMasses = [[avgPrecurmass, {sample: listMSMS}]]

    def __cmp__(self, other):
        return self.cmp(self.avgPrecurmass, other.avgPrecurmass)
        # https://stackoverflow.com/questions/8276983/why-cant-i-use-the-method-cmp-in-python-3-as-for-python-2

    @staticmethod
    def cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __repr__(self):
        str = "%.4f -> " % (self.avgPrecurmass)
        for i in self.listMasses:
            str += "%s, " % list(i[1].keys())
        return str + "\n"


def printClusters(keys, listClusters):
    """This is for debugging the alignment functions. It
    just prints the resulting alignment."""

    for cl in listClusters:
        str = ""
        for sample in keys:
            if sample in cl:
                if cl[sample].content:
                    str += "  {0:>9.4f} - {1:>12.1f}  ".format(
                        cl[sample].mass, cl[sample].content["intensity"]
                    )
                    # str +=  "  %.4f  " % cl[sample].content['intensity']
                else:
                    try:
                        str += " /{0:>9.4f} - {1:>12}/ ".format(
                            cl[sample].mass, ""
                        )
                    except TypeError:
                        print("TypeError:", cl[sample].mass)
            else:
                str += " /{0:>9} - {1:>12}/ ".format("empty", "")
        print(str)


def avgPrecursor(content):
    precurmass = 0
    msms = []
    entries = []
    numEntries = 0
    for entry in content:
        precurmass += entry.precurmass
        msms += entry.msms
        entries += entry.entries
        numEntries += 1

    avgPrecurmass = precurmass / len(content)

    # def __init__(self, mass, retentionTime, charge, polarity, fileName, MSMSthreshold = None, table = None):
    output = MSMS(
        avgPrecurmass, 0.0, None, content[0].polarity, content[0].fileName
    )

    return output


def avgMSMSFragment(content):
    intensity = 0
    for entry in content:
        intensity += entry["intensity"]

    avgIntensity = intensity / len(content)

    output = {"intensity": avgIntensity, "polarity": content[0]["polarity"]}

    return output


class specEntry:
    def __init__(self, mass=None, content={}, charge=None, sample=None):
        self.mass = mass
        self.content = content
        self.sample = sample
        self.charge = charge

    def __repr__(self):
        txt = "{0:6}".format(self.mass)
        for k in list(self.content.keys()):
            txt += " > {0:12}: {1:6}".format(k, str(self.content[k]))
        return txt

    def __cmp__(self, other):
        return self.cmp(self.mass, other.mass)
        # https://stackoverflow.com/questions/8276983/why-cant-i-use-the-method-cmp-in-python-3-as-for-python-2

    @staticmethod
    def cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __lt__(self, other):
        return self.mass < other.mass


def mkSurveyHeuristic(
    sc,
    polarity,
    numLoops=None,
    deltaRes=0,
    minocc=None,
    msThreshold=None,
    checkoccupation=True,
):
    """Align the MS spectra."""

    listPolarity = []
    for k in sc.listSamples:
        if sc.dictSamples[k].polarity not in listPolarity:
            listPolarity.append(sc.dictSamples[k].polarity)

    if polarity == "+":
        polarity_int = 1
    else:
        polarity_int = -1

    # get the base peak dictionary
    dictBasePeakIntensity_MS = {}
    for sample in sc.listSamples:
        dictBasePeakIntensity_MS[sample] = sc.dictSamples[sample].base_peak_ms1
    sc.dictBasePeakIntensity_MS = dictBasePeakIntensity_MS

    for charge in listPolarity:
        dictSpecEntry = {}

        for sample in sc.listSamples:
            # generate a list of specEntry elements
            dictSpecEntry[sample] = []
            for i in sorted(sc.dictSamples[sample].listPrecurmass):
                dictSpecEntry[sample].append(
                    specEntry(mass=i.precurmass, content=i.intensity)
                )

        listClusters = heuristicAlignment(
            list(dictSpecEntry.keys()),
            dictSpecEntry,
            # TypeTolerance('res', sc.options['MSresolution']),
            sc.options["MSresolution"],
            deltaRes=sc.options["MSresolutionDelta"],
            minMass=sc.options["MSmassrange"][0],
        )

        # generate MSMSEntry
        for i in listClusters:
            dictScans = {}.fromkeys(sc.listSamples)
            numOccSmpl = 0
            isEmpty = True
            dictIntensity = {}
            peakList = []
            for sample in sc.listSamples:
                try:
                    if i[sample].content:
                        numOccSmpl += 1
                        dictIntensity[sample] = i[sample].content
                        peakList.append(
                            [i[sample].mass, {sample: i[sample].content}]
                        )
                        isEmpty = False
                    else:
                        dictIntensity[sample] = 0.0

                except KeyError:
                    dictIntensity[sample] = 0.0

                dictScans[sample] = 1

            if not isEmpty:
                if checkoccupation:
                    checkOcc = False
                    checkOcc = sc.checkOccupation(
                        dictIntensity,
                        dictScans,
                        occThr=sc.options["MSminOccupation"],
                        mode="MS",
                        threshold=sc.options["MSthreshold"],
                        threshold_type=sc.options["MSthresholdType"],
                        dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                    )

                    if checkOcc:
                        sc.listSurveyEntry.append(
                            SurveyEntry(
                                msmass=i[sample].mass,
                                smpl=dictIntensity,
                                peaks=peakList,
                                charge=None,
                                polarity=polarity_int,
                                dictScans=dictScans,
                                dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                            )
                        )

                else:
                    sc.listSurveyEntry.append(
                        SurveyEntry(
                            msmass=i[sample].mass,
                            smpl=dictIntensity,
                            peaks=peakList,
                            charge=None,
                            polarity=polarity_int,
                            dictScans=dictScans,
                            dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                        )
                    )


def mkSurveyLinear(
    sc,
    listPolarity,
    numLoops=None,
    deltaRes=0,
    minocc=None,
    checkoccupation=True,
    bin_res=False,
    collapse=False,
    **kwargs
):
    """Align the MS spectra."""

    # get the base peak dictionary
    dictBasePeakIntensity_MS = {}
    for sample in sc.listSamples:
        dictBasePeakIntensity_MS[sample] = sc.dictSamples[sample].base_peak_ms1
    sc.dictBasePeakIntensity_MS = dictBasePeakIntensity_MS

    # store smalles mass
    if sc.options["MSmassrange"]:
        minMass = sc.options["MSmassrange"][0]
        maxMass = sc.options["MSmassrange"][1]
    else:
        minMass = 0
        maxMass = 100000

    #### try with the standard algorithm ###
    # dictSpecEntry = {}
    # for key in sc.listSamples:
    # 	dictSpecEntry[key] = []
    # 	for i in sc.dictSamples[key].listPrecurmass:
    # 		if i.precurmass >= minMass and i.precurmass <= maxMass:
    # 			dictSpecEntry[key].append(specEntry(
    # 				mass = i.precurmass,
    # 				content = {'sample' : key,
    # 					'intensity' : i.intensity,
    # 					'polarity' : i.polarity,
    # 					'scans' : i.scanCount}))

    # listClusters = linearAlignment(dictSpecEntry.keys(),
    # 	dictSpecEntry,
    # 	sc.options['MSresolution'],
    # 	merge = mergeSumIntensity, # to be confirmed !!!
    # 	mergeTolerance = sc.options['MSresolution'],
    # 	mergeDeltaRes = sc.options['MSresolutionDelta'])

    # printClusters(dictSpecEntry.keys(), listClusters)

    # return None

    for polarity in listPolarity:
        ### this stores the precursors as tab-separated file ###
        # for key in sc.listSamples:
        # 	f = open('pr-' + key[:-6] + '.txt', 'w')
        # 	for entry in sc.dictSamples[key].listPrecurmass:
        # 		f.write("%.6f\t%.4f\n" % (entry.precurmass, entry.intensity))
        # 	f.close()
        ### the end                                          ###

        ### generate list of all MSmasses ###

        # initialize listMSSpec
        listMSSpec = []
        for i in range(numLoops + 1):
            listMSSpec.append([])

        for key in sc.dictSamples:
            if sc.dictSamples[key].polarity == polarity:
                for i in sc.dictSamples[key].listPrecurmass:
                    if i.precurmass >= minMass and i.precurmass <= maxMass:
                        listMSSpec[0].append(
                            peakCluster(
                                mass=i.precurmass,
                                dictIntensity={i.smpl: i.intensity},
                                charge=i.charge,
                                polarity=polarity,
                                dictScans={i.smpl: i.scanCount},
                            )
                        )
                        listMSSpec[0][-1].peakList.append(
                            [i.precurmass, {i.smpl: i.intensity}]
                        )

        # if no mass found for a given charge, continues
        if listMSSpec[0] == []:
            continue

        if len(listMSSpec[0]) == 1:
            entry = listMSSpec[0][0]

            for k in sc.listSamples:
                if not k in entry.dictIntensity:
                    entry.dictIntensity[k] = 0.0
                if not k in entry.dictScans:
                    entry.dictScans[k] = 1

            if checkoccupation:
                checkOcc = sc.checkOccupation(
                    entry.dictIntensity,
                    entry.dictScans,
                    occThr=sc.options["MSminOccupation"],
                    mode="MS",
                    dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                    threshold=sc.options["MSthreshold"],
                    threshold_type=sc.options["MSthresholdType"],
                )

                if checkOcc:
                    sc.listSurveyEntry.append(
                        SurveyEntry(
                            msmass=entry.mass,
                            smpl=entry.dictIntensity,
                            peaks=entry.peakList,
                            charge=None,
                            polarity=polarity,
                            dictScans=entry.dictScans,
                            dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                        )
                    )

            else:
                sc.listSurveyEntry.append(
                    SurveyEntry(
                        msmass=entry.mass,
                        smpl=entry.dictIntensity,
                        peaks=entry.peakList,
                        charge=None,
                        polarity=polarity,
                        dictScans=entry.dictScans,
                        dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                    )
                )

            return True

        listMSSpec[0].sort()

        if bin_res:
            listMSSpec[0] = list(reversed(listMSSpec[0]))
            binsize = len(sc.dictSamples)
            sorted_mass = sorted((s.mass for s in listMSSpec[0]), reverse=True)
            up_to = binsize * 10 if binsize * 10 < len(sorted_mass) else -1
            diffs = [
                sorted_mass[i] - sorted_mass[i + 1]
                for i, _ in enumerate(sorted_mass[:up_to])
            ]  # hope to find at least one full bin here
            s_diffs = sorted(diffs)  # diffs are coorelated to the resolution
            m = mean(s_diffs)
            s_diffs = [d for d in s_diffs if d < m]  # remove outliers
            # m1 = mean(s_diffs)
            # s_diffs = [d for d in s_diffs if d > m1 ] #remove outliers
            # diffs = [d for d in s_diffs if d > s_diffs[0]*2 and d < s_diffs[-1] * 0.5]
            # binres = mean(diffs[:binsize]) * 2 if diffs else 0.002
            binres = mean(s_diffs) if diffs else 0.0002
            # listMSSpec[0] = list(reversed(listMSSpec[0]))
            # mstolerance = sc.options['MStolerance']
            # if mstolerance.kind == 'da':
            # 	binres = mstolerance.da * 2
            # elif mstolerance.kind == 'ppm':
            # 	binres = max((s.mass for s in listMSSpec[0])) /(100000 / mstolerance.ppm)
            # 	binres = binres * 2
            # binsize = len(sc.dictSamples)
            binres_og = binres
            newres1 = None

            sc.options["calcSelectionWindow"] = max(
                sc.options.get("calcSelectionWindow", 0.1), m * 4
            )  # average distance between peaks , 0.5 because thats the defult from orbitrap

        # sort precursor masses by intensity
        # listMSmassIntensity = sorted(listMSmass, cmp = sortPrecursorMasses)
        # TODO: do alignment according to sorted list by intensity

        for count in range(numLoops):
            current = 0
            lnext = []
            binres = binres_og if bin_res else None

            while current < (len(listMSSpec[count]) - 1):
                # calc mass window for cluster
                if sc.options["MSresolution"].kind != "Da":
                    res = (
                        sc.options["MSresolution"].tolerance
                        + (listMSSpec[count][current].mass - minMass)
                        * deltaRes
                    )
                    # res = sc.options['MSresolution'].getTinDA(listMSSpec[count][current].mass
                else:
                    raise LipidXException(
                        "Tolerance value for averaging MS has to be resolution"
                    )

                partialRes = listMSSpec[count][current].mass / res

                # routine for collecting all masses which are in partialRes
                # index = 1
                lrsltMSMS = [listMSSpec[count][current]]

                # instead of counting with 'current' we just delete the peak which is
                # in the bin from the spectra list. Thus we save some space.
                del listMSSpec[count][current]

                lastEntry = None

                if bin_res:
                    if (
                        binres == binres_og and newres1
                    ):  # for when the loop restart
                        binres = newres1
                        # bin_at_mass = lrsltMSMS[0].mass  to reduce  just based on mass
                    partialRes = binres  # * (lrsltMSMS[0].mass/bin_at_mass)  to reduce  just based on mass

                while (
                    abs(listMSSpec[count][current].mass - lrsltMSMS[0].mass)
                    < partialRes
                ):
                    if (
                        bin_res
                        and binsize > 1
                        and bin_res
                        and len(listMSSpec[count][current].peakList)
                        >= binsize * 0.95
                    ):
                        break
                    lrsltMSMS.append(listMSSpec[count][current])
                    del listMSSpec[count][current]

                    if listMSSpec[count] == []:
                        lastEntry = lrsltMSMS[-1]
                        break

                if bin_res and len(lrsltMSMS) >= binsize * 0.95:
                    newres = max((p.mass for p in lrsltMSMS)) - min(
                        (p.mass for p in lrsltMSMS)
                    )
                    newres = newres * 10  # for a looser fit between spectra
                    if newres < binres and newres > 0.00001:
                        binres = newres
                        if newres1 is None:
                            newres1 = newres
                        # bin_at_mass = lrsltMSMS[0].mass  to reduce  just based on mass

                ### check error
                # if there should be overlapping errors, correct them by checking for
                # every precursor mass which should go into the cluster, if the sample
                # is already there. If yes, then save its position and start with this
                # positition in the next round
                # count = 0
                # for i in range(len(lrsltMSMS)):
                # 	for j in lrsltMSMS[:i:]:
                # 		if intersect(lrsltMSMS[i][1].keys(), j[1].keys()) != []:
                # 			count += 1
                ### end check error

                # current += index

                # calc average of cluster
                sum = 0
                avg = 0
                length = 0
                for i in lrsltMSMS:
                    for j in i.peakList:
                        sum += j[0]
                        length += 1
                avg = sum / length

                # calc average of count
                # sum = 0
                # for i in lrsltMSMS:
                # 	sum += i.count
                # avgCount = sum / len(lrsltMSMS)

                # collect the cluster masses intensities
                dictIntensity = {}
                countIntensity = {}
                dictScans = {}
                for i in lrsltMSMS:
                    for k in list(i.dictIntensity.keys()):
                        if k not in countIntensity:
                            countIntensity[k] = 1
                        else:
                            countIntensity[k] += 1

                        ### TODO: Attention, the method of just summing the
                        ### intensities for "too-close" peaks in on sample lead to
                        ### strong differences in the result (at least the unit test does
                        ### not accept the result). This has be checked and confirmed.
                        if k not in dictIntensity:
                            dictIntensity[k] = i.dictIntensity[k]
                        else:
                            dictIntensity[k] += i.dictIntensity[k]

                        if k not in dictScans:
                            dictScans[k] = i.dictScans[k]

                    ## take average intensity
                    # for k in i.dictIntensity.keys():
                    # 	dictIntensity[k] = dictIntensity[k] / countIntensity[k]

                # is it not the last round?
                if count != numLoops - 1:
                    # store list for a maybe second round
                    # for intensKey in dictIntensity.keys():
                    listMSSpec[count + 1].append(
                        peakCluster(
                            mass=avg,
                            dictIntensity=dictIntensity,
                            polarity=polarity,
                            charge=None,
                            dictScans=dictScans,
                        )
                    )
                    for e in lrsltMSMS:
                        for p in e.peakList:
                            if len(list(p[1].keys())) < 2 and not listMSSpec[
                                count + 1
                            ][-1].findPeak(key=list(p[1].keys())[0]):
                                listMSSpec[count + 1][-1].peakList.append(p)

                    # if current == len(listMSSpec[count]) - 1:
                    # if listMSSpec[count] == []:
                    if not lastEntry is None:
                        # store last for a maybe second round
                        # for intensKey in dictIntensity.keys():
                        if not lastEntry in lrsltMSMS:
                            listMSSpec[count + 1].append(
                                peakCluster(
                                    mass=lastEntry.mass,
                                    dictIntensity=lastEntry.dictIntensity,
                                    charge=None,
                                    polarity=polarity,
                                    dictScans=lastEntry.dictScans,
                                )
                            )
                            listMSSpec[count + 1][
                                -1
                            ].peakList = lastEntry.peakList

                    else:
                        for e in lrsltMSMS:
                            for p in e.peakList:
                                if len(
                                    list(p[1].keys())
                                ) < 2 and not listMSSpec[count + 1][
                                    -1
                                ].findPeak(
                                    key=list(p[1].keys())[0]
                                ):
                                    listMSSpec[count + 1][-1].peakList.append(
                                        p
                                    )

                # it is the last round
                else:
                    listMSSpec[count + 1].append(
                        peakCluster(
                            mass=avg,
                            dictIntensity=dictIntensity,
                            charge=None,
                            polarity=polarity,
                            dictScans=dictScans,
                        )
                    )

                    for e in lrsltMSMS:
                        for p in e.peakList:
                            # only add peaks which are not aligned
                            if len(list(p[1].keys())) < 2 and not listMSSpec[
                                count + 1
                            ][-1].findPeak(key=list(p[1].keys())[0]):
                                listMSSpec[count + 1][-1].peakList.append(p)

                    if current == len(listMSSpec[count]) - 1:
                        # store last for a maybe second round
                        # for intensKey in dictIntensity.keys():
                        if not listMSSpec[count][current] in lrsltMSMS:
                            if (
                                listMSSpec[count + 1][-1].mass
                                != listMSSpec[count][-1].mass
                            ):
                                listMSSpec[count + 1].append(
                                    peakCluster(
                                        mass=listMSSpec[count][-1].mass,
                                        dictIntensity=listMSSpec[count][
                                            -1
                                        ].dictIntensity,
                                        charge=None,
                                        polarity=polarity,
                                        dictScans=listMSSpec[count][
                                            -1
                                        ].dictScans,
                                    )
                                )
                                listMSSpec[count + 1][
                                    -1
                                ].peakList = listMSSpec[count][-1].peakList

                    else:
                        for e in lrsltMSMS:
                            for p in e.peakList:
                                if len(
                                    list(p[1].keys())
                                ) < 2 and not listMSSpec[count + 1][
                                    -1
                                ].findPeak(
                                    key=list(p[1].keys())[0]
                                ):
                                    listMSSpec[count + 1][-1].peakList.append(
                                        p
                                    )

                    # assert that every peak has the right distance to its predesessor
                    # if len(listMSSpec[count + 1]) > 1:
                    # 	assert listMSSpec[count + 1][-1].mass - listMSSpec[count + 1][-2].mass >= partialRes

        ### check if minimum occupation is fullfilled ###
        listMSSpec[-1] = reversed(listMSSpec[-1])
        for entry in listMSSpec[-1]:
            for k in sc.listSamples:
                if not k in entry.dictIntensity:
                    entry.dictIntensity[k] = 0.0
                if not k in entry.dictScans:
                    entry.dictScans[k] = 1

            if checkoccupation:
                checkOcc = sc.checkOccupation(
                    entry.dictIntensity,
                    entry.dictScans,
                    occThr=sc.options["MSminOccupation"],
                    mode="MS",
                    dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                    threshold=sc.options["MSthreshold"],
                    threshold_type=sc.options["MSthresholdType"],
                )

                if checkOcc:
                    sc.listSurveyEntry.append(
                        SurveyEntry(
                            msmass=entry.mass,
                            smpl=entry.dictIntensity,
                            peaks=entry.peakList,
                            charge=None,
                            polarity=polarity,
                            dictScans=entry.dictScans,
                            dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                        )
                    )

            else:
                sc.listSurveyEntry.append(
                    SurveyEntry(
                        msmass=entry.mass,
                        smpl=entry.dictIntensity,
                        peaks=entry.peakList,
                        charge=None,
                        polarity=polarity,
                        dictScans=entry.dictScans,
                        dictBasePeakIntensity=sc.dictBasePeakIntensity_MS,
                    )
                )

        del listMSSpec
    
    if kwargs.get("make_intermediate_output", False):
        # datafreame before collapese
        from pathlib import Path
        from lx.spectraTools import saveSC
        destination = Path(sc.options['importDir']) / Path("lx1_masterscan_aligned_spectra.pkl")
        saveSC(sc, destination)

    if collapse:
        sc.listSurveyEntry = collape_join_adjecent_clusters(sc.listSurveyEntry)
        if kwargs.get("make_intermediate_output", False):
            destination = Path(sc.options['importDir']) / Path("lx1_masterscan_collapsed_spectra.pkl")
            saveSC(sc, destination)




def mkSurveyHierarchical(
    sc, listPolarity, numLoops=None, deltaRes=0, minocc=None, msThreshold=None
):
    """Align the MS spectra."""

    resolution = sc.options["MSresolution"]

    output = []

    for polarity in listPolarity:
        if polarity > 0:
            p = "+"
        else:
            p = "-"

        # generate list of all sample names

    cl = hclusterHeuristic(sc.listSamples, sc.dictSamples, resolution)


def make_lx1_ms2_to_ms1(msmsLists, scan):
    import pandas as pd 
    from pathlib import Path
    def peaks_generator():
        for precursor_str, surveyEntries in msmsLists.items():
            for se in surveyEntries[0].se:
                ms1_mass = se.precurmass
                ms2_precursor = precursor_str
                yield (ms1_mass, ms2_precursor)
    df = pd.DataFrame(peaks_generator())
    df.rename(
        columns={
            0: "ms1_mass",
            1: "ms2_precursor",
            },
        inplace=True,)
    destination = Path(scan.options["importDir"]) / Path("lx1_ms2_to_ms1.pkl")
    df.to_pickle(destination)


def make_lx1_ms2_averages(msmsLists, scan):
    import pandas as pd
    from  pathlib import Path
    def peaks_generator():
        for precursor_str, cluster in msmsLists.items():
            precurmass = precursor_str
            for avgpeak in cluster:
                avgmass = avgpeak.mass
                for peak in avgpeak.peaks:
                    mass = peak[0]
                    for spectra, inty in peak[1].items():
                        peak = (
                            spectra,
                            avgmass,
                            None,
                            mass,
                            inty,
                            precurmass
                        )
                        yield peak
    df = pd.DataFrame(peaks_generator())
    df.rename(
        columns={
            0: "specName",
            1: "cluster",
            2: "retention_times_str",
            3: "mass",
            4: "intensity",
            5: "precursor",
        },
        inplace=True,
        )
    df["specName"] = df["specName"].astype('category')
    df["cluster"] = df["cluster"].astype('category')
    df["retention_times_str"] = df["retention_times_str"].astype('category')
    df["precursor"] = df["precursor"].astype('category')
    destination = Path(scan.options["importDir"]) / Path("lx1_ms2_averages.pkl")
    df.to_pickle(destination)

def make_lx1_ms2_groups(listClusters, scan):
    import pandas as pd
    from pathlib import Path
    def peaks_generator():
        for cluster_no, cluster in enumerate(listClusters):
            for filename, spectra in cluster.items():
                cluster = cluster_no #spectra.mass #NOTE listClusters[-1] does not have same mass in cluster
                precurmass = spectra.mass # spectra.content['MSMS'].precurmass
                scans_str = ' '.join(map(str,spectra.content['MSMS'].retentionTime))
                for mass, inty in spectra.content['MSMS'].entries:
                    peak = (
                        filename,
                        cluster,
                        scans_str,
                        mass,
                        inty,
                        precurmass
                    )
                    yield peak
    df = pd.DataFrame(peaks_generator())
    df.rename(
        columns={
            0: "specName",
            1: "cluster",
            2: "retention_times_str",
            3: "mass",
            4: "intensity",
            5: "precursor",
        },
        inplace=True,
        )
    df["specName"] = df["specName"].astype('category')
    df["cluster"] = df["cluster"].astype('category')
    df["retention_times_str"] = df["retention_times_str"].astype('category')
    df["precursor"] = df["precursor"].astype('category')
    destination = Path(scan.options["importDir"]) / Path("lx1_ms2_groups.pkl")
    df.to_pickle(destination)

def mkMSMSEntriesLinear_new(
    scan,
    listPolarity,
    numLoops=None,
    isPIS=False,
    relative=None,
    bin_res=False,
    collapse=False,
    **kwargs
):
    ################################################################
    ###	merge MS/MS experiments if there are more than one for a ###
    ### precursor mass                                           ###
    ################################################################

    secondStep = True
    numLoops = 3
    

    msmsThreshold = scan.options["MSMSthreshold"]
    if bin_res:
        tolerance = TypeTolerance("Da", scan.options["calcSelectionWindow"])
        window = (
            scan.options["calcSelectionWindow"] * 2
        )  # maybe its too small maybe use * 2?
        deltaRes = None
    elif not isPIS:
        tolerance = TypeTolerance("Da", scan.options["selectionWindow"])
        # tolerance = scan.options['MSresolution']
        window = scan.options["selectionWindow"] / 2
        deltaRes = None
    else:
        tolerance = scan.options["MSMSresolution"]
        deltaRes = scan.options["MSMSresolutionDelta"]
        window = scan.options["MSMSresolution"]

    listPolarity = []
    for k in scan.listSamples:
        if scan.dictSamples[k].polarity not in listPolarity:
            listPolarity.append(scan.dictSamples[k].polarity)

    # check if there are MS/MS spectra at all
    msmsThere = False
    for polarity in listPolarity:
        for sample in scan.listSamples:
            # TODO: This has to be tested ASAP
            if (
                scan.dictSamples[sample].listMsms != []
                and scan.dictSamples[sample].polarity == polarity
            ):
                msmsThere = True

    # double check if the MSMSresolution was set
    if msmsThere:
        if (
            not scan.options["MSMSresolution"]
            or scan.options["MSMSresolution"] == 0
        ):
            raise LipidXException("no resolution setting given for MS/MS.")

        if (
            not scan.options["selectionWindow"]
            or scan.options["selectionWindow"] == 0
        ):
            raise LipidXException("no selection window given.")

    ### go seperately for the polarity ###
    for polarity in listPolarity:
        ############################################################
        ### Cluster the precursor masses and average MS/MS scans ###

        dictMSMS = {}
        listAt = []

        dictSpecEntry = {}
        for sample in scan.listSamples:
            if msmsThere:
                # generate a list of specEntry elements
                dictSpecEntry[sample] = []
                scan.dictSamples[sample].listMsms.sort()
                for i in scan.dictSamples[sample].listMsms:
                    dictSpecEntry[sample].append(
                        specEntry(
                            mass=i.precurmass,
                            content={"sample": sample, "MSMS": i},
                        )
                    )

        if msmsThere:
            listClusters = linearAlignment(
                list(dictSpecEntry.keys()),
                dictSpecEntry,
                tolerance,
                merge=mergeListMsms,
                mergeTolerance=scan.options["MSMSresolution"],
                mergeDeltaRes=scan.options["MSMSresolutionDelta"],
                bintolerance=scan.options["MSMStolerance"],
                res_by_fullbin=scan.options["alignmentMethodMSMS"]
                == "calctol",
            )

            if kwargs.get("make_intermediate_output", False):
                make_lx1_ms2_groups(listClusters, scan)


            # listClusters = r_linearAlignment(
            #     list(dictSpecEntry.keys()),
            #     dictSpecEntry,
            #     tolerance,
            #     merge=mergeListMsms,
            #     mergeTolerance=scan.options["MSMSresolution"],
            #     mergeDeltaRes=scan.options["MSMSresolutionDelta"],
            #     bintolerance=scan.options["MSMStolerance"],
            #     res_by_fullbin=scan.options["alignmentMethodMSMS"] == "calctol",
            # )

        else:
            listClusters = False

        ### Cluster the precursor masses and average MS/MS scans ###
        ############################################################

        if listClusters:
            #### check again with this debugging output!
            # for sample in dictSpecEntry.keys():#cl.keys():
            # 	print sample,
            # print ''
            # for cl in listClusters:
            # 	str = ''
            # 	for sample in dictSpecEntry.keys():#cl.keys():
            # 		if cl.has_key(sample):
            # 			if cl[sample].content:
            # 				str +=  "  %.4f  " % cl[sample].mass
            # 			else:
            # 				try:
            # 					str +=  " /%.4f/ " % cl[sample].mass
            # 				except TypeError:
            # 					print "TypeError:", cl[sample].mass
            # 		else:
            # 			str += " / empty  / "
            # 	print str
            #### end of the debugging output

            ##################################################################
            ### align all the MS/MS masses for each precursor mass cluster ###

            alignedMSMS = []
            msmsLists = {}
            for cl in listClusters:
                sum = 0
                for sample in list(cl.keys()):
                    sum += cl[sample].mass
                if cl != {}:
                    avgPrecursorMass = sum / len(list(cl.keys()))

                    # the standard data format for alignment functions
                    dictSpecEntry = {}

                    # collect the base peaks of the merged spectra
                    dictBasePeakIntensity = {}

                    for sample in list(cl.keys()):
                        dictBasePeakIntensity[sample] = 0

                        if cl[sample].content:
                            dictSpecEntry[sample] = []

                            p = cl[sample].content["MSMS"].polarity

                            # find base peak
                            for msmsEntry in (
                                cl[sample].content["MSMS"].entries
                            ):
                                if (
                                    msmsEntry[1]
                                    > dictBasePeakIntensity[sample]
                                ):
                                    dictBasePeakIntensity[sample] = msmsEntry[
                                        1
                                    ]

                            # collect MS/MS entries for specEntry
                            for msmsEntry in (
                                cl[sample].content["MSMS"].entries
                            ):
                                # check if the threshold setting fits encompassing the scanCount
                                # this is the first check for the threshold. Later when the MS/MS
                                # were aligned and should be put into MSMSEntries, we'll check
                                # the threshold again combined with the occupation threshold
                                aboveThreshold = False
                                if (
                                    scan.options["MSMSthresholdType"]
                                    == "relative"
                                ):
                                    if msmsEntry[1] >= (
                                        dictBasePeakIntensity[sample]
                                        * scan.options["MSMSthreshold"]
                                    ) / sqrt(
                                        cl[sample].content["MSMS"].scanCount
                                    ):
                                        aboveThreshold = True
                                else:
                                    if msmsEntry[1] >= scan.options[
                                        "MSMSthreshold"
                                    ] / sqrt(
                                        cl[sample].content["MSMS"].scanCount
                                    ):
                                        aboveThreshold = True

                                if aboveThreshold:
                                    # mk a specEntry for the alignment function
                                    dictSpecEntry[sample].append(
                                        specEntry(
                                            mass=msmsEntry[0],
                                            content={
                                                "sample": sample,
                                                "intensity": msmsEntry[1],
                                                "polarity": p,
                                                "scanCount": cl[sample]
                                                .content["MSMS"]
                                                .scanCount,
                                                "peak_info": msmsEntry[3:],
                                            },
                                        )
                                    )

                    # do the clustering for the alignment
                    cluster = linearAlignment(
                        list(dictSpecEntry.keys()),
                        dictSpecEntry,
                        scan.options["MSMSresolution"],
                        deltaRes=scan.options["MSMSresolutionDelta"],
                        minMass=scan.options["MSMSmassrange"][0],
                        bintolerance=scan.options["MSMStolerance"],
                        res_by_fullbin=scan.options["alignmentMethodMSMS"]
                        == "calctol",
                    )
                    if collapse:
                        cluster = collape_join_adjecent_clusters_msms(cluster)

                    # check again with this debugging output!
                    # if cluster:
                    # 	print "PRCMass: %.4f" % avgPrecursorMass,
                    # 	for sample in dictSpecEntry.keys():#cl.keys():
                    # 		print sample,
                    # 	print ''
                    # 	for cl in cluster:
                    # 		str = ''
                    # 		str2 = ''
                    # 		for sample in dictSpecEntry.keys():#cl.keys():
                    # 			if cl.has_key(sample):
                    # 				if cl[sample].content:
                    # 					str +=  "> %.4f  " % cl[sample].mass
                    # 					str2 +=  " [%.4f] " % cl[sample].content['intensity']
                    # 				else:
                    # 					try:
                    # 						str +=  " /%.4f/ " % cl[sample].mass
                    # 						str2 +=  " /         / "
                    # 					except TypeError:
                    # 						print "TypeError:", cl[sample].mass
                    # 			else:
                    # 				str += " / empty  / "
                    # 		print str
                    # 		print str2
                    ## end of the debugging output

                    # alignedMSMS.append([avgPrecursorMass, cluster])

                    # generate MSMSEntry with the dedicated intensities
                    if cluster:
                        for i in cluster:
                            # check for the occupation of every fragment
                            numSmpl = len(scan.listSamples)
                            numOccSmpl = 0
                            isEmpty = True
                            dictIntensity = {}
                            dictScanCount = {}
                            peakList = []
                            sum = 0

                            for sample in scan.listSamples:
                                try:
                                    if i[sample].content:
                                        numOccSmpl += 1
                                        dictIntensity[sample] = i[
                                            sample
                                        ].content["intensity"]
                                        dictScanCount[sample] = i[
                                            sample
                                        ].content["scanCount"]
                                        peakList.append(
                                            [
                                                i[sample].mass,
                                                {
                                                    sample: i[sample].content[
                                                        "intensity"
                                                    ]
                                                },
                                            ]
                                        )
                                        isEmpty = False
                                        sum += i[sample].mass
                                    else:
                                        dictIntensity[sample] = 0.0
                                        dictScanCount[sample] = 1

                                except KeyError:
                                    dictIntensity[sample] = 0.0
                                    dictScanCount[sample] = 1

                            avgMass = sum / numOccSmpl

                            if not isEmpty:
                                if scan.checkOccupation(
                                    dictIntensity,
                                    dictScanCount,
                                    occThr=scan.options["MSMSminOccupation"],
                                    mode="MSMS",
                                    dictBasePeakIntensity=dictBasePeakIntensity,
                                    threshold=scan.options["MSMSthreshold"],
                                    threshold_type=scan.options[
                                        "MSMSthresholdType"
                                    ],
                                ):
                                    if (
                                        "%.6f" % avgPrecursorMass
                                        not in msmsLists
                                    ):
                                        msmsLists[
                                            "%.6f" % avgPrecursorMass
                                        ] = []

                                    msmsLists[
                                        "%.6f" % avgPrecursorMass
                                    ].append(
                                        MSMSEntry(
                                            mass=avgMass,
                                            dictIntensity=dictIntensity,
                                            peaks=peakList,
                                            polarity=polarity,
                                            charge=None,
                                            se=None,
                                            samples=scan.listSamples,
                                            dictScanCount=dictScanCount,
                                            dictBasePeakIntensity=dictBasePeakIntensity,
                                        )
                                    )

            ### align all the MS/MS masses for each precursor mass cluster ###
            ##################################################################

            ###################################
            ### Start association algorithm ###

            if kwargs.get("make_intermediate_output", False):
                make_lx1_ms2_averages(msmsLists, scan)
            if msmsLists != {}:
                print(
                    "Associate MSMSEntry objects to the according SurveyEntry objects (precursor masses)"
                )

                # now listAvg is the basis for assigning the dta data to their
                # survey precurmass

                listSECharge = []
                for se in scan.listSurveyEntry:
                    if se.polarity == polarity:
                        listSECharge.append(se)

                if listSECharge != []:
                    listSurveyEntry = listSECharge

                    iterEntry = sorted(
                        listSECharge, key=lambda x: x.precurmass
                    ).__iter__()

                    iterListAvg = sortDictKeys(
                        adict=msmsLists, compare="float"
                    ).__iter__()

                    listSEcurrentAvg = []
                    listSEnextAvg = []
                    onlyOneMSMS = False

                    try:
                        currentAvg = next(iterListAvg)
                    except StopIteration:
                        print("No MS/MS spectra after the averaging!")
                        break

                    try:
                        nextAvg = next(iterListAvg)
                    except StopIteration:
                        onlyOneMSMS = True

                    if not onlyOneMSMS:
                        while iterListAvg:
                            # calc window if a PIS is given
                            if isPIS:
                                window = tolerance.getTinDA(float(currentAvg))

                            # is the following precursor mass overlapping with the current?
                            if float(currentAvg) + window > float(
                                nextAvg
                            ):  # - window:
                                listSE = []
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(nextAvg) + window
                                    ):
                                        listSE.append(se)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break

                                for j in range(len(listSE)):
                                    ni = abs(
                                        listSE[j].precurmass
                                        - float(currentAvg)
                                    )
                                    niplus1 = abs(
                                        listSE[j].precurmass - float(nextAvg)
                                    )
                                    if ni < niplus1:
                                        for se in scan.get_SurveyEntry(
                                            listSE[j].precurmass,
                                            listSE[j].polarity,
                                        ):
                                            se.listMSMS = msmsLists[currentAvg]
                                            for msmsentry in se.listMSMS:
                                                if isinstance(se, SurveyEntry):
                                                    msmsentry.se.append(se)
                                                else:
                                                    print(
                                                        "Error with SurveyEntry",
                                                        se,
                                                        " -> is no SurveyEntry",
                                                    )
                                                    exit(0)
                                    else:
                                        for se in scan.get_SurveyEntry(
                                            listSE[j].precurmass,
                                            listSE[j].polarity,
                                        ):
                                            se.listMSMS = msmsLists[nextAvg]
                                            for msmsentry in se.listMSMS:
                                                if isinstance(se, SurveyEntry):
                                                    msmsentry.se.append(se)
                                                else:
                                                    print(
                                                        "Error with SurveyEntry",
                                                        se,
                                                        " -> is no SurveyEntry",
                                                    )
                                                    exit(0)

                            else:
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(currentAvg) + window
                                    ):
                                        se.listMSMS = msmsLists[currentAvg]
                                        for msmsentry in se.listMSMS:
                                            if isinstance(se, SurveyEntry):
                                                msmsentry.se.append(se)
                                            else:
                                                print(
                                                    "Error with SurveyEntry",
                                                    se,
                                                    " -> is no SurveyEntry",
                                                )
                                                exit(0)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break

                            currentAvg = nextAvg
                            try:
                                nextAvg = next(iterListAvg)
                            except StopIteration:
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(currentAvg) + window
                                    ):
                                        se.listMSMS = msmsLists[currentAvg]
                                        for msmsentry in se.listMSMS:
                                            msmsentry.se.append(se)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break
                                break

                    else:  # just one MS/MS spectrum present
                        for se in listSurveyEntry:
                            if (
                                float(currentAvg) - window < se.precurmass
                                and se.precurmass < float(currentAvg) + window
                            ):
                                se.listMSMS = msmsLists[currentAvg]
                                for msmsentry in se.listMSMS:
                                    if isinstance(se, SurveyEntry):
                                        msmsentry.se.append(se)
                                    else:
                                        print(
                                            "Error with SurveyEntry",
                                            se,
                                            " -> is no SurveyEntry",
                                        )
                                        exit(0)
                
            else:
                print("No MS/MS spectra present")

                ### End association algorithm ###
                ###################################
            
            if kwargs.get("make_intermediate_output", False):
                make_lx1_ms2_to_ms1(msmsLists, scan)

    for i in scan.listSamples:
        if (
            i in scan.dictSamples
        ):  # TODO: listSamples should actually be same as scan.dictSamples.keys()
            del scan.dictSamples[i]


def mass_close_enough(c, current):
    mass_c = [v.mass for k, v in c.items() if v.content]
    mass_curr = [v.mass for k, v in current.items() if v.content]
    dist_mass_c = max(mass_c) - min(mass_c)
    dist_mass_curr = max(mass_curr) - min(mass_curr)

    dist_mass_max = max(
        dist_mass_c, dist_mass_curr
    )  # to deal with one being zero

    mean_mass_c = sum(mass_c) / len(mass_c)
    mean_mass_curr = sum(mass_curr) / len(mass_curr)

    max_mass = max(mean_mass_c, mean_mass_curr)
    min_mass = min(mean_mass_c, mean_mass_curr)

    return min_mass > max_mass - (dist_mass_max * 2)  # too far away


def intensity_far_enough_on(c, current):
    # check if intensity mismatch
    intensities_c = [v.content["intensity"] for k, v in c.items() if v.content]
    mid_c_i = (max(intensities_c) + min(intensities_c)) / 2

    intensities_curr = [
        v.content["intensity"] for k, v in current.items() if v.content
    ]
    mid_curr_i = (max(intensities_curr) + min(intensities_curr)) / 2

    mean_i = (mid_c_i + mid_curr_i) / 2
    diff_i = abs(mid_c_i - mid_curr_i)

    mid_scans_c = {
        k
        for k, v in c.items()
        if v.content
        and mean_i - diff_i <= v.content["intensity"] <= mean_i + diff_i
    }
    mid_scans_curr = {
        k
        for k, v in current.items()
        if v.content
        and mean_i - diff_i <= v.content["intensity"] <= mean_i + diff_i
    }

    if (
        mid_scans_c or mid_scans_curr
    ):  # cant clearly distinguish high and low clusters
        return None
    else:
        return mean_i


def collapseable(c, current):
    c_scans = {k for k, v in c.items() if v.content}
    current_scans = {k for k, v in current.items() if v.content}
    both_scans = c_scans.intersection(current_scans)
    return not both_scans


def collapse_join(c, current):
    current.update({k: v for k, v in c.items() if v.content})
    masses = [v.mass for k, v in current.items() if v.content]
    mean_m = sum(masses) / len(masses)
    for v in (v for k, v in current.items() if not v.content):
        v.mass = mean_m
    return current


def fill_cluster(cluster, keys):
    if not cluster:
        return None
    masses = [v.mass for k, v in cluster.items()]
    mean_m = sum(masses) / len(masses)

    tmp = {k: specEntry(mass=mean_m, content=None) for k in keys}
    tmp.update(cluster)
    return tmp


def collape_join_adjecent_clusters_msms(cluster):
    res = (
        []
    )  # must create new instances becase, all atributes are calulated on init not on call!!!!!
    cluster_iter = iter(cluster)
    current = next(cluster_iter, None)
    c = next(cluster_iter, None)
    while c:
        if not mass_close_enough(c, current):
            res.append(current)
            current = c
            c = next(cluster_iter, None)
            continue
        elif collapseable(c, current):
            current = collapse_join(c, current)
            c = next(cluster_iter, None)
            continue

        split_i = intensity_far_enough_on(c, current)
        if not split_i:
            res.append(current)
            current = c
            c = next(cluster_iter, None)
            continue

        # rearange the clusters
        high_cluster = {
            k: v
            for k, v in c.items()
            if v.content and v.content["intensity"] > split_i
        }
        high_cluster.update(
            {
                k: v
                for k, v in current.items()
                if v.content and v.content["intensity"] > split_i
            }
        )

        low_cluster = {
            k: v
            for k, v in c.items()
            if v.content and v.content["intensity"] <= split_i
        }
        low_cluster.update(
            {
                k: v
                for k, v in current.items()
                if v.content and v.content["intensity"] <= split_i
            }
        )

        any_high_cluster = high_cluster or False
        any_low_cluster = low_cluster or False

        high_cluster = fill_cluster(high_cluster, c.keys())
        low_cluster = fill_cluster(low_cluster, c.keys())

        if any_low_cluster and any_high_cluster:
            current = low_cluster
            c = high_cluster
        elif any_low_cluster:
            current = low_cluster
            c = next(cluster_iter, None)
        elif any_high_cluster:
            current = high_cluster
            c = next(cluster_iter, None)

    return res


def collape_join_adjecent_clusters(
    survey_entries, max_dist=0.05, consider_intensity=True
):
    """join adjecent clusters that may be complementary,

    Args:
            survey_entries (dict of spentries): all the clusters so far
            max_dist (float, optional): how far a cluster is in daltons to try and merge them if they are complementary. Defaults to 0.1. # default is arbitrary
            consider_intensity (bool, optional): try to cluster similar intensities

    Returns:
            same as cluster but collapsed, may include duplicated entries in adjacent clusters
    """
    res = (
        []
    )  # must create new instances becase, all atributes are calulated on init not on call!!!!!
    current = survey_entries[0]
    collapsing = False
    for c in survey_entries[1:]:
        if abs(c.peakMean - current.peakMean) > max_dist:
            res.append(current)
            current = c
            collapsing = False
            continue

        c_spectras = {k for k, v in c.dictIntensity.items() if v > 0}
        current_spectras = {
            k for k, v in current.dictIntensity.items() if v > 0
        }

        # update mac_dist
        if len(c_spectras) > 0.7 * len(c.dictIntensity):
            max_dist = min(abs(c.peakMean - current.peakMean), max_dist / 2)
            max_dist = max(max_dist, 0.0001)
            max_dist = max_dist * 2

        overlap = c_spectras.intersection(current_spectras)

        if overlap:
            res.append(current)
            current = c
            collapsing = False
            continue

        # join the cluster
        current.dictIntensity.update(
            {k: v for k, v in c.dictIntensity.items() if v > 0}
        )
        current.peaks.extend(c.peaks)
        current.dictScans.update(
            {k: v for k, v in c.dictScans.items() if v > 1}
        )

        entry = SurveyEntry(
            msmass=sum([x[0] for x in current.peaks]) / len(current.peaks),
            smpl=current.dictIntensity,
            peaks=current.peaks,
            charge=None,
            polarity=current.polarity,
            dictScans=current.dictScans,
            dictBasePeakIntensity=current.dictBasePeakIntensity,
        )

        if collapsing and res:
            res.pop()
        # res.append(entry)
        current = entry
        collapsing = True

    return res


def mkMSMSEntriesHeuristic_new(
    scan, listPolarity, numLoops=None, isPIS=False, relative=None
):
    ################################################################
    ###	merge MS/MS experiments if there are more than one for a ###
    ### precursor mass                                           ###
    ################################################################

    secondStep = True
    numLoops = 3

    msmsThreshold = scan.options["MSMSthreshold"]
    if not isPIS:
        tolerance = TypeTolerance("Da", scan.options["selectionWindow"])
        # tolerance = scan.options['MSresolution']
        window = scan.options["selectionWindow"] / 2
        deltaRes = None
    else:
        tolerance = scan.options["MSMSresolution"]
        deltaRes = scan.options["MSMSresolutionDelta"]
        window = scan.options["MSMSresolution"]

    listPolarity = []
    for k in scan.listSamples:
        if scan.dictSamples[k].polarity not in listPolarity:
            listPolarity.append(scan.dictSamples[k].polarity)

    # check if there are MS/MS spectra at all
    msmsThere = False
    for polarity in listPolarity:
        for sample in scan.listSamples:
            # TODO: This has to be tested ASAP
            if (
                scan.dictSamples[sample].listMsms != []
                and scan.dictSamples[sample].polarity == polarity
            ):
                msmsThere = True

    # double check if the MSMSresolution was set
    if msmsThere:
        if (
            not scan.options["MSMSresolution"]
            or scan.options["MSMSresolution"] == 0
        ):
            raise LipidXException("no resolution setting given for MS/MS.")

        if (
            not scan.options["selectionWindow"]
            or scan.options["selectionWindow"] == 0
        ):
            raise LipidXException("no selection window given.")

    ### go seperately for the polarity ###
    for polarity in listPolarity:
        ############################################################
        ### Cluster the precursor masses and average MS/MS scans ###

        dictMSMS = {}
        listAt = []

        dictSpecEntry = {}

        for sample in scan.listSamples:
            if msmsThere:
                # generate a list of specEntry elements
                dictSpecEntry[sample] = []
                scan.dictSamples[sample].listMsms.sort()
                for i in scan.dictSamples[sample].listMsms:
                    dictSpecEntry[sample].append(
                        specEntry(
                            mass=i.precurmass,
                            content={"sample": sample, "MSMS": i},
                        )
                    )

        if msmsThere:
            listClusters = heuristicAlignment(
                list(dictSpecEntry.keys()), dictSpecEntry, tolerance
            )  # ,
            # merge = mergeListMsms,
            # mergeTolerance = scan.options['MSMSresolution'],
            # mergeDeltaRes = scan.options['MSMSresolutionDelta'])

        else:
            listClusters = False

        ### Cluster the precursor masses and average MS/MS scans ###
        ############################################################

        if listClusters:
            #### check again with this debugging output!
            # for sample in dictSpecEntry.keys():#cl.keys():
            # 	print sample,
            # print ''
            # for cl in listClusters:
            # 	str = ''
            # 	for sample in dictSpecEntry.keys():#cl.keys():
            # 		if cl.has_key(sample):
            # 			if cl[sample].content:
            # 				str +=  "  %.4f  " % cl[sample].mass
            # 			else:
            # 				try:
            # 					str +=  " /%.4f/ " % cl[sample].mass
            # 				except TypeError:
            # 					print "TypeError:", cl[sample].mass
            # 		else:
            # 			str += " / empty  / "
            # 	print str
            #### end of the debugging output

            ##################################################################
            ### align all the MS/MS masses for each precursor mass cluster ###

            alignedMSMS = []
            msmsLists = {}
            for cl in listClusters:
                sum = 0
                for sample in list(cl.keys()):
                    sum += cl[sample].mass
                if cl != {}:
                    avgPrecursorMass = sum / len(list(cl.keys()))

                    # the standard data format for alignment functions
                    dictSpecEntry = {}

                    # collect the base peaks of the merged spectra
                    dictBasePeakIntensity = {}

                    for sample in list(cl.keys()):
                        dictBasePeakIntensity[sample] = 0

                        if cl[sample].content:
                            dictSpecEntry[sample] = []

                            p = cl[sample].content["MSMS"].polarity

                            # find base peak
                            for msmsEntry in (
                                cl[sample].content["MSMS"].entries
                            ):
                                if (
                                    msmsEntry[1]
                                    > dictBasePeakIntensity[sample]
                                ):
                                    dictBasePeakIntensity[sample] = msmsEntry[
                                        1
                                    ]

                            # collect MS/MS entries for specEntry
                            for msmsEntry in (
                                cl[sample].content["MSMS"].entries
                            ):
                                # check if the threshold setting fits encompassing the scanCount
                                # this is the first check for the threshold. Later when the MS/MS
                                # were aligned and should be put into MSMSEntries, we'll check
                                # the threshold again combined with the occupation threshold
                                aboveThreshold = False
                                if (
                                    scan.options["MSMSthresholdType"]
                                    == "relative"
                                ):
                                    if msmsEntry[1] >= (
                                        dictBasePeakIntensity[sample]
                                        * scan.options["MSMSthreshold"]
                                    ) / sqrt(
                                        cl[sample].content["MSMS"].scanCount
                                    ):
                                        aboveThreshold = True
                                else:
                                    if msmsEntry[1] >= scan.options[
                                        "MSMSthreshold"
                                    ] / sqrt(
                                        cl[sample].content["MSMS"].scanCount
                                    ):
                                        aboveThreshold = True

                                if aboveThreshold:
                                    # mk a specEntry for the alignment function
                                    dictSpecEntry[sample].append(
                                        specEntry(
                                            mass=msmsEntry[0],
                                            content={
                                                "sample": sample,
                                                "intensity": msmsEntry[1],
                                                "polarity": p,
                                                "scanCount": cl[sample]
                                                .content["MSMS"]
                                                .scanCount,
                                                "peak_info": msmsEntry[3:],
                                            },
                                        )
                                    )

                    # do the clustering for the alignment
                    cluster = heuristicAlignment(
                        list(dictSpecEntry.keys()),
                        dictSpecEntry,
                        scan.options["MSMSresolution"],
                        deltaRes=scan.options["MSMSresolutionDelta"],
                        minMass=scan.options["MSMSmassrange"][0],
                    )

                    # check again with this debugging output!
                    # if cluster:
                    # 	print "PRCMass: %.4f" % avgPrecursorMass,
                    # 	for sample in dictSpecEntry.keys():#cl.keys():
                    # 		print sample,
                    # 	print ''
                    # 	for cl in cluster:
                    # 		str = ''
                    # 		str2 = ''
                    # 		for sample in dictSpecEntry.keys():#cl.keys():
                    # 			if cl.has_key(sample):
                    # 				if cl[sample].content:
                    # 					str +=  "> %.4f  " % cl[sample].mass
                    # 					str2 +=  " [%.4f] " % cl[sample].content['intensity']
                    # 				else:
                    # 					try:
                    # 						str +=  " /%.4f/ " % cl[sample].mass
                    # 						str2 +=  " /         / "
                    # 					except TypeError:
                    # 						print "TypeError:", cl[sample].mass
                    # 			else:
                    # 				str += " / empty  / "
                    # 		print str
                    # 		print str2
                    ## end of the debugging output

                    # alignedMSMS.append([avgPrecursorMass, cluster])

                    # generate MSMSEntry with the dedicated intensities
                    if cluster:
                        for i in cluster:
                            # check for the occupation of every fragment
                            numSmpl = len(scan.listSamples)
                            numOccSmpl = 0
                            isEmpty = True
                            dictIntensity = {}
                            dictScanCount = {}
                            peakList = []
                            sum = 0

                            for sample in scan.listSamples:
                                try:
                                    if i[sample].content:
                                        numOccSmpl += 1
                                        dictIntensity[sample] = i[
                                            sample
                                        ].content["intensity"]
                                        dictScanCount[sample] = i[
                                            sample
                                        ].content["scanCount"]
                                        peakList.append(
                                            [
                                                i[sample].mass,
                                                {
                                                    sample: i[sample].content[
                                                        "intensity"
                                                    ]
                                                },
                                            ]
                                        )
                                        isEmpty = False
                                        sum += i[sample].mass
                                    else:
                                        dictIntensity[sample] = 0.0
                                        dictScanCount[sample] = 1

                                except KeyError:
                                    dictIntensity[sample] = 0.0
                                    dictScanCount[sample] = 1

                            if numOccSmpl > 0:
                                avgMass = sum / numOccSmpl
                            else:
                                isEmpty = True

                            if not isEmpty:
                                if scan.checkOccupation(
                                    dictIntensity,
                                    dictScanCount,
                                    occThr=scan.options["MSMSminOccupation"],
                                    mode="MSMS",
                                    dictBasePeakIntensity=dictBasePeakIntensity,
                                    threshold=scan.options["MSMSthreshold"],
                                    threshold_type=scan.options[
                                        "MSMSthresholdType"
                                    ],
                                ):
                                    if (
                                        "%.6f" % avgPrecursorMass
                                        not in msmsLists
                                    ):
                                        msmsLists[
                                            "%.6f" % avgPrecursorMass
                                        ] = []

                                    msmsLists[
                                        "%.6f" % avgPrecursorMass
                                    ].append(
                                        MSMSEntry(
                                            mass=avgMass,
                                            dictIntensity=dictIntensity,
                                            peaks=peakList,
                                            polarity=polarity,
                                            charge=None,
                                            se=None,
                                            samples=scan.listSamples,
                                            dictScanCount=dictScanCount,
                                            dictBasePeakIntensity=dictBasePeakIntensity,
                                        )
                                    )

            ### align all the MS/MS masses for each precursor mass cluster ###
            ##################################################################

            ###################################
            ### Start association algorithm ###

            if msmsLists != {}:
                print(
                    "Associate MSMSEntry objects to the according SurveyEntry objects (precursor masses)"
                )

                # now listAvg is the basis for assigning the dta data to their
                # survey precurmass

                listSECharge = []
                for se in scan.listSurveyEntry:
                    if se.polarity == polarity:
                        listSECharge.append(se)

                if listSECharge != []:
                    listSurveyEntry = listSECharge

                    iterEntry = sorted(
                        listSECharge,
                        lambda x, y: cmp(x.precurmass, y.precurmass),
                    ).__iter__()

                    iterListAvg = sortDictKeys(
                        adict=msmsLists, compare="float"
                    ).__iter__()

                    listSEcurrentAvg = []
                    listSEnextAvg = []
                    onlyOneMSMS = False

                    try:
                        currentAvg = next(iterListAvg)
                    except StopIteration:
                        print("No MS/MS spectra after the averaging!")
                        break

                    try:
                        nextAvg = next(iterListAvg)
                    except StopIteration:
                        onlyOneMSMS = True

                    if not onlyOneMSMS:
                        while iterListAvg:
                            # calc window if a PIS is given
                            if isPIS:
                                window = tolerance.getTinDA(float(currentAvg))

                            # is the following precursor mass overlapping with the current?
                            if float(currentAvg) + window > float(
                                nextAvg
                            ):  # - window:
                                listSE = []
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(nextAvg) + window
                                    ):
                                        listSE.append(se)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break

                                for j in range(len(listSE)):
                                    ni = abs(
                                        listSE[j].precurmass
                                        - float(currentAvg)
                                    )
                                    niplus1 = abs(
                                        listSE[j].precurmass - float(nextAvg)
                                    )
                                    if ni < niplus1:
                                        for se in scan.get_SurveyEntry(
                                            listSE[j].precurmass,
                                            listSE[j].polarity,
                                        ):
                                            se.listMSMS = msmsLists[currentAvg]
                                            for msmsentry in se.listMSMS:
                                                if isinstance(se, SurveyEntry):
                                                    msmsentry.se.append(se)
                                                else:
                                                    print(
                                                        "Error with SurveyEntry",
                                                        se,
                                                        " -> is no SurveyEntry",
                                                    )
                                                    exit(0)
                                    else:
                                        for se in scan.get_SurveyEntry(
                                            listSE[j].precurmass,
                                            listSE[j].polarity,
                                        ):
                                            se.listMSMS = msmsLists[nextAvg]
                                            for msmsentry in se.listMSMS:
                                                if isinstance(se, SurveyEntry):
                                                    msmsentry.se.append(se)
                                                else:
                                                    print(
                                                        "Error with SurveyEntry",
                                                        se,
                                                        " -> is no SurveyEntry",
                                                    )
                                                    exit(0)

                            else:
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(currentAvg) + window
                                    ):
                                        se.listMSMS = msmsLists[currentAvg]
                                        for msmsentry in se.listMSMS:
                                            if isinstance(se, SurveyEntry):
                                                msmsentry.se.append(se)
                                            else:
                                                print(
                                                    "Error with SurveyEntry",
                                                    se,
                                                    " -> is no SurveyEntry",
                                                )
                                                exit(0)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break

                            currentAvg = nextAvg
                            try:
                                nextAvg = next(iterListAvg)
                            except StopIteration:
                                for se in listSurveyEntry:
                                    if (
                                        float(currentAvg) - window
                                        < se.precurmass
                                        and se.precurmass
                                        < float(currentAvg) + window
                                    ):
                                        se.listMSMS = msmsLists[currentAvg]
                                        for msmsentry in se.listMSMS:
                                            msmsentry.se.append(se)

                                    # stop for loop, when masses get too big
                                    if float(nextAvg) + window < se.precurmass:
                                        break
                                break

                    else:  # just one MS/MS spectrum present
                        for se in listSurveyEntry:
                            if (
                                float(currentAvg) - window < se.precurmass
                                and se.precurmass < float(currentAvg) + window
                            ):
                                se.listMSMS = msmsLists[currentAvg]
                                for msmsentry in se.listMSMS:
                                    if isinstance(se, SurveyEntry):
                                        msmsentry.se.append(se)
                                    else:
                                        print(
                                            "Error with SurveyEntry",
                                            se,
                                            " -> is no SurveyEntry",
                                        )
                                        exit(0)

            else:
                print("No MS/MS spectra present")

                ### End association algorithm ###
                ###################################

    for i in scan.listSamples:
        if (
            i in scan.dictSamples
        ):  # TODO: listSamples should actually be same as scan.dictSamples.keys()
            del scan.dictSamples[i]


def mkMSMSEntriesHeuristic(
    scan, listPolarity, numLoops=None, isPIS=False, relative=None
):
    ################################################################
    ###	merge MS/MS experiments if there are more than one for a ###
    ### precursor mass                                           ###
    ################################################################

    secondStep = True
    numLoops = 3

    msmsThreshold = scan.options["MSMSthreshold"]
    if not isPIS:
        # tolerance = TypeTolerance('Da', scan.options['selectionWindow'])
        tolerance = scan.options["MSMSresolution"]
        window = scan.options["selectionWindow"] / 2
        deltaRes = None
    else:
        tolerance = scan.options["MSMSresolution"]
        deltaRes = scan.options["MSMSresolutionDelta"]
        window = scan.options["MSMSresolution"]

    listPolarity = []
    for k in scan.listSamples:
        if scan.dictSamples[k].polarity not in listPolarity:
            listPolarity.append(scan.dictSamples[k].polarity)

    for charge in listPolarity:
        msmsThere = False
        dictMSMS = {}
        listAt = []

        dictSpecEntry = {}

        for sample in scan.listSamples:
            if scan.dictSamples[sample].listMsms != []:
                msmsThere = True

            if msmsThere:
                # generate a list of specEntry elements
                dictSpecEntry[sample] = []
                for i in scan.dictSamples[sample].listMsms:
                    dictSpecEntry[sample].append(
                        specEntry(
                            mass=i.precurmass,
                            content={"sample": sample, "MSMS": i},
                        )
                    )

        # double check if the MSMSresolution was set
        if msmsThere:
            if (
                not scan.options["MSMSresolution"]
                or scan.options["MSMSresolution"] == 0
            ):
                raise LipidXException("no resolution setting given for MS/MS.")

            if (
                not scan.options["selectionWindow"]
                or scan.options["selectionWindow"] == 0
            ):
                raise LipidXException("no selection window given.")

        if msmsThere:
            listClusters = heuristicAlignment(
                list(dictSpecEntry.keys()),
                dictSpecEntry,
                TypeTolerance("Da", window),
            )
            # tolerance)
            # merge = mergeListMsms,
            # mergeTolerance = scan.options['MSMSresolution'],
            # mergeDeltaRes = scan.options['MSMSresolutionDelta'])

        else:
            listClusters = False

        # check again with this debugging output!
        if listClusters:
            # for cl in listClusters:
            # 	str = ''
            # 	for sample in dictSpecEntry.keys():#cl.keys():
            # 		if cl.has_key(sample):
            # 			if cl[sample].content:
            # 				str +=  "  %.4f  " % cl[sample].mass
            # 			else:
            # 				try:
            # 					str +=  " /%.4f/ " % cl[sample].mass
            # 				except TypeError:
            # 					print "TypeError:", cl[sample].mass
            # 		else:
            # 			str += " / empty  / "
            # 	print str

            # dbgfile = open('C:\Users\The Duke\My_Projects\LipidXplorer PLoS software article\chp-peak_alignment_methods\spec_Ecoli_low_to_high-070909-DS\debug.txt', 'a')

            alignedMSMS = []
            msmsLists = {}
            for cl in listClusters:
                sum = 0
                for sample in list(cl.keys()):
                    sum += cl[sample].mass
                if cl != {}:
                    avgPrecursorMass = sum / len(list(cl.keys()))

                    dictSpecEntry = {}
                    for sample in list(cl.keys()):
                        dictSpecEntry[sample] = []
                        dictBasePeakIntensity[sample] = 0.0

                        # if an entrie is there
                        if cl[sample].content:
                            for msmsEntry in (
                                cl[sample].content["MSMS"].entries
                            ):
                                # collect base peak intensities
                                if (
                                    msmsEntry[1]
                                    > dictBasePeakIntensity[sample]
                                ):
                                    dictBasePeakIntensity[sample] = msmsEntry[
                                        1
                                    ]

                                p = cl[sample].content["MSMS"].polarity

                                # check if the threshold setting fits encompassing the scanCount
                                scanCount = (
                                    cl[sample].content["MSMS"].scanCount
                                )
                                if isPIS:
                                    threshold = (
                                        cl[sample].content["MSMS"].threshold
                                    )
                                else:
                                    threshold = scan.options["MSMSthreshold"]

                                aboveThreshold = False
                                if (
                                    scan.options["MSMSthresholdType"]
                                    == "relative"
                                ):
                                    if msmsEntry[1] >= (
                                        (dictBasePeakIntensity[sample] / 100)
                                        * threshold
                                    ) / sqrt(scanCount):
                                        aboveThreshold = True
                                else:
                                    if msmsEntry[1] >= threshold / sqrt(
                                        scanCount
                                    ):
                                        aboveThreshold = True

                                if msmsEntry[1] >= cl[sample].content[
                                    "MSMS"
                                ].threshold / sqrt(
                                    cl[sample].content["MSMS"].scanCount
                                ):
                                    dictSpecEntry[sample].append(
                                        specEntry(
                                            mass=msmsEntry[0],
                                            content={
                                                "sample": sample,
                                                "intensity": msmsEntry[1],
                                                "polarity": p,
                                                "scanCount": scanCount,
                                                "threshold": threshold,
                                            },
                                        )
                                    )

                    # do clustering
                    cluster = heuristicAlignment(
                        list(dictSpecEntry.keys()),
                        dictSpecEntry,
                        scan.options["MSMSresolution"],
                        deltaRes=scan.options["MSMSresolutionDelta"],
                        minMass=scan.options["MSMSmassrange"][0],
                    )

                    alignedMSMS.append([avgPrecursorMass, cluster])

                    # generate MSMSEntry
                    if cluster:
                        # 	str = "\n>>> %f \n" % avgPrecursorMass
                        # 	for cl in cluster:
                        # 		for sample in dictSpecEntry.keys():#cl.keys():
                        # 			if cl.has_key(sample):
                        # 				if cl[sample].content:
                        # 					str +=  "  %.4f  " % cl[sample].mass
                        # 				else:
                        # 					try:
                        # 						str +=  " /%.4f/ " % cl[sample].mass
                        # 					except TypeError:
                        # 						print "TypeError:", cl[sample].mass
                        # 			else:
                        # 				str += " / empty  / "
                        # 		str += '\n'
                        # 		dbgfile.write(str)

                        for i in cluster:
                            numSmpl = len(scan.listSamples)
                            numOccSmpl = 0
                            isEmpty = True
                            dictIntensity = {}
                            dictScanCount = {}
                            peakList = []
                            for sample in scan.listSamples:
                                try:
                                    if i[sample].content:
                                        numOccSmpl += 1
                                        dictIntensity[sample] = i[
                                            sample
                                        ].content["intensity"]
                                        dictScanCount[sample] = i[
                                            sample
                                        ].content["scanCount"]
                                        peakList.append(
                                            [
                                                i[sample].mass,
                                                {
                                                    sample: i[sample].content[
                                                        "intensity"
                                                    ]
                                                },
                                            ]
                                        )
                                        isEmpty = False
                                        sum += i[sample].mass
                                    else:
                                        dictIntensity[sample] = 0.0
                                        dictScanCount[sample] = 1

                                except KeyError:
                                    dictIntensity[sample] = 0.0
                                    dictScanCount[sample] = 1

                            if not isEmpty:
                                if isPIS:
                                    if scan.checkOccupation(
                                        dictIntensity,
                                        dictScanCount,
                                        mode="MSMS",
                                        occThr=scan.options[
                                            "MSMSminOccupation"
                                        ],
                                        threshold=scan.options[
                                            "MSMSthreshold"
                                        ],
                                        threshold_type=scan.options[
                                            "MSMSthresholdType"
                                        ],
                                        dictBasePeakIntensity=dictBasePeakIntensity,
                                    ):
                                        if (
                                            "%.6f" % avgPrecursorMass
                                            not in msmsLists
                                        ):
                                            msmsLists[
                                                "%.6f" % avgPrecursorMass
                                            ] = []

                                        msmsLists[
                                            "%.6f" % avgPrecursorMass
                                        ].append(
                                            MSMSEntry(
                                                mass=i[sample].mass,
                                                dictIntensity=dictIntensity,
                                                peaks=peakList,
                                                polarity=charge,
                                                charge=None,
                                                se=None,
                                                samples=scan.listSamples,
                                                dictScanCount=dictScanCount,
                                                dictBasePeakIntensity=dictBasePeakIntensity,
                                            )
                                        )
                                else:
                                    if scan.checkOccupation(
                                        dictIntensity,
                                        dictScanCount,
                                        occThrs=scan.options[
                                            "MSMSminOccupation"
                                        ],
                                        threshold=scan.options[
                                            "MSMSthreshold"
                                        ],
                                        threshold_type=scan.options[
                                            "MSMSthresholdType"
                                        ],
                                        dictBasePeakIntensity=dictBasePeakIntensity,
                                        mode="MSMS",
                                    ):
                                        if (
                                            "%.6f" % avgPrecursorMass
                                            not in msmsLists
                                        ):
                                            msmsLists[
                                                "%.6f" % avgPrecursorMass
                                            ] = []

                                        msmsLists[
                                            "%.6f" % avgPrecursorMass
                                        ].append(
                                            MSMSEntry(
                                                mass=i[sample].mass,
                                                dictIntensity=dictIntensity,
                                                peaks=peakList,
                                                polarity=charge,
                                                charge=None,
                                                se=None,
                                                samples=scan.listSamples,
                                                dictScanCount=dictScanCount,
                                                dictBasePeakIntensity=dictBasePeakIntensity,
                                            )
                                        )

            # dbgfile.close()

            ######################################################################
            ### Start association algorithm                                    ###
            ######################################################################

            print(
                "Associate MSMSEntry objects to the according SurveyEntry objects (precursor masses)"
            )

            # now listAvg is the basis for assigning the dta data to their
            # survey precurmass

            listSECharge = []
            for se in scan.listSurveyEntry:
                if se.polarity == charge:
                    listSECharge.append(se)

            if listSECharge != []:
                listSurveyEntry = listSECharge

                iterEntry = sorted(
                    listSECharge, lambda x, y: cmp(x.precurmass, y.precurmass)
                ).__iter__()

                iterListAvg = sortDictKeys(
                    adict=msmsLists, compare="float"
                ).__iter__()

                listSEcurrentAvg = []
                listSEnextAvg = []

                currentAvg = next(iterListAvg)
                nextAvg = next(iterListAvg)
                while iterListAvg:
                    # calc window if a PIS is given
                    if isPIS:
                        window = tolerance.getTinDA(float(currentAvg))

                    # is the following precursor mass overlapping with the current?
                    if float(currentAvg) + window > float(
                        nextAvg
                    ):  # - window:
                        listSE = []
                        for se in listSurveyEntry:
                            if (
                                float(currentAvg) - window < se.precurmass
                                and se.precurmass < float(nextAvg) + window
                            ):
                                listSE.append(se)

                            # stop for loop, when masses get too big
                            if float(nextAvg) < se.precurmass:
                                break

                        for j in range(len(listSE)):
                            ni = abs(listSE[j].precurmass - float(currentAvg))
                            niplus1 = abs(
                                listSE[j].precurmass - float(nextAvg)
                            )
                            if ni < niplus1:
                                for se in scan.get_SurveyEntry(
                                    listSE[j].precurmass, listSE[j].polarity
                                ):
                                    se.listMSMS = msmsLists[currentAvg]
                                    for msmsentry in se.listMSMS:
                                        if isinstance(se, SurveyEntry):
                                            msmsentry.se.append(se)
                                        else:
                                            print(
                                                "Error with SurveyEntry",
                                                se,
                                                " -> is no SurveyEntry",
                                            )
                                            exit(0)
                            else:
                                for se in scan.get_SurveyEntry(
                                    listSE[j].precurmass, listSE[j].polarity
                                ):
                                    se.listMSMS = msmsLists[nextAvg]
                                    for msmsentry in se.listMSMS:
                                        if isinstance(se, SurveyEntry):
                                            msmsentry.se.append(se)
                                        else:
                                            print(
                                                "Error with SurveyEntry",
                                                se,
                                                " -> is no SurveyEntry",
                                            )
                                            exit(0)

                    else:
                        for se in listSurveyEntry:
                            if (
                                float(currentAvg) - window < se.precurmass
                                and se.precurmass < float(currentAvg) + window
                            ):
                                se.listMSMS = msmsLists[currentAvg]
                                for msmsentry in se.listMSMS:
                                    if isinstance(se, SurveyEntry):
                                        msmsentry.se.append(se)
                                    else:
                                        print(
                                            "Error with SurveyEntry",
                                            se,
                                            " -> is no SurveyEntry",
                                        )
                                        exit(0)

                            # stop for loop, when masses get too big
                            if float(nextAvg) + window < se.precurmass:
                                break

                    currentAvg = nextAvg
                    try:
                        nextAvg = next(iterListAvg)
                    except StopIteration:
                        for se in listSurveyEntry:
                            if (
                                float(currentAvg) - window < se.precurmass
                                and se.precurmass < float(currentAvg) + window
                            ):
                                se.listMSMS = msmsLists[currentAvg]
                                for msmsentry in se.listMSMS:
                                    msmsentry.se.append(se)

                            # stop for loop, when masses get too big
                            if float(nextAvg) < se.precurmass:
                                break
                        break

    for i in scan.listSamples:
        del scan.dictSamples[i]


def getResSteps(dictSamples, mstolerance):
    mass = []
    tols = []

    mstol = None
    if mstolerance.kind == "da":
        mstol = mstolerance.da * 2  # double to make it less sensitive

    for _, samples in dictSamples.items():
        s_samples = sorted(samples, key=lambda x: x.mass, reverse=True)

        if mstol == None and mstolerance.kind == "ppm":
            mstol = s_samples[0].mass / (100000 / mstolerance.ppm)
            mstol = mstol * 2

        for idx, s_sample in enumerate(s_samples[:-1]):
            next_sample = s_samples[idx + 1]
            if s_sample.mass - next_sample.mass < mstol:
                mstol = s_sample.mass - next_sample.mass
                mass.append(s_sample.mass)
                tols.append(mstol)
        mstol = None

    s_mass_tol = sorted(zip(mass, tols), reverse=True)

    res = []
    for idx, (mz, tol) in enumerate(s_mass_tol[:-1]):
        next_tol = s_mass_tol[idx + 1][1]
        if next_tol < tol:
            res.append((mz, tol))

    return res


def r_linearAlignment(
    listSamples,
    dictSamples,
    tolerance,
    merge=None,
    mergeTolerance=None,
    mergeDeltaRes=None,
    charge=None,
    deltaRes=None,
    minocc=None,
    msThreshold=None,
    intensityWeightedAvg=False,
    minMass=None,
    fadi_denominator=None,
    fadi_percentage=0.0,
    bintolerance=None,
    res_by_fullbin=False,
    res_by_steps=False,
    min_da_delta_all_scans=None,
):
    import pandas as pd
    import numpy as np

    def bin_generator(masses):
        # TODO assert masses are ordered
        up_to = None
        for _, mass in masses.iteritems():
            if up_to is None:
                up_to = mass + tolerance.getTinDA(mass)

            if mass <= up_to:
                yield up_to
            else:
                up_to = mass + tolerance.getTinDA(mass)
                yield up_to

    df = pd.DataFrame(
        (
            {"mass": e.mass, **e.content}
            for s in dictSamples.values()
            for e in s
        )
    )
    df.sort_values("mass", inplace=True)
    # NOTE do it 3 times as per lx1...
    df["bins1"] = list(bin_generator(df.mass))
    df["bins2"] = list(
        bin_generator(df.groupby("bins1")["mass"].transform("mean"))
    )
    df["bins3"] = list(
        bin_generator(df.groupby("bins2")["mass"].transform("mean"))
    )
    # cluster to merge, if multiple peaks from same sample
    g = df.groupby(["bins3", "sample"])
    df["sample_count"] = g.cumcount()
    df["merged_mass"] = g["mass"].transform("mean")
    # drop the peaks that are alredy averaged  into one
    df = df.loc[df.sample_count == 0]

    agg_df = (
        df.assign(
            mass_intensity=lambda x: x.mass * x.intensity
        )  # for the weighted average intensity
        .groupby("bins3")
        .agg(
            {
                "mass": ["mean", "count", "min", "max"],
                "intensity": ["mean", "sum"],
                "mass_intensity": "sum",
            }
        )
        .dropna()
    )
    agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]

    # NOTE frequency filtered is applied after all 3 not on each iteration
    mask_ff = agg_df.mass_count / fadi_denominator >= fadi_percentage
    agg_df = agg_df[mask_ff]

    # NOTE intensity threshold is do in add_Sample... but lets do it here
    # NOTE  is uses options["MSthreshold"] that is missing here
    MSthreshold = 0.0001
    mask_inty = agg_df.intensity_mean > MSthreshold
    agg_df = agg_df[mask_inty]

    # weigted average is do in def add_Sample... but lets do it here
    agg_df["mass"] = agg_df.mass_intensity_sum / agg_df.intensity_sum

    return agg_df


def linearAlignment(
    listSamples,
    dictSamples,
    tolerance,
    merge=None,
    mergeTolerance=None,
    mergeDeltaRes=None,
    charge=None,
    deltaRes=None,
    minocc=None,
    msThreshold=None,
    intensityWeightedAvg=False,
    minMass=None,
    fadi_denominator=None,
    fadi_percentage=0.0,
    bintolerance=None,
    res_by_fullbin=False,
    res_by_steps=False,
    min_da_delta_all_scans=None,
):
    # using fadi_denominator, fadi_percentage, becayse nbofscans and msthreshold variables are already in use !!!
    # these varuables are used to implement fadi filter
    """
    This is the standard algorithm to align spectra. It is published
    in [...].

    It is optimized for the available data structures. Therefore the input
    is an own format (specEntry) provided as list in listSamples. Furthermore,
    dictSamples: is the list of all sample names (keys from dict)
    tolerance: is a TypeTolerance type with the
            tolerance as da, ppm or res.
    deltaRes: if the tolerance is given as resolution, the deltaRes
            states the resolution change over the masses.

    The output is a list of specEntry
    that can be "filtered" as per DS
    """
    # get max length of peak in the spectra
    speclen = 0
    for k in listSamples:
        if speclen < len(dictSamples[k]):
            speclen = len(dictSamples[k])

    # nothing there? Return nothing.
    if speclen < 1:
        return None

    # just one fragment? Return the result imediatly.
    mass = None
    if speclen == 1:
        cluster = {}
        for sample in listSamples:
            try:
                mass = dictSamples[sample][0].mass
                cluster[sample] = specEntry(
                    mass=dictSamples[sample][0].mass,
                    content=dictSamples[sample][0].content,
                    charge=dictSamples[sample][0].charge,
                )
            except IndexError:
                if mass:
                    cluster[sample] = specEntry(
                        mass=mass, content=None, charge=None
                    )
                else:
                    for s in listSamples:
                        try:
                            mass = dictSamples[s][0].mass
                        except IndexError:
                            pass
                    if mass:
                        cluster[sample] = specEntry(
                            mass=mass, content=None, charge=None
                        )
                    else:
                        return None

        return [cluster]

    # start the algorithm
    numLoops = 3

    # initialize merging algorithm
    listResult = []
    for i in range(numLoops + 1):
        listResult.append([])

    if res_by_steps and not res_by_fullbin:
        res_steps = getResSteps(dictSamples, bintolerance)

    # join all peaks into one list
    for sample in listSamples:
        for index in range(len(dictSamples[sample])):
            listResult[0].append(
                [dictSamples[sample][index].mass, [dictSamples[sample][index]]]
            )

    # the list (listResult[0]) is:
    #   [avg, [specEntry1, specEntry2, ..., specEntryN]]
    # sort the list
    listResult[0].sort()
    newres1 = None
    if res_by_fullbin:
        listResult[0] = list(reversed(listResult[0]))

        sorted_mass = [v[0] for v in listResult[0]]
        binsize = len(dictSamples)
        up_to = binsize * 10 if binsize * 10 < len(sorted_mass) else -1
        diffs = [
            sorted_mass[i] - sorted_mass[i + 1]
            for i, _ in enumerate(sorted_mass[:up_to])
        ]  # hope to find at least one full bin here
        diffs = [d for d in diffs if d > 0.0001 and d < 0.1]
        s_diffs = sorted(diffs)  # diffs are coorelated to the resolution
        if not min_da_delta_all_scans:
            min_da_delta_all_scans = 0.0002
        if binsize > 1:
            binres = (
                mean(s_diffs[:binsize]) * 2
                if s_diffs
                else min_da_delta_all_scans * 0.99
            )  # get average diffs to avoid outliers and times 2 to make flexible
        else:
            binres = min_da_delta_all_scans * 0.99
        # mstolerance = bintolerance
        # if mstolerance.kind == 'da':
        # 	binres = mstolerance.da * 2
        # elif mstolerance.kind == 'ppm':
        # 	binres = sorted_mass[0] /(100000 / mstolerance.ppm)
        # 	binres = binres * 2

        binres_og = binres

    for count in range(numLoops):
        current = 0
        binres = binres_og if res_by_fullbin else None

        if count > 0 and not newres1 and min_da_delta_all_scans:
            # went trough one cicle an no res was calculated so will use the min dist intead
            newres1 = min_da_delta_all_scans * 0.99
        # stop if the end of the list is reached
        if not current < (len(listResult[count]) - 1):
            listResult[-1] = listResult[count]
            break

        while current < (len(listResult[count]) - 1):
            # routine for collecting all masses which are in partialRes
            index = 1
            bin = [listResult[count][current]]

            # get the window size
            if isinstance(tolerance, TypeTolerance):
                if tolerance.kind == "Da":
                    res = tolerance.da
                else:
                    if deltaRes:
                        tmp = (
                            tolerance.tolerance
                            + (listResult[count][current][0] - minMass)
                            * deltaRes
                        )
                    else:
                        tmp = tolerance.tolerance

                    # this happened once, when
                    # tolerance.tolerance == 500, deltaRes == -20,
                    # listResult[count][current][0] == 177.916671753 and
                    # minMass == 152.916671753
                    if tmp == 0.0:
                        tmp = tolerance.tolerance

                    res = listResult[count][current][0] / tmp

            else:
                raise LipidXException(
                    "The given tolerance is not of TypeTolerance()"
                )

            # override resolution
            if (
                res_by_steps
            ):  # NOTE this is not used only here as reference implementation
                current_m = listResult[count][current + index][0]
                if current_m >= res_steps[0][0]:
                    res = res_steps[0][1]
                elif current_m <= res_steps[-1][0]:
                    res = res_steps[-1][1]
                else:
                    for rs in res_steps:
                        if rs[0] < current_m:
                            res = last
                            break
                        last = rs[1]
                    # res = next((rs[1] for rs in res_steps if rs[0] < current_m)) cant do this because I need one before the one that is returned

            if res_by_fullbin:
                if binres == binres_og and newres1 is not None:
                    # bin_at_mass = bin[0][0] to reduce  just based on mass
                    binres = newres1
                res = binres  # * (bin[0][0] / bin_at_mass) to reduce  just based on mass

            while abs(listResult[count][current + index][0] - bin[0][0]) < res:
                if (
                    res_by_fullbin
                    and binsize > 1
                    and res_by_fullbin
                    and len(listResult[count][current + index][1])
                    >= binsize * 0.95
                ):  # there is more than one bin (its just a merge) and the element is not already full
                    break  # bin is already full

                bin.append(listResult[count][current + index])

                if (current + index) < (len(listResult[count]) - 1):
                    index += 1
                else:
                    break

            current += index

            if res_by_fullbin and len(bin) >= binsize * 0.95:
                newres = max((b[0] for b in bin)) - min((b[0] for b in bin))
                newres = newres * 7  # to make it very loose
                if newres < binres and newres > 0.00001:
                    binres = newres
                    if newres1 is None:
                        newres1 = newres
                        # dont set calcselectionwindow here because its very tight
                    # bin_at_mass = bin[0][0] to reduce  just based on mass

            # go for intensity weighted average and non-weighted avg
            if not intensityWeightedAvg:
                # calc average of the bin
                cnt = 0
                sum = 0
                avg = 0
                for i in bin:
                    for specentry in i[1]:
                        sum += specentry.mass
                        cnt += 1
                avg = sum / cnt

            else:
                cnt = 0
                sumMass = 0
                sumIntensity = 0
                avg = 0
                for i in bin:
                    for specentry in i[1]:
                        sumMass += (
                            specentry.mass * specentry.content["intensity"]
                        )
                        sumIntensity += specentry.content["intensity"]
                        cnt += 1
                if sumIntensity == 0:
                    raise LipidXException(
                        "A peak intensity is zero. This should not be."
                        + " Probably you imported profile spectra instead of centroided."
                    )
                avg = sumMass / sumIntensity

            resultingSpecEntries = []
            for i in bin:
                resultingSpecEntries += i[1]

            # filtering starts here, default setings imply no filtering
            fadi_ratio = 1.0
            if fadi_denominator is not None and fadi_denominator > 0.0:
                fadi_ratio = (
                    cnt / float(fadi_denominator)
                    if fadi_denominator is not None and fadi_denominator != 0.0
                    else 1.0
                )

            if fadi_ratio >= fadi_percentage:
                listResult[count + 1].append([avg, resultingSpecEntries])

            # if 'current' is last entry of our non-merged spectrum (count)
            # just add it to the bin
            if listResult[count][current] == listResult[count][-1]:
                if not listResult[count][current] in bin:
                    listResult[count + 1].append(
                        [
                            listResult[count][current][0],
                            listResult[count][current][1],
                        ]
                    )

    ##################
    ### gen output ###

    listOutput = []
    for entry in listResult[-1]:
        cluster = {}
        clusterToMerge = {}
        mass = None
        entryCollection = {}
        for i in entry[1]:  # entry[1] contains the merged specEntries
            mass = i.mass  # store the mass for empty specEntries

            if (
                i.content["sample"] not in cluster
            ):  # fill the output dictionary 'cluster'
                cluster[i.content["sample"]] = i

                if merge:
                    clusterToMerge[i.content["sample"]] = [
                        i
                    ]  # collect the entries for a maybe merging

            else:  # the sample has already an entry, so we have to merge
                if merge:  # ...but only if merge is switched on
                    clusterToMerge[i.content["sample"]].append(
                        i
                    )  # add the related entry to the cluster which should be merged

        if merge:  # merge if merging function is given
            for sample in listSamples:
                if sample in clusterToMerge:
                    if (
                        len(clusterToMerge[sample]) > 1
                    ):  # merge only, if there is more than one entry
                        cluster[sample] = merge(
                            sample,
                            clusterToMerge[sample],
                            linearAlignment,
                            mergeTolerance,
                            mergeDeltaRes,
                            bintolerance=bintolerance,
                            res_by_fullbin=res_by_fullbin,
                        )
                    else:
                        cluster[sample] = clusterToMerge[sample][0]

        # fill cluster with empty masses to have a full entry
        for sample in listSamples:
            if sample not in cluster:
                cluster[sample] = specEntry(mass=entry[1][0].mass)

        # for sample in listSamples:
        # 	if not cluster.has_key(sample):
        # 		if mass:
        # 			cluster[sample] = specEntry(
        # 					mass = mass,
        # 					content = None)
        # 		else:
        # 			for s in listSamples:
        # 				if i.content.has_key(s):
        # 					mass = i.mass
        # 					break
        # 			cluster[sample] = specEntry(
        # 					mass = mass,
        # 					content = None)

        listOutput.append(cluster)

    if res_by_fullbin:
        listOutput = list(reversed(listOutput))
    ### gen output ###
    ##################

    return listOutput


def sparseHierarchicalAlignment(
    listSamples,
    dictSamples,
    tolerance,
    deltaRes=None,
    minocc=None,
    msThreshold=None,
    minMass=None,
):
    # get max length of peak in the spectra
    speclen = 0
    for k in list(dictSamples.keys()):
        if speclen < len(dictSamples[k]):
            speclen = len(dictSamples[k])

    # nothing there? Return nothing.
    if speclen < 1:
        return None

    # just one fragment? Return the result imediatly.
    mass = None
    if speclen == 1:
        cluster = {}
        for sample in list(dictSamples.keys()):
            try:
                mass = dictSamples[sample][0].mass
                cluster[sample] = specEntry(
                    mass=dictSamples[sample][0].mass,
                    content=dictSamples[sample][0].content,
                )
            except IndexError:
                if mass:
                    cluster[sample] = specEntry(mass=mass, content=None)
                else:
                    for s in list(dictSamples.keys()):
                        try:
                            mass = dictSamples[s][0].mass
                        except IndexError:
                            pass
                    cluster[sample] = specEntry(mass=mass, content=None)

        return [cluster]

    ###########################
    ### Start the algorithm ###

    # initialize output list algorithm
    spectrum = []

    # join all peaks into one list and add an unique index to each entry
    for index_sample in range(len(list(dictSamples.keys()))):
        for index_peak in range(len(list(dictSamples.values())[index_sample])):
            spectrum.append(
                (
                    list(dictSamples.values())[index_sample][index_peak],
                    (index_sample + 1) * (index_peak + 1),
                )
            )

    # sort the list to have a sparse data set
    spectrum.sort()

    # idea: get all peaks falling into the window of 2 * resolution
    # and cluster this list. Then remove all peaks which were in the
    # first cluster from the spectrum and repeat this step until
    # the end. Although clusters are redundantly calculated,
    # we prevent the algorithm to introduce a linear shift, as it
    # is the case with Kazmi's algorithm. This is because the algorithm
    # might cluster peaks from different origins, since their
    # distribution might overlap within the resolution.

    results = []
    while spectrum != []:  # circle throught the merged peak list
        ### get the window size from the first peak of the spectrum ###
        if isinstance(tolerance, TypeTolerance):
            if tolerance.kind == "Da":
                res = tolerance.da
            else:
                if deltaRes:
                    tmp = (
                        tolerance.tolerance
                        + (spectrum[0][0].mass - minMass) * deltaRes
                    )
                else:
                    tmp = tolerance.tolerance
                res = spectrum[0][0].mass / tmp

        ### collect the first peaks which are within two times the resolution ###
        # the result is in 'toCluster'
        toCluster = []
        index_peak = 0
        pivot = spectrum[0][0].mass
        try:
            while pivot + 2 * res > spectrum[index_peak][0].mass:
                toCluster.append(spectrum[index_peak])
                del spectrum[index_peak]
        except IndexError:
            r = []
            for i in toCluster:
                r.append(i[0])
            results += [r]
            return results

        ### cluster the bin ###
        cl = HierarchicalClustering(
            toCluster,
            lambda x, y: abs(x[0].mass - y[0].mass),
            linkage="complete",
        )

        # get all clusters which are at the level of the resolution
        c = cl.getlevel(res)

        ### subtract all peaks from the bin 'toCluster' which are in the ###
        ### first cluster                                                ###
        curtain = []
        if isinstance(c[0], type([])):
            for i in c[0]:
                append = True
                for tc in toCluster:
                    if i[1] == tc[1]:
                        append = False
                if append:
                    curtain.append(i)
        else:
            append = True
            for tc in toCluster:
                if c[0][1] == tc[1]:
                    append = False
            if append:
                curtain.append([c])

        # add the remaining peaks back to the original spectrum
        spectrum = curtain + spectrum

        ### store the first cluster as a result ###
        if isinstance(c[0], type([])):
            for i in c:
                r = []
                for j in i:
                    r.append(j[0])  # store only the specEntry
                results.append(r)
        else:
            results.append([c[0][0]])

    pass


def heuristicAlignment(
    listSamples,
    dictSamples,
    tolerance,
    deltaRes=None,
    minocc=None,
    msThreshold=None,
    minMass=None,
):
    """
    The algorithm is taken from "Alignment of high resolution mass spectra:
    development of a heuristic aprroach for metabolomics" by
    Saira Kazmi et al (2006). Metabolomics 2(2):75-83.

    It is optimized for the available data structures. Therefore the input
    is an own format (specEntry) provided as list in listSamples. Furthermore,
    dictSamples: is the list of all sample names (keys from dict)
    tolerance: is a TypeTolerance type with the
            tolerance as da, ppm or res.
    deltaRes: if the tolerance is given as resolution, the deltaRes
            states the resolution change over the masses.

    The output is a list of specEntry"""

    # get max length of peak in the spectra
    speclen = 0
    for k in listSamples:
        if speclen < len(dictSamples[k]):
            speclen = len(dictSamples[k])

    # nothing there? Return nothing.
    if speclen < 1:
        return None

    # just one fragment? Return the result imediatly.
    mass = None
    if speclen == 1:
        cluster = {}
        for sample in listSamples:
            try:
                mass = dictSamples[sample][0].mass
                cluster[sample] = specEntry(
                    mass=dictSamples[sample][0].mass,
                    content=dictSamples[sample][0].content,
                )
            except IndexError:
                if mass:
                    cluster[sample] = specEntry(mass=mass, content=None)
                else:
                    for s in listSamples:
                        try:
                            mass = dictSamples[s][0].mass
                        except IndexError:
                            pass
                    cluster[sample] = specEntry(mass=mass, content=None)

        return [cluster]

    ###########################
    ### Start the algorithm ###

    ### initiate A, BA and BB -> the initiate cluster ###
    A = {}
    output = []

    # generate a dictionary with entries {sample1 : 0, sample2 : 0, ... }
    # this are the indices for the current peaks of all samples
    peakIndex = {}.fromkeys(listSamples, 0)

    # read smallest unclassified peak from each sample"
    mass = None
    for sample in listSamples:
        try:
            mass = dictSamples[sample][peakIndex[sample]].mass
            A[sample] = [
                dictSamples[sample][peakIndex[sample]].mass,
                dictSamples[sample][peakIndex[sample]].content,
            ]
        except IndexError:
            if mass:
                A[sample] = [mass, None]
            else:
                for s in listSamples:
                    try:
                        mass = dictSamples[s][peakIndex[s]].mass
                    except IndexError:
                        pass

                A[sample] = [mass, None]

    # find the smallest mass in dictA:
    smallest = ["", 10000, 0]
    for sample in listSamples:
        if smallest[1] > A[sample][0]:
            smallest = [sample] + deepcopy(A[sample])
    pivotSample = smallest[0]
    if minMass:
        smallest_spec = minMass
    else:
        smallest_spec = deepcopy(smallest[1])

    # form a new bin
    BA = []
    BA.append(smallest)

    # get the window size
    if tolerance.kind == "Da":
        res = tolerance.da
    else:
        res = tolerance.getTinDA(smallest[1])

    # read in the next value for A[smallest]
    mass = None
    for sample in listSamples:
        if sample == pivotSample:
            try:
                peakIndex[sample] += 1

                mass = dictSamples[sample][peakIndex[sample]].mass
                A[sample][0] = dictSamples[sample][peakIndex[sample]].mass
                A[sample][1] = dictSamples[sample][peakIndex[sample]].content

            except IndexError:
                if mass:
                    A[sample] = [mass, None]
                else:
                    for s in listSamples:
                        try:
                            mass = dictSamples[s][peakIndex[s]].mass
                        except IndexError:
                            pass
                    A[sample] = [mass, None]

        else:
            if abs(smallest[1] - A[sample][0]) < res:
                BA.append([sample] + deepcopy(A[sample]))

                try:
                    # get next entry for A
                    peakIndex[sample] += 1

                    mass = dictSamples[sample][peakIndex[sample]].mass

                    A[sample][0] = dictSamples[sample][peakIndex[sample]].mass
                    A[sample][1] = dictSamples[sample][
                        peakIndex[sample]
                    ].content

                except IndexError:
                    if mass:
                        A[sample] = [mass, None]
                    else:
                        for s in listSamples:
                            try:
                                mass = dictSamples[s][peakIndex[s]].mass
                            except IndexError:
                                pass
                        A[sample] = [mass, None]

    if speclen == 2:
        entry = []
        for sample in listSamples:
            entry.append([sample] + A[sample])
        output = [BA]
        output.append(deepcopy(entry))
        isNotAtTheEndOfTheSpectrum = False
    else:
        # initiate upcoming loop
        isNotAtTheEndOfTheSpectrum = True

    endTrigger = {}
    for sample in listSamples:
        endTrigger[sample] = 0

    while isNotAtTheEndOfTheSpectrum:
        ### repeat the steps above

        # find the smallest mass in dictA:
        smallest = ["", 10000, 0]
        for sample in listSamples:
            if smallest[1] > A[sample][0]:
                smallest = [sample] + deepcopy(A[sample])
        pivotSample = smallest[0]

        # form a new bin
        BB = []
        BB.append(deepcopy(smallest))

        # get the window size
        if tolerance.kind == "Da":
            res = tolerance.da
        else:
            if deltaRes > 0:
                res = tolerance.getTinDA(smallest[1])

        mass = None
        # read in the next value for A[smallest]
        for sample in listSamples:
            if sample == pivotSample:
                peakIndex[sample] += 1
                try:
                    mass = dictSamples[sample][peakIndex[sample]].mass
                    A[sample][0] = dictSamples[sample][peakIndex[sample]].mass
                    A[sample][1] = dictSamples[sample][
                        peakIndex[sample]
                    ].content

                except IndexError:
                    # peakIndex[sample] -= 1
                    endTrigger[sample] = 1

                    if mass:
                        A[sample] = [mass, None]
                    else:
                        for s in listSamples:
                            try:
                                mass = dictSamples[s][peakIndex[s]].mass
                            except IndexError:
                                pass
                        A[sample] = [mass, None]

            else:
                if abs(smallest[1] - A[sample][0]) < res:
                    BB.append([sample] + deepcopy(A[sample]))

                    # get next entry for A
                    peakIndex[sample] += 1
                    try:
                        mass = dictSamples[sample][peakIndex[sample]].mass
                        A[sample][0] = dictSamples[sample][
                            peakIndex[sample]
                        ].mass
                        A[sample][1] = dictSamples[sample][
                            peakIndex[sample]
                        ].content

                    except IndexError:
                        # peakIndex[sample] -= 1
                        endTrigger[sample] = 1
                        if mass:
                            A[sample] = [mass, None]
                        else:
                            for s in listSamples:
                                try:
                                    mass = dictSamples[s][peakIndex[s]].mass
                                except IndexError:
                                    pass
                            A[sample] = [mass, None]

        ### adjust bins BA and BB

        # find largest peak in BA
        largestBA = ["", 0, 0]
        for i in BA:
            if i[1] > largestBA[1]:
                largestBA = deepcopy(i)

        # find smallest peak in BB
        smallestBB = ["", 100000, 0]
        for i in BB:
            if i[1] < smallestBB[1]:
                smallestBB = deepcopy(i)

        if abs(smallestBB[1] - largestBA[1]) < res:
            # union dictBA and dictBB
            B = BA + BB
            cl = HierarchicalClustering(
                B, lambda x, y: abs(x[1] - y[1]), linkage="complete"
            )
            C = cl.getlevel(res)

            BB = deepcopy(C[-1])

            if len(C) >= 2:
                BA = deepcopy(C[-2])
            else:
                BA = []

            if len(C) >= 3:
                for i in C[:-2]:
                    output.append(deepcopy(i))
        else:
            sum = 0
            for i in BA:
                sum += i[1]
            mean = float(sum) / len(BA)

            withinRange = False
            for i in BA:
                if abs(i[1] - mean) > res:
                    withinRange = True
                    break

            if withinRange:
                # repeat the clustering step
                cl = HierarchicalClustering(
                    BA, lambda x, y: abs(x[1] - y[1]), linkage="complete"
                )
                C = cl.getlevel(res)

                BB = deepcopy(C[-1])

                if len(C) >= 2:
                    BA = deepcopy(C[-2])
                else:
                    BA = []

                if len(C) >= 3:
                    for i in C[:-2]:
                        output.append(deepcopy(i))

        output.append(deepcopy(BA))
        BA = deepcopy(BB)

        for k in list(peakIndex.keys()):
            if not peakIndex[k] < speclen:
                isNotAtTheEndOfTheSpectrum = False

        if not isNotAtTheEndOfTheSpectrum:
            # gen entry for the output format
            entry = []
            for sample in listSamples:
                entry.append([sample] + A[sample])
            output.append(deepcopy(entry))

            for sample in listSamples:
                peakIndex[sample] += 1

        sum = 0
        for i in list(endTrigger.values()):
            sum += i

        if sum == len(list(endTrigger.values())):
            output.append(BA)
            isNotAtTheEndOfTheSpectrum = False

    # sort the clusters, since they always come unsorted
    for index in range(len(output)):
        sum = 0
        length = 0
        for i in output[index]:
            # check if there are dummy entries, they should not go to the avg
            # (dummy entries have a 'None' in content (i[2]))
            if i[2]:
                sum += i[1]
                length += 1

        if length > 0:
            avg = sum / length
        else:
            avg = 0

        output[index] = [avg, output[index]]

    output.sort(cmp=lambda x, y: cmp(x[0], y[0]))

    ### put the output in a specEntry list ###
    listMSSpec = []
    for index in range(len(output)):
        cluster = {}
        for cl in output[index][1]:
            if cl[0] in listSamples:
                cluster[cl[0]] = specEntry(mass=cl[1], content=cl[2])

        listMSSpec.append(cluster)
        ### this makes it: specEntry[index] = [avg, cluster]

    ### Start the algorithm ###
    ###########################

    ###########################################
    ### routine for checking empty elements ###

    index = 0
    while index < len(listMSSpec):
        # check for empty entries
        mass = None
        noMassFound = False
        for sample in listSamples:
            if sample in listMSSpec[index]:
                if listMSSpec[index][sample].mass:
                    mass = listMSSpec[index][sample].mass
                    content = listMSSpec[index][sample].content

                    listMSSpec[index][sample] = specEntry(
                        mass=mass, content=content
                    )

                else:
                    if not mass:
                        for s in listSamples:
                            if (
                                s in listMSSpec[index]
                                and listMSSpec[index][s].mass
                            ):
                                mass = listMSSpec[index][s].mass
                                break

                    if not mass:
                        noMassFound = True

                    if mass:
                        listMSSpec[index][sample] = specEntry(
                            mass=mass, content=None
                        )
            else:
                if not mass:
                    for s in listSamples:
                        if (
                            s in listMSSpec[index]
                            and listMSSpec[index][s].mass
                        ):
                            mass = listMSSpec[index][s].mass
                            break

                if not mass:
                    noMassFound = True

                if mass:
                    listMSSpec[index][sample] = specEntry(
                        mass=mass, content=None
                    )

        if noMassFound:
            del listMSSpec[index]
        else:
            index += 1

    ### routine for checking empty elements ###
    ###########################################

    return listMSSpec


def mergeListMsms(
    sample,
    listSpecEntries,
    align,
    mergeTolerance,
    mergeDeltaRes,
    bintolerance=None,
    res_by_fullbin=False,
):
    """Merge several MS/MS scans. The specEntries have the precursor mass and
    the MS/MS lists in their .content attribute.

    This is the averaging algorithm for MS/MS spectra. The "mergeTolerance" is
    misleading, because this is actually the MSMSresolution."""

    length = len(listSpecEntries)

    out = listSpecEntries[0]
    outMSMS = listSpecEntries[0].content["MSMS"]
    # right = specEntryRight.content['MSMS']

    ### first: put the MS/MS lists together in a new specEntry ###

    sumMass = 0
    sumPrecurmass = 0
    listScanNumber = []
    listRetentionTime = []
    listPeaksCount = []
    listTotIonCurrent = []
    listFileName = []
    sumEntries = []
    sumScanCount = 0
    for entry in listSpecEntries:
        sumMass += entry.mass

        e = entry.content["MSMS"]
        sumPrecurmass += e.precurmass
        listScanNumber.append(e.scanNumber)
        listRetentionTime.append(e.retentionTime)
        listPeaksCount.append(e.peaksCount)
        listTotIonCurrent.append(e.totIonCurrent)
        listFileName.append(e.fileName)
        sumEntries += e.entries
        sumScanCount += e.scanCount

    out.mass = sumMass / length
    outMSMS.precurmass = sumPrecurmass / length
    outMSMS.scanNumber = listScanNumber
    outMSMS.retentionTime = listRetentionTime
    outMSMS.peaksCount = listPeaksCount
    outMSMS.totIonCurrent = listTotIonCurrent
    outMSMS.entries = sumEntries
    outMSMS.scanCount = sumScanCount

    # TODO: assert charge and polarity are the same
    # if not left.charge == right.charge:
    # 	return None
    # if not left.polarity == right.polarity:
    # 	return None
    # left.msms = []
    # left.entries = [[] for i in range(0,2)]

    ####################################
    ### averaging of the MS/MS scans ###

    # make a new specEntries dict for the averaging algorithm
    dictSpecEntries = {"one": []}
    for entry in outMSMS.entries:
        dictSpecEntries["one"].append(
            specEntry(
                mass=entry[0],
                content={
                    "sample": "one",
                    "intensity": entry[1],
                    "peak_info": entry[2:],
                },
            )
        )

    # start the averaging algorithm
    from . import readSpectra

    fadi_percentageMSMS = readSpectra.fadi_percentageMSMS
    if dictSpecEntries["one"] != []:
        listClusters = align(
            ["one"],
            dictSpecEntries,
            mergeTolerance,
            intensityWeightedAvg=True,
            merge=mergeSumIntensity,
            deltaRes=mergeDeltaRes,
            minMass=sorted(dictSpecEntries["one"])[0].mass,
            fadi_denominator=length,
            fadi_percentage=fadi_percentageMSMS,
            bintolerance=bintolerance,
            res_by_fullbin=res_by_fullbin,
        )

        # for cl in listClusters:
        # 	str = ''
        # 	for sample in dictSpecEntries.keys():#cl.keys():
        # 		if cl.has_key(sample):
        # 			if cl[sample].content:
        # 				str +=  "  %.4f  " % cl[sample].mass
        # 				#str +=  "  %.4f  " % cl[sample].content['intensity']
        # 			else:
        # 				try:
        # 					str +=  " /%.4f/ " % cl[sample].mass
        # 				except TypeError:
        # 					print "TypeError:", cl[sample].mass
        # 		else:
        # 			str += " / empty  / "
        # 	print str

        # put the resulting list to the output specEntry
        listEntries = []
        for cl in listClusters:
            entry = [[], []]
            entry[0] = cl["one"].mass
            entry[1] = cl["one"].content["intensity"]
            for e in cl["one"].content["peak_info"]:
                entry.append(e)
            listEntries.append(entry)
        listSpecEntries[0].content["MSMS"].entries = listEntries

    else:  # there were no entries summed in outMSMS.entries
        pass

    ### averaging of the MS/MS scans ###
    ####################################

    return listSpecEntries[0]


def mergeSumIntensity(
    sample,
    listSpecEntries,
    align,
    mergeTolerance,
    mergeDeltaRes,
    bintolerance=None,
    res_by_fullbin=False,
):  # bintolerance , res_by_fullbin unuse but needed for the arg signature
    """This function calculates the average intensity (average over the given
    peaks and not from all scans) and the average weighted m/z for the peak mass.
    """

    out = listSpecEntries[0]

    sumMass = 0
    sumMassIntensity = 0
    sumIntensity = 0
    for entry in listSpecEntries:
        sumMass += entry.mass
        sumMassIntensity += entry.mass * entry.content["intensity"]
        sumIntensity += entry.content["intensity"]

    if not sumIntensity > 0.0:
        return out

    out.mass = sumMassIntensity / sumIntensity
    # out.content['intensity'] = sumIntensity
    out.content["intensity"] = sumIntensity / len(listSpecEntries)

    return out


def mkList(left, right):
    if isinstance(left, type([])) and isinstance(right, type([])):
        left = left + right
    if not isinstance(left, type([])) and isinstance(right, type([])):
        left = [left] + right
    if isinstance(left, type([])) and not isinstance(right, type([])):
        left = left + [right]
    if not isinstance(left, type([])) and not isinstance(right, type([])):
        left = [left, right]


def mergeListMsms_noContainer(
    sample, listSpecEntries, align, mergeTolerance, mergeDeltaRes
):
    """Merge several MS/MS scans. The specEntries have the precursor mass and
    the MS/MS lists in their .content attribute."""

    length = len(listSpecEntries)

    out = listSpecEntries[0]
    outEntries = listSpecEntries[0].content["entries"]
    # right = specEntryRight.content['MSMS']

    ### first: put the MS/MS lists together in a new specEntry ###

    sumMass = 0
    sumEntries = []
    sumScanCount = 0
    for entry in listSpecEntries:
        sumMass += entry.mass

        e = entry.content["entries"]
        sumEntries += e
        sumScanCount += entry.content["scanCount"]

    out.mass = sumMass / length

    ####################################
    ### averaging of the MS/MS scans ###

    # make a new specEntries dict for the averaging algorithm
    dictSpecEntries = {"one": []}
    for entry in outEntries:
        dictSpecEntries["one"].append(
            specEntry(
                mass=entry[0],
                content={
                    "sample": "one",
                    "intensity": entry[1],
                    "peak_info": entry[2:],
                },
            )
        )

    # start the averaging algorithm
    if dictSpecEntries["one"] != []:
        listClusters = align(
            ["one"],
            dictSpecEntries,
            mergeTolerance,
            intensityWeightedAvg=True,
            merge=mergeSumIntensity,
            deltaRes=mergeDeltaRes,
            minMass=sorted(dictSpecEntries["one"])[0].mass,
        )

        # put the resulting list to the output specEntry
        listEntries = []
        for cl in listClusters:
            entry = [[], []]
            entry[0] = cl["one"].mass
            entry[1] = cl["one"].content["intensity"]
            for e in cl["one"].content["peak_info"]:
                entry.append(e)
            listEntries.append(entry)
        listSpecEntries[0].content["entries"] = listEntries
        listSpecEntries[0].content["scanCount"] = sumScanCount

    else:  # there were no entries summed in outMSMS.entries
        pass

    ### averaging of the MS/MS scans ###
    ####################################

    return listSpecEntries[0]


def alignPIS(
    sc,
    listPolarity,
    numLoops=None,
    deltaRes=0,
    minocc=None,
    alignmentMS="linear",
):
    """Align the MS spectra."""

    ### this stores the precursors as tab-separated file ###
    # for key in sc.listSamples:
    # 	f = open('pr-' + key[:-6] + '.txt', 'w')
    # 	for entry in sc.dictSamples[key].listPrecurmass:
    # 		f.write("%.6f\t%.4f\n" % (entry.precurmass, entry.intensity))
    # 	f.close()
    ### the end                                          ###

    ### merge multiple scans ###
    listSample = []
    listMSmass = []
    for key in sc.listSamples:
        polarity = sc.dictSamples[key].polarity

        # generate list of all sample names belonging to the polarity
        listSample.append(key)

        dictScans = {}

        for msmsEntry in sc.dictSamples[key].listMsms:
            precurmass = "%.2f" % msmsEntry.precurmass
            if precurmass not in dictScans:
                dictScans[precurmass] = [msmsEntry]
            else:
                dictScans[precurmass].append(msmsEntry)

        ### start with scan averaging ###
        dictMassEntry = {}
        dictPISResult = {}
        for mass in sorted(
            list(dictScans.keys()), cmp=lambda x, y: cmp(float(x), float(y))
        ):
            dictMassEntry[mass] = []
            dictSpecEntry = {}

            count = 1
            for entry in dictScans[mass]:
                mKey = "%s%d" % (mass, count)
                dictSpecEntry[mKey] = []

                for e in entry.entries:
                    dictSpecEntry[mKey].append(
                        specEntry(
                            mass=e[0],
                            content={"sample": mKey, "intensity": e[1]},
                        )
                    )
                count += 1

            if alignmentMS == "linear":
                listClusters = linearAlignment(
                    list(dictSpecEntry.keys()),
                    dictSpecEntry,
                    sc.options["MSMSresolution"],
                    merge=mergePIS,
                )
            elif alignmentMS == "heuristic":
                listClusters = heuristicAlignment(
                    list(dictSpecEntry.keys()),
                    dictSpecEntry,
                    sc.options["MSMSresolution"],
                )

            ### end start with scan averaging ###

            # for cl in listClusters:
            # 	str = ''
            # 	for sample in dictSpecEntry.keys():#cl.keys():
            # 		if cl.has_key(sample):
            # 			if cl[sample].content:
            # 				str +=  "  %.4f  " % cl[sample].mass
            # 				#str +=  "  %.4f  " % cl[sample].content['intensity']
            # 			else:
            # 				try:
            # 					str +=  " /%.4f/ " % cl[sample].mass
            # 				except TypeError:
            # 					print "TypeError:", cl[sample].mass
            # 		else:
            # 			str += " / empty  / "
            # 	print str

            for cl in listClusters:
                ### calculate intensity weigthed mass average ###

                # get maximum intensity
                maxIntensity = 0
                for sample in list(dictSpecEntry.keys()):
                    if cl[sample].content:
                        if cl[sample].content["intensity"] > maxIntensity:
                            maxIntensity = cl[sample].content["intensity"]

                # calculate the weighted average
                numEntries = 0
                sumMass = 0
                sumIntensity = 0
                sumIntensityW = 0
                sumIntensityWMass = 0
                for sample in list(dictSpecEntry.keys()):
                    if cl[sample].content:
                        numEntries += 1
                        sumMass += cl[sample].mass
                        sumIntensity += cl[sample].content["intensity"]
                        sumIntensityW += (
                            cl[sample].content["intensity"] / maxIntensity
                        )
                        sumIntensityWMass += (
                            cl[sample].content["intensity"] / maxIntensity
                        ) * cl[sample].mass

                # if the peak is there, append it on the result list
                if sumIntensityWMass > 0.0:
                    avgMass = sumIntensityWMass / sumIntensityW
                    ### end calculate intensity weigthed mass average ###

                    ### collect result for subsequent alignment ###
                    dictMassEntry[mass].append(
                        specEntry(
                            mass=avgMass,
                            content={
                                "sample": mass,
                                "intensity": sumIntensity / numEntries,
                                "fragment": mass,
                                "numScans": numEntries,
                            },
                        )
                    )
                    ### end collect result for subsequent alignment ###

        ### align the precursor masses ###
        dictSpecEntry = dictMassEntry
        # del dictMassEntry

        if alignmentMS == "linear":
            listClusters = linearAlignment(
                list(dictSpecEntry.keys()),
                dictSpecEntry,
                sc.options["MSMSresolution"],
                merge=mergePIS,
            )
        elif alignmentMS == "heuristic":
            listClusters = heuristicAlignment(
                list(dictSpecEntry.keys()),
                dictSpecEntry,
                sc.options["MSMSresolution"],
            )

        # for cl in listClusters:
        # 	str = ''
        # 	for sample in dictSpecEntry.keys():#cl.keys():
        # 		if cl.has_key(sample):
        # 			if cl[sample].content:
        # 				str +=  "  %.4f  " % cl[sample].mass
        # 				#str +=  "  %.4f  " % cl[sample].content['intensity']
        # 			else:
        # 				try:
        # 					str +=  " /%.4f/ " % cl[sample].mass
        # 				except TypeError:
        # 					print "TypeError:", cl[sample].mass
        # 		else:
        # 			str += " / empty  / "
        # 	print str

        ### end align the precursor masses ###

        dictPISResult[key] = listClusters

        # use well known specEntry type
        listMSSpectrum = []
        for cl in listClusters:
            m = 0
            count = 0
            peakListMSMS = []
            peakListMS = []
            for sample in list(dictSpecEntry.keys()):
                if sample in cl:
                    if cl[sample].content:
                        m += cl[sample].mass
                        count += 1
                        peakListMSMS.append(
                            [float(sample), cl[sample].content["intensity"]]
                        )
                        peakListMS.append([m, cl[sample].content["intensity"]])
                        numScans = cl[sample].content["numScans"]

            if count > 0.0:
                avgMass = m / count

                s = specEntry(
                    mass=avgMass,
                    content={
                        "peakListMS": peakListMS,
                        "peakListMSMS": peakListMSMS,
                        "count": count,
                        "numScans": numScans,
                    },
                )

                listMSSpectrum.append(s)

        ### do the transpose ###
        ########################

        # lpdxSample = Sample(
        # 			sampleName = key,
        # 			sourceDir = key,
        # 			sourceFile = key,
        # 			polarity = polarity,
        # 			options = sc.options,
        # 			MSMSresolution = sc.options['MSMSresolution'],
        # 			MSthreshold = sc.options['MSthreshold'])

        sc.dictSamples[key].listMsms = []

        for i in listMSSpectrum:
            sc.dictSamples[key].listMsms.append(
                MSMS(
                    i.mass,
                    charge=None,
                    polarity=polarity,
                    fileName=key,
                    scanNumber=None,
                    retentionTime=None,
                    peaksCount=None,
                    totIonCurrent=None,
                )
            )

            # raise LipidXException("HERE IS TODO. What happens with the PIS spectra?")
            # lpdxSample.listMsms.append(MSMS(
            # 			i.mass,
            # 			charge = None,
            # 			polarity = polarity,
            # 			fileName = key,
            # 			scanNumber = None,
            # 			retentionTime = None,
            # 			peaksCount = None,
            # 			totIonCurrent = None))

            ### sort out peaks below the given threshold
            threshold = sc.options["MSMSthreshold"]

            if sc.options["MSMSthresholdType"] == "relative":
                # find base peak
                basePeakIntensity = 0
                for m in i.content["peakListMSMS"]:
                    if basePeakIntensity < m[1]:
                        basePeakIntensity = m[1]

                threshold *= basePeakIntensity

            thrshld = threshold / sqrt(i.content["numScans"])

            for j in i.content["peakListMSMS"]:
                if j[1] >= thrshld:
                    sc.dictSamples[key].listMsms[-1].entries.append(j)
            sc.dictSamples[key].listMsms[-1].scanCount = i.content["numScans"]

        # sc.dictSamples[key] = lpdxSample
        try:
            set_PrecurmassFromMSMS(sc.dictSamples[key], chg=polarity)
        except AttributeError:
            raise LipidXException(
                "The spectra you want to import are not "
                + "Precursor Ion Scan (PIS) spectra. Please check the 'PIS' switch "
                + "at the 'Import Source' panel. [alignPIS]"
            )

    return None


def mergePIS(sample, listSpecEntries, align, mergeTolerance, mergeDeltaRes):
    # print sample
    # for i in listSpecEntries:s:
    # 	print "----"
    # 	print i.mass
    # 	print i.content
    return listSpecEntries[0]
    pass


def doClusterMSMS(res, msms):
    retMsms = MSMS(
        mass=msms.precurmass,
        retentionTime=None,
        charge=msms.charge,
        polarity=msms.polarity,
        fileName=msms.fileName,
    )

    listEntries = msms.entries
    listEntries.sort()

    iterEntry = listEntries.__iter__()

    precurmasslist = []

    # get pivotmass
    try:
        pivot = next(iterEntry)
    except StopIteration:
        return msms

    while iterEntry:
        # set lookaheadFlag. It is important for the last entry
        lookaheadFlag = False

        # get first mass
        precurmasslist = []
        precurmasslist.append(deepcopy(pivot))

        # next mass
        try:
            lookahead = next(iterEntry)
        except StopIteration:
            break

        # hpb
        if isinstance(res, TypeTolerance):
            hpb = pivot[0] / res.tolerance
        else:
            hpb = pivot[0] / res

        # go through peaks
        while lookahead[0] <= pivot[0] + hpb:
            precurmasslist.append(deepcopy(lookahead))
            try:
                lookahead = next(iterEntry)
            except StopIteration:
                break
            lookaheadFlag = True

        pivot = deepcopy(lookahead)

        # calc average mass with the intensity as weight

        # get max intensity
        maxint = 0
        for i in precurmasslist:
            if i[1] > maxint:
                maxint = i[1]

        # get intensity weights and the sum of all precursmass's
        sumcount = 0
        sumprecurmass = 0
        for i in precurmasslist:
            if maxint != 0.0:
                i[0] = (i[1] / maxint) * i[0]
                sumprecurmass = sumprecurmass + i[0]
                sumcount = sumcount + (i[1] / maxint)
            else:
                sumprecurmass = sumprecurmass + i[0]
                sumcount = sumcount + (i[1])

        if sumprecurmass == 0:
            raise LipidXException("Zero sum in precursormass. This is nogood.")

        # get intensity average
        sumintensity = 0
        for i in precurmasslist:
            sumintensity = sumintensity + i[1]

        # problems with zero valued sumcount, but this should not be...
        if sumcount == 0.0:
            sumcount = 1

        avgprecurmass = sumprecurmass / sumcount
        avgintensity = sumintensity  # / len(precurmasslist)
        retMsms.entries.append([avgprecurmass, avgintensity])

    # just append the last entry, because otherwise it will be deleted.
    # This is ok, since if it would be in the lpdxCluster resolution range,
    # it would be deleted anyway.
    retMsms.entries.append([msms.entries[-1][0], msms.entries[-1][1]])
    return retMsms


def doClusterSample(res, sample):
    """lpdxCluster algorithm
    see p.1.b
    Go through the masses, mass by mass, and look if there are masses in the
    sample.accuracy range just calculated. More precise:

    begin with the smallest mass in the ordered list of masses
    while there is next mass
            1) Get next mass and make it pivot
            2) look sample.accuracy to the right.
                    If there is a mass take it and make mass new pivot
            3) look 2 * sample.accuracy to the right.
            If there is the first mass goto 2)
                    else end algorithm
    """

    sample.listPrecurmass.sort()

    itersampl = sample.listPrecurmass.__iter__()

    newsample = deepcopy(sample)
    newsample.listPrecurmass = []

    flag = False
    precurmasslist = []

    # get pivotmass
    try:
        pivot = next(itersampl)
    except StopIteration:
        return sample

    while itersampl:
        # get first mass
        precurmasslist = []
        precurmasslist.append(deepcopy(pivot))

        # next mass
        try:
            lookahead = next(itersampl)
        except StopIteration:
            break

        # set flag which is needed for the last entry
        flag = False

        # hpb
        if isinstance(res, TypeTolerance):
            hpb = pivot.precurmass / res.tolerance
        else:
            hpb = pivot.precurmass / res

        while lookahead.precurmass <= pivot.precurmass + hpb:
            flag = True
            precurmasslist.append(deepcopy(lookahead))
            # pivot = deepcopy(lookahead)
            try:
                lookahead = next(itersampl)
            except StopIteration:
                break

        pivot = deepcopy(lookahead)

        # calc average mass with the intensity as weight

        # get max intensity
        maxint = 0
        for i in precurmasslist:
            if i.intensity > maxint:
                maxint = i.intensity

        # get intensity weights and the sum of all precursmass's
        sumcount = 0
        sumprecurmass = 0
        if maxint != 0:
            for i in precurmasslist:
                i.precurmass = (i.intensity / maxint) * i.precurmass
                sumprecurmass = sumprecurmass + i.precurmass
                sumcount = sumcount + (i.intensity / maxint)
        else:
            # if an intensity is zero, just take the average of the precurmasses
            for i in precurmasslist:
                sumprecurmass += i.precurmass
                sumcount += 1

        # get intensity weights and the sum of all precursmass's
        sumcountScan = 0
        for i in precurmasslist:
            sumcountScan += i.scanCount
        countScan = sumcountScan / len(precurmasslist)

        # get sum intensity
        sumintensity = 0
        for i in precurmasslist:
            sumintensity = sumintensity + i.intensity

        avgprecurmass = sumprecurmass / sumcount

        newsample.add_MSMass(
            MSMass(
                precurmass=avgprecurmass,
                intensity=sumintensity,
                smpl=sample.sampleName,
                polarity=precurmasslist[0].polarity,
                charge=None,
                fileName=None,
                scanCount=1,
                basePeakIntensity=pivot.basePeakIntensity,
            )
        )

    if not flag:
        newsample.listPrecurmass.append(sample.listPrecurmass[-1])

    return newsample


def lpdxClusterMSMS(sample, resolution):
    for i in range(len(sample.listMsms)):
        sample.listMsms[i] = doClusterMSMS(resolution, sample.listMsms[i])
