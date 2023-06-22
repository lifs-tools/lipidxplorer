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


class specEntry:
    def __init__(self, mass=None, content={}, charge=None):
        self.mass = mass
        self.content = content
        self.charge = charge

    def __repr__(self):
        str = "{0:6}".format(self.mass)
        for k in list(self.content.keys()):
            str += " > {0:12}: {1:6}".format(k, self.content[k])
        return str

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
):
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
    secondStep = True
    numLoops = 3

    # initialize merging algorithm
    listResult = []
    for i in range(numLoops + 1):
        listResult.append([])

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

    for count in range(numLoops):
        current = 0

        if not current < (len(listResult[count]) - 1):
            listResult[-1] = listResult[count]
            break

        while current < (len(listResult[count]) - 1):
            # routine for collecting all masses which are in partialRes
            index = 1
            svIndex = 0
            sv = False
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
                    res = listResult[count][current][0] / tmp

            lastEntry = None

            while listResult[count][current + index][0] - bin[0][0] < res:
                bin.append(listResult[count][current + index])

                if (current + index) < (len(listResult[count]) - 1):
                    index += 1
                else:
                    break

            current += index

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

    ### gen output ###
    ##################

    return listOutput
