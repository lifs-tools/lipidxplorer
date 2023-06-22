from lx.tools import unionSF
from lx.mfql.chemsc import calcSFbyMass
from lx.mfql.runtimeStatic import (
    TypeSFConstraint,
    TypeElementSequence,
    TypeFloat,
    TypeList,
    TypeTolerance,
)
from lx.exceptions import LipidXException
from lx.spectraContainer import MSMSEntry


class TypeScan:
    def __init__(self, mfqlObj, **argv):  # , listScans, mfqlObj, **argv):
        # 	self.listScans = listScans
        self.mfqlObj = mfqlObj

        self.scanTerm = None

        if "mark" in argv:
            tmp = argv["mark"]
            if isinstance(tmp, TypeObject):
                if tmp.elementSequence.isSFConstraint:
                    self.sfcontstraint = tmp.elementSequence
                else:
                    self.elementSequence = tmp.elementSequence
                    self.chemsc = tmp.elementSequence

                self.polarity = tmp.elementSequence.polarity
                self.mass = tmp.elementSequence.getWeight()

        self.massrange = None
        self.tolerance = None
        self.minocc = None
        self.maxocc = None
        self.options = {}

        # if argv.has_key('options'):
        # 	self.options = argv['options']
        #
        # 			for op in self.options:
        # 				if op[0] ==  'massrange':
        # 					self.massrange = op[1]
        # 				if op[0] == 'tolerance':
        # 					self.tolerance = op[1]
        # 				if op[0] == 'minocc':
        # 					self.minocc = op[1]
        # 				if op[0] == 'maxocc':
        # 					self.maxocc = op[1]

        if "name" in argv:
            self.name = argv["name"]
        else:
            self.name = None
        if "sfconstraint" in argv:
            self.sfconstraint = argv["sfconstraint"]
        else:
            self.sfconstraint = None
        if "scope" in argv:
            self.scope = argv["scope"]
        else:
            self.scope = None
        if "masterscan" in argv:
            self.masterscan = argv["masterscan"]
        else:
            self.masterscan = None
        if "expression" in argv:
            self.expression = argv["expression"]
        else:
            self.expression = None

        self.result = False  # any mass found?
        self.resultList = []  # if True -> the resulting list of marks

        self.scanResults = []

    def __cmp__(self, other):
        if isinstance(other, string):
            return self.cmp(self.name, other)
        else:
            return self.cmp(self, other)
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

    def evaluate(self):
        """OUT: list of TypeMark()"""

        listResult = []

        # the name for the precursor if no MS1 scan is given
        stdName = "prc"

        # generate empty mark
        positionPseudoMS = 10000
        self.mfqlObj.markIndex += 1

        positionMS = 0

        groups = []
        for mo in self.scanTerm:
            groups.append([])

        if self.mfqlObj.options["alignmentMethodMS"] == "calctol":
            newtol = max(
                (
                    (e.massWindow, e.peakMean)
                    for e in self.mfqlObj.sc.listSurveyEntry
                ),
                key=lambda item: item[0] * item[1],
            )
            # maybe =  self.mfqlObj.sc.options['calcSelectionWindow']
            ppm_tol = newtol[0] / (newtol[1] / 1_000_000)

        for se in self.mfqlObj.sc.listSurveyEntry:
            for indexM in range(len(self.scanTerm)):
                scanEntry = TypeScanEntry(se=se)
                takeScanEntry = False
                scanTermBool = True

                for m in self.scanTerm[indexM].list():
                    options = {}

                    boolPassStep = True

                    if not scanTermBool:
                        boolPassStep = False

                    if m.scope == "MS1+" or m.scope == "MS1-":
                        # check massrange
                        # if 'massrange' in mfqlObj.options:
                        if not self.mfqlObj.options.isEmpty("MSmassrange"):
                            options["massrange"] = self.mfqlObj.options[
                                "MSmassrange"
                            ]
                            if not (
                                self.mfqlObj.options["MSmassrange"][0]
                                <= se.precurmass
                                and se.precurmass
                                <= self.mfqlObj.options["MSmassrange"][1]
                            ):
                                boolPassStep = False

                        ## test for occupation threshold
                        # if not 'minocc' in options:
                        # 	if 'MSminOccupation' in self.mfqlObj.sc.optionalOptions:
                        # 		if se.occupation < self.mfqlObj.sc.optionalOptions['MSminOccupation']:
                        # 			boolPassStep = False
                        # else:
                        # 	if se.occupation < options['minocc'].float:
                        # 		boolPassStep = False

                        ## test for occupation threshold
                        # if 'maxocc' in options:
                        #
                        # 	if se.occupation > options['maxocc'].float:
                        # 		boolPassStep = False

                    if m.scope == "MS1+" or m.scope == "MS1-":
                        if not self.mfqlObj.options.isEmpty("MSminOccupation"):
                            options["minocc"] = self.mfqlObj.options[
                                "MSminOccupation"
                            ]

                        if (
                            self.mfqlObj.options["alignmentMethodMS"]
                            == "calctol"
                        ):  # is LX2
                            options["tolerance"] = TypeTolerance(
                                "ppm", ppm_tol
                            )

                        if not "tolerance" in options:
                            if not self.mfqlObj.options.isEmpty(
                                "optionalMStolerance"
                            ):
                                options["tolerance"] = self.mfqlObj.options[
                                    "optionalMStolerance"
                                ]  # make the 2* fattest cluster
                            else:
                                options["tolerance"] = self.mfqlObj.options[
                                    "MStolerance"
                                ]

                        if not options["tolerance"]:
                            raise LipidXException(
                                "The tolerance for MS is not given. No lipid detection possible."
                            )

                    elif m.scope == "MS2+" or m.scope == "MS2-":
                        if not self.mfqlObj.options.isEmpty("MSMSmassrange"):
                            options["massrange"] = self.mfqlObj.options[
                                "MSMSmassrange"
                            ]

                        if not self.mfqlObj.options.isEmpty(
                            "MSMSminOccupation"
                        ):
                            options["minocc"] = self.mfqlObj.options[
                                "MSMSminOccupation"
                            ]

                        if not "tolerance" in options:
                            if not self.mfqlObj.options.isEmpty(
                                "optionalMSMStolerance"
                            ):
                                options["tolerance"] = self.mfqlObj.options[
                                    "optionalMSMStolerance"
                                ]
                            else:
                                options["tolerance"] = self.mfqlObj.options[
                                    "MSMStolerance"
                                ]

                        if not options["tolerance"]:
                            raise LipidXException(
                                "The tolerance for MS/MS is not given. No lipid detection possible."
                            )

                    # if every 'if' fits, start the marking procedure
                    if boolPassStep:
                        ### searching in positive MS with sf-constraint
                        if (
                            m.scope == "MS1+" and se.polarity > 0
                        ):  # and isinstance(m, TypeSFConstraint):
                            if not m.name in list(scanEntry.dictMarks.keys()):
                                scanEntry.dictMarks[m.name] = []

                            # sf-constraint given
                            if isinstance(m, TypeSFConstraint):
                                scconst = m.elementSequence

                                if m.elementSequence:
                                    newChemsc = calcSFbyMass(
                                        se.precurmass,
                                        m.elementSequence,
                                        options["tolerance"],
                                    )

                                    # precursor mass found, adding to result list
                                    if newChemsc != []:
                                        se.listPrecurmassSF = unionSF(
                                            se.listPrecurmassSF,
                                            newChemsc,
                                            self.mfqlObj.queryName,
                                        )

                                        takeScanEntry = True
                                        scanEntry.scope = "MS1+"
                                        scanEntry.name = m.name
                                        scanEntry.encodedName = "%s:%d" % (
                                            m.name,
                                            int(se.precurmass),
                                        )

                                        for i in newChemsc:
                                            if not se.charge is None:
                                                errppm = (
                                                    -(
                                                        (
                                                            i.getWeight()
                                                            - se.precurmass
                                                        )
                                                        * 1000000
                                                    )
                                                    / se.precurmass
                                                ) * abs(se.charge)
                                                errda = -(
                                                    i.getWeight()
                                                    - se.precurmass
                                                ) * abs(se.charge)
                                            else:
                                                errppm = (
                                                    -(
                                                        (
                                                            i.getWeight()
                                                            - se.precurmass
                                                        )
                                                        * 1000000
                                                    )
                                                    / se.precurmass
                                                )
                                                errda = -(
                                                    i.getWeight()
                                                    - se.precurmass
                                                )

                                            if errppm != 0:
                                                errres = 1000000 / errppm
                                            else:
                                                errres = 1000000
                                            self.mfqlObj.markIndex += 1

                                            occ = self.mfqlObj.sc.getOccupation(
                                                se.dictIntensity,
                                                se.dictScans,
                                                threshold=self.mfqlObj.options[
                                                    "MSthreshold"
                                                ],
                                            )

                                            mark = TypeMark(
                                                type=0,
                                                se=se,
                                                msmse=None,
                                                name=m.name,
                                                isnl=None,
                                                encodedName="%s:%d"
                                                % (m.name, int(se.precurmass)),
                                                chemsc=i,
                                                scconst=scconst,
                                                scope="MS1+",
                                                precursor=None,
                                                options=options,
                                                isSFConstraint=True,
                                                expAccuraccy=options[
                                                    "tolerance"
                                                ],
                                                errppm=errppm,
                                                errda=errda,
                                                errres=errres,
                                                occ=occ,
                                                binsize=se.massWindow,
                                                charge=se.charge,
                                                mass=se.precurmass,
                                                frsc=None,
                                                frmass=None,
                                                nlsc=None,
                                                nlmass=None,
                                                markIndex=[
                                                    self.mfqlObj.markIndex
                                                ],
                                                positionMS=positionMS,
                                                positionMSMS=None,
                                            )

                                            notIn = True
                                            for i in se.listMark:
                                                if mark == i:
                                                    notIn = False

                                            if notIn:
                                                if not m.name in list(
                                                    scanEntry.dictMarks.keys()
                                                ):
                                                    scanEntry.dictMarks[
                                                        m.name
                                                    ] = []
                                                scanEntry.dictMarks[
                                                    m.name
                                                ].append(mark)
                                                se.listMark.append(mark)

                                else:
                                    takeScanEntry = True
                                    scanEntry.scope = "MS1+"
                                    scanEntry.name = m.name
                                    scanEntry.encodedName = "%s:%d" % (
                                        m.name,
                                        int(se.precurmass),
                                    )
                                    errda = None
                                    errppm = None
                                    errres = None
                                    self.mfqlObj.markIndex += 1
                                    occ = self.mfqlObj.sc.getOccupation(
                                        se.dictIntensity,
                                        se.dictScans,
                                        threshold=self.mfqlObj.options[
                                            "MSthreshold"
                                        ],
                                    )
                                    mark = TypeMark(
                                        type=0,
                                        se=se,
                                        msmse=None,
                                        name=m.name,
                                        isnl=None,
                                        encodedName="%s:%d"
                                        % (m.name, int(se.precurmass)),
                                        chemsc=None,
                                        scconst=scconst,
                                        scope="MS1+",
                                        precursor=None,
                                        options=options,
                                        isSFConstraint=False,
                                        expAccuraccy=options["tolerance"],
                                        errppm=errppm,
                                        errda=errda,
                                        errres=errres,
                                        occ=se.occupation,
                                        binsize=se.massWindow,
                                        charge=se.charge,
                                        mass=se.precurmass,
                                        frsc=None,
                                        frmass=se.precurmass,
                                        nlsc=None,
                                        nlmass=None,
                                        markIndex=[self.mfqlObj.markIndex],
                                        positionMS=positionMS,
                                        positionMSMS=None,
                                    )

                                    notIn = True
                                    for i in se.listMark:
                                        if mark == i:
                                            notIn = False

                                    if notIn:
                                        if not m.name in list(
                                            scanEntry.dictMarks.keys()
                                        ):
                                            scanEntry.dictMarks[m.name] = []
                                        scanEntry.dictMarks[m.name].append(
                                            mark
                                        )
                                        se.listMark.append(mark)

                            elif isinstance(m, TypeElementSequence):
                                scconst = None

                                if options["tolerance"].fitIn(
                                    se.precurmass,
                                    m.elementSequence.getWeight(),
                                ):
                                    se.listPrecurmassSF = unionSF(
                                        se.listPrecurmassSF,
                                        [m.elementSequence],
                                        self.mfqlObj.queryName,
                                    )

                                    takeScanEntry = True
                                    scanEntry.scope = "MS1+"
                                    scanEntry.name = m.name
                                    scanEntry.encodedName = "%s:%d" % (
                                        m.name,
                                        int(se.precurmass),
                                    )

                                    if not se.charge is None:
                                        errppm = (
                                            -(
                                                (
                                                    m.elementSequence.getWeight()
                                                    - se.precurmass
                                                )
                                                * 1000000
                                            )
                                            / se.precurmass
                                        ) * abs(se.charge)
                                        errda = -(
                                            m.elementSequence.getWeight()
                                            - se.precurmass
                                        ) * abs(se.charge)
                                    else:
                                        errppm = (
                                            -(
                                                (
                                                    m.elementSequence.getWeight()
                                                    - se.precurmass
                                                )
                                                * 1000000
                                            )
                                            / se.precurmass
                                        )
                                        errda = -(
                                            m.elementSequence.getWeight()
                                            - se.precurmass
                                        )

                                    if errppm != 0:
                                        errres = 1000000 / errppm
                                    else:
                                        errres = 1000000
                                    self.mfqlObj.markIndex += 1
                                    occ = self.mfqlObj.sc.getOccupation(
                                        se.dictIntensity,
                                        se.dictScans,
                                        threshold=self.mfqlObj.options[
                                            "MSthreshold"
                                        ],
                                    )
                                    mark = TypeMark(
                                        type=0,
                                        se=se,
                                        msmse=None,
                                        name=m.name,
                                        isnl=None,
                                        encodedName="%s:%d"
                                        % (m.name, int(se.precurmass)),
                                        chemsc=m.elementSequence,
                                        scconst=None,
                                        scope="MS1+",
                                        precursor=None,
                                        options=options,
                                        isSFConstraint=False,
                                        expAccuraccy=options["tolerance"],
                                        errppm=errppm,
                                        errda=errda,
                                        errres=errres,
                                        occ=occ,
                                        binsize=se.massWindow,
                                        charge=se.charge,
                                        mass=se.precurmass,
                                        frsc=None,
                                        frmass=None,
                                        nlsc=None,
                                        nlmass=None,
                                        markIndex=[self.mfqlObj.markIndex],
                                        positionMS=positionMS,
                                        positionMSMS=None,
                                    )

                                    notIn = True
                                    for i in se.listMark:
                                        if mark == i:
                                            notIn = False

                                    if notIn:
                                        if not m.name in list(
                                            scanEntry.dictMarks.keys()
                                        ):
                                            scanEntry.dictMarks[m.name] = []
                                        scanEntry.dictMarks[m.name].append(
                                            mark
                                        )
                                        se.listMark.append(mark)

                            elif isinstance(m, TypeList):
                                for ml in m.listElementSequence:
                                    if options["tolerance"].fitIn(
                                        se.precurmass,
                                        ml.elementSequence.getWeight(),
                                    ):
                                        se.listPrecurmassSF = unionSF(
                                            se.listPrecurmassSF,
                                            [ml.elementSequence],
                                            self.mfqlObj.queryName,
                                        )

                                        takeScanEntry = True
                                        scanEntry.scope = "MS1+"
                                        scanEntry.name = ml.name
                                        scanEntry.encodedName = "%s:%d" % (
                                            ml.name,
                                            int(se.precurmass),
                                        )

                                        if not se.charge is None:
                                            errppm = (
                                                -(
                                                    (
                                                        ml.elementSequence.getWeight()
                                                        - se.precurmass
                                                    )
                                                    * 1000000
                                                )
                                                / se.precurmass
                                            ) * abs(se.charge)
                                            errda = -(
                                                ml.elementSequence.getWeight()
                                                - se.precurmass
                                            ) * abs(se.charge)
                                        else:
                                            errppm = (
                                                -(
                                                    (
                                                        ml.elementSequence.getWeight()
                                                        - se.precurmass
                                                    )
                                                    * 1000000
                                                )
                                                / se.precurmass
                                            )
                                            errda = -(
                                                ml.elementSequence.getWeight()
                                                - se.precurmass
                                            )

                                        if errppm != 0:
                                            errres = 1000000 / errppm
                                        else:
                                            errres = 1000000
                                        self.mfqlObj.markIndex += 1
                                        occ = self.mfqlObj.sc.getOccupation(
                                            se.dictIntensity,
                                            se.dictScans,
                                            threshold=self.mfqlObj.options[
                                                "MSthreshold"
                                            ],
                                        )
                                        mark = TypeMark(
                                            type=0,
                                            se=se,
                                            msmse=None,
                                            name=ml.name,
                                            isnl=None,
                                            encodedName="%s:%d"
                                            % (ml.name, int(se.precurmass)),
                                            chemsc=ml.elementSequence,
                                            scconst=None,
                                            scope="MS1+",
                                            precursor=None,
                                            options=options,
                                            isSFConstraint=False,
                                            expAccuraccy=options["tolerance"],
                                            errppm=errppm,
                                            errda=errda,
                                            errres=errres,
                                            occ=occ,
                                            binsize=se.massWindow,
                                            charge=se.charge,
                                            mass=se.precurmass,
                                            frsc=None,
                                            frmass=None,
                                            nlsc=None,
                                            nlmass=None,
                                            markIndex=[self.mfqlObj.markIndex],
                                            positionMS=positionMS,
                                            positionMSMS=None,
                                        )

                                        notIn = True
                                        for i in se.listMark:
                                            if mark == i:
                                                notIn = False

                                        if notIn:
                                            if not ml.name in list(
                                                scanEntry.dictMarks.keys()
                                            ):
                                                scanEntry.dictMarks[
                                                    ml.name
                                                ] = []
                                            scanEntry.dictMarks[
                                                ml.name
                                            ].append(mark)
                                            se.listMark.append(mark)

                            else:
                                takeScanEntry = True
                                scanEntry.scope = "MS1+"
                                scanEntry.name = m.name
                                scanEntry.encodedName = "%s:%d" % (
                                    m.name,
                                    int(se.precurmass),
                                )
                                errda = None
                                errppm = None
                                errres = None
                                self.mfqlObj.markIndex += 1
                                occ = self.mfqlObj.sc.getOccupation(
                                    se.dictIntensity,
                                    se.dictScans,
                                    threshold=self.mfqlObj.options[
                                        "MSthreshold"
                                    ],
                                )
                                mark = TypeMark(
                                    type=0,
                                    se=se,
                                    msmse=None,
                                    name=m.name,
                                    isnl=None,
                                    encodedName="%s:%d"
                                    % (m.name, int(se.precurmass)),
                                    chemsc=None,
                                    scconst=scconst,
                                    scope="MS1+",
                                    precursor=None,
                                    options=options,
                                    isSFConstraint=False,
                                    expAccuraccy=options["tolerance"],
                                    errppm=errppm,
                                    errda=errda,
                                    errres=errres,
                                    occ=occ,
                                    binsize=se.massWindow,
                                    charge=se.charge,
                                    mass=se.precurmass,
                                    frsc=None,
                                    frmass=se.precurmass,
                                    nlsc=None,
                                    nlmass=None,
                                    markIndex=[self.mfqlObj.markIndex],
                                    positionMS=positionMS,
                                    positionMSMS=None,
                                )

                                notIn = True
                                for i in se.listMark:
                                    if mark == i:
                                        notIn = False

                                if notIn:
                                    if not m.name in list(
                                        scanEntry.dictMarks.keys()
                                    ):
                                        scanEntry.dictMarks[m.name] = []
                                    scanEntry.dictMarks[m.name].append(mark)
                                    se.listMark.append(mark)

                        ### searching in negative MS
                        elif (
                            m.scope == "MS1-" and se.polarity < 0
                        ):  # and isinstance(m, TypeSFConstraint):
                            if not m.name in list(scanEntry.dictMarks.keys()):
                                scanEntry.dictMarks[m.name] = []

                            # sf-constraint given
                            if isinstance(m, TypeSFConstraint):
                                scconst = m.elementSequence

                                if m.elementSequence:
                                    newChemsc = calcSFbyMass(
                                        se.precurmass,
                                        m.elementSequence,
                                        options["tolerance"],
                                    )

                                    # precursor mass found, adding to result list
                                    if newChemsc != []:
                                        se.listPrecurmassSF = unionSF(
                                            se.listPrecurmassSF,
                                            newChemsc,
                                            self.mfqlObj.queryName,
                                        )

                                        takeScanEntry = True
                                        scanEntry.scope = "MS1-"
                                        scanEntry.name = m.name
                                        scanEntry.encodedName = "%s:%d" % (
                                            m.name,
                                            int(se.precurmass),
                                        )

                                        for i in newChemsc:
                                            if not se.charge is None:
                                                errppm = (
                                                    -(
                                                        (
                                                            i.getWeight()
                                                            - se.precurmass
                                                        )
                                                        * 1000000
                                                    )
                                                    / se.precurmass
                                                ) * abs(se.charge)
                                                errda = -(
                                                    i.getWeight()
                                                    - se.precurmass
                                                ) * abs(se.charge)
                                            else:
                                                errppm = (
                                                    -(
                                                        (
                                                            i.getWeight()
                                                            - se.precurmass
                                                        )
                                                        * 1000000
                                                    )
                                                    / se.precurmass
                                                )
                                                errda = -(
                                                    i.getWeight()
                                                    - se.precurmass
                                                )

                                            if errppm != 0:
                                                errres = 1000000 / errppm
                                            else:
                                                errres = 1000000
                                            self.mfqlObj.markIndex += 1
                                            occ = self.mfqlObj.sc.getOccupation(
                                                se.dictIntensity,
                                                se.dictScans,
                                                threshold=self.mfqlObj.options[
                                                    "MSthreshold"
                                                ],
                                            )
                                            mark = TypeMark(
                                                type=0,
                                                se=se,
                                                msmse=None,
                                                name=m.name,
                                                isnl=None,
                                                encodedName="%s:%d"
                                                % (m.name, int(se.precurmass)),
                                                chemsc=i,
                                                scconst=scconst,
                                                scope="MS1-",
                                                precursor=None,
                                                options=options,
                                                isSFConstraint=True,
                                                expAccuraccy=options[
                                                    "tolerance"
                                                ],
                                                errppm=errppm,
                                                errda=errda,
                                                errres=errres,
                                                occ=occ,
                                                binsize=se.massWindow,
                                                charge=se.charge,
                                                mass=se.precurmass,
                                                frsc=None,
                                                frmass=None,
                                                nlsc=None,
                                                nlmass=None,
                                                markIndex=[
                                                    self.mfqlObj.markIndex
                                                ],
                                                positionMS=positionMS,
                                                positionMSMS=None,
                                            )

                                            notIn = True
                                            for i in se.listMark:
                                                if mark == i:
                                                    notIn = False

                                            if notIn:
                                                se.listMark.append(mark)
                                                if not m.name in list(
                                                    scanEntry.dictMarks.keys()
                                                ):
                                                    scanEntry.dictMarks[
                                                        m.name
                                                    ] = []
                                                scanEntry.dictMarks[
                                                    m.name
                                                ].append(mark)

                            elif isinstance(m, TypeElementSequence):
                                scconst = None

                                if options["tolerance"].fitIn(
                                    se.precurmass,
                                    m.elementSequence.getWeight(),
                                ):
                                    se.listPrecurmassSF = unionSF(
                                        se.listPrecurmassSF,
                                        [m.elementSequence],
                                        self.mfqlObj.queryName,
                                    )

                                    takeScanEntry = True
                                    scanEntry.scope = "MS1-"
                                    scanEntry.name = m.name
                                    scanEntry.encodedName = "%s:%d" % (
                                        m.name,
                                        int(se.precurmass),
                                    )

                                    if not se.charge is None:
                                        errppm = (
                                            -(
                                                (
                                                    m.elementSequence.getWeight()
                                                    - se.precurmass
                                                )
                                                * 1000000
                                            )
                                            / se.precurmass
                                        ) * abs(se.charge)
                                        errda = -(
                                            m.elementSequence.getWeight()
                                            - se.precurmass
                                        ) * abs(se.charge)
                                    else:
                                        errppm = (
                                            -(
                                                (
                                                    m.elementSequence.getWeight()
                                                    - se.precurmass
                                                )
                                                * 1000000
                                            )
                                            / se.precurmass
                                        )
                                        errda = -(
                                            m.elementSequence.getWeight()
                                            - se.precurmass
                                        )

                                    if errppm != 0:
                                        errres = 1000000 / errppm
                                    else:
                                        errres = 1000000
                                    self.mfqlObj.markIndex += 1
                                    occ = self.mfqlObj.sc.getOccupation(
                                        se.dictIntensity,
                                        se.dictScans,
                                        threshold=self.mfqlObj.options[
                                            "MSthreshold"
                                        ],
                                    )
                                    mark = TypeMark(
                                        type=0,
                                        se=se,
                                        msmse=None,
                                        name=m.name,
                                        isnl=None,
                                        encodedName="%s:%d"
                                        % (m.name, int(se.precurmass)),
                                        chemsc=m.elementSequence,
                                        scconst=None,
                                        scope="MS1-",
                                        precursor=None,
                                        options=options,
                                        isSFConstraint=False,
                                        expAccuraccy=options["tolerance"],
                                        errppm=errppm,
                                        errda=errda,
                                        errres=errres,
                                        occ=occ,
                                        binsize=se.massWindow,
                                        charge=se.charge,
                                        mass=se.precurmass,
                                        frsc=None,
                                        frmass=None,
                                        nlsc=None,
                                        nlmass=None,
                                        markIndex=[self.mfqlObj.markIndex],
                                        positionMS=positionMS,
                                        positionMSMS=None,
                                    )

                                    notIn = True
                                    for i in se.listMark:
                                        if mark == i:
                                            notIn = False

                                    if notIn:
                                        se.listMark.append(mark)
                                        if not m.name in list(
                                            scanEntry.dictMarks.keys()
                                        ):
                                            scanEntry.dictMarks[m.name] = []
                                        scanEntry.dictMarks[m.name].append(
                                            mark
                                        )

                            elif isinstance(m, TypeList):
                                for ml in m.listElementSequence:
                                    if options["tolerance"].fitIn(
                                        se.precurmass,
                                        ml.elementSequence.getWeight(),
                                    ):
                                        se.listPrecurmassSF = unionSF(
                                            se.listPrecurmassSF,
                                            [ml.elementSequence],
                                            self.mfqlObj.queryName,
                                        )

                                        takeScanEntry = True
                                        scanEntry.scope = "MS1-"
                                        scanEntry.name = ml.name
                                        scanEntry.encodedName = "%s:%d" % (
                                            ml.name,
                                            int(se.precurmass),
                                        )

                                        if not se.charge is None:
                                            errppm = (
                                                -(
                                                    (
                                                        ml.elementSequence.getWeight()
                                                        - se.precurmass
                                                    )
                                                    * 1000000
                                                )
                                                / se.precurmass
                                            ) * abs(se.charge)
                                            errda = -(
                                                ml.elementSequence.getWeight()
                                                - se.precurmass
                                            ) * abs(se.charge)
                                        else:
                                            errppm = (
                                                -(
                                                    (
                                                        ml.elementSequence.getWeight()
                                                        - se.precurmass
                                                    )
                                                    * 1000000
                                                )
                                                / se.precurmass
                                            )
                                            errda = -(
                                                ml.elementSequence.getWeight()
                                                - se.precurmass
                                            )

                                        if errppm != 0:
                                            errres = 1000000 / errppm
                                        else:
                                            errres = 1000000
                                        self.mfqlObj.markIndex += 1
                                        occ = self.mfqlObj.sc.getOccupation(
                                            se.dictIntensity,
                                            se.dictScans,
                                            threshold=self.mfqlObj.options[
                                                "MSthreshold"
                                            ],
                                        )
                                        mark = TypeMark(
                                            type=0,
                                            se=se,
                                            msmse=None,
                                            name=ml.name,
                                            isnl=None,
                                            encodedName="%s:%d"
                                            % (ml.name, int(se.precurmass)),
                                            chemsc=ml.elementSequence,
                                            scconst=None,
                                            scope="MS1-",
                                            precursor=None,
                                            options=options,
                                            isSFConstraint=False,
                                            expAccuraccy=options["tolerance"],
                                            errppm=errppm,
                                            errda=errda,
                                            errres=errres,
                                            occ=occ,
                                            binsize=se.massWindow,
                                            charge=se.charge,
                                            mass=se.precurmass,
                                            frsc=None,
                                            frmass=None,
                                            nlsc=None,
                                            nlmass=None,
                                            markIndex=[self.mfqlObj.markIndex],
                                            positionMS=positionMS,
                                            positionMSMS=None,
                                        )

                                        notIn = True
                                        for i in se.listMark:
                                            if mark == i:
                                                notIn = False

                                        if notIn:
                                            se.listMark.append(mark)
                                            if not ml.name in list(
                                                scanEntry.dictMarks.keys()
                                            ):
                                                scanEntry.dictMarks[
                                                    ml.name
                                                ] = []
                                            scanEntry.dictMarks[
                                                ml.name
                                            ].append(mark)

                            else:
                                takeScanEntry = True
                                scanEntry.scope = "MS1-"
                                scanEntry.name = m.name
                                scanEntry.encodedName = "%s:%d" % (
                                    m.name,
                                    int(se.precurmass),
                                )
                                errda = None
                                errppm = None
                                errres = None
                                self.mfqlObj.markIndex += 1
                                occ = self.mfqlObj.sc.getOccupation(
                                    se.dictIntensity,
                                    se.dictScans,
                                    threshold=self.mfqlObj.options[
                                        "MSthreshold"
                                    ],
                                )
                                mark = TypeMark(
                                    type=0,
                                    se=se,
                                    msmse=None,
                                    name=m.name,
                                    isnl=None,
                                    encodedName="%s:%d"
                                    % (m.name, int(se.precurmass)),
                                    chemsc=None,
                                    scconst=scconst,
                                    scope="MS1-",
                                    precursor=None,
                                    options=options,
                                    isSFConstraint=False,
                                    expAccuraccy=options["tolerance"],
                                    errppm=errppm,
                                    errda=errda,
                                    errres=errres,
                                    occ=occ,
                                    binsize=se.massWindow,
                                    charge=se.charge,
                                    mass=se.precurmass,
                                    frsc=None,
                                    frmass=se.precurmass,
                                    nlsc=None,
                                    nlmass=None,
                                    markIndex=[self.mfqlObj.markIndex],
                                    positionMS=positionMS,
                                    positionMSMS=None,
                                )

                                if True:  # not mark in se.listMark:
                                    se.listMark.append(mark)
                                    if not m.name in list(
                                        scanEntry.dictMarks.keys()
                                    ):
                                        scanEntry.dictMarks[m.name] = []
                                    scanEntry.dictMarks[m.name].append(mark)

                        ###############################################################################
                        # Searching in fragment spectra results often in more than one marks per      #
                        # sf-constraint. Furthermore, more than one different sum compositions for    #
                        # the precursor mass lead also to more than one sum composition for one       #
                        # mark. We take this into account by generating more than one mark. One for   #
                        # every single sum composition possible. I.e. for example 2 sum compositions  #
                        # for precursor mass lead to 2 sum compositions for the neutral loss          #
                        # of a fragment search (PIS). Check out the code to see, what else            #
                        # is generated.                                                               #
                        ###############################################################################

                        ### searching in positive MS/MS
                        # elif m.scope == "MS2+" and se.polarity > 0\
                        # 	and (not m.precursor or (scanEntry.dictMarks.has_key(m.precursor) and\
                        # 	scanEntry.dictMarks[m.precursor] != [])):

                        elif (
                            m.scope == "MS2+"
                            and se.polarity > 0
                            and se.listPrecurmassSF != []
                        ):
                            if not m.name in list(scanEntry.dictMarks.keys()):
                                scanEntry.dictMarks[m.name] = []

                            positionMSMS = 0

                            for msmse in se.listMSMS:
                                ### check for options ###
                                boolPassStep = True

                                # check massrange
                                if "massrange" in options:
                                    if not (
                                        options["massrange"][0] <= msmse.mass
                                        and msmse.mass
                                        <= options["massrange"][1]
                                    ):
                                        boolPassStep = False

                                if boolPassStep:
                                    isNL = False
                                    hasFR = False
                                    hasNL = False
                                    nlElementSequence = []
                                    frElementSequence = []

                                    # sf-constraint given
                                    if isinstance(m, TypeSFConstraint):
                                        scconst = m.elementSequence

                                        # prepare variables for marking by deciding for neutral loss or fragment search
                                        if m.elementSequence:
                                            # given ElementSequence is a Fragment
                                            if m.elementSequence.polarity > 0:
                                                mass = msmse.mass
                                            # given ElementSequence is a NeutralLoss
                                            elif (
                                                m.elementSequence.polarity == 0
                                            ):
                                                mass = (
                                                    se.precurmass - msmse.mass
                                                )
                                                isNL = True
                                            else:
                                                raise Scan_Exception(
                                                    "searching a negative "
                                                    + "fragment in a positive spectrum makes no sense."
                                                )

                                        newChemsc = calcSFbyMass(
                                            mass,
                                            m.elementSequence,
                                            options["tolerance"],
                                        )

                                        if newChemsc != []:
                                            # msmse.listChemsc += newChemsc

                                            # calculate other attributes for TypeMark
                                            if not isNL:
                                                frElementSequence = newChemsc
                                                if se.listPrecurmassSF != []:
                                                    hasNL = True
                                                    for (
                                                        i
                                                    ) in se.listPrecurmassSF:
                                                        for j in newChemsc:
                                                            nlElementSequence.append(
                                                                i - j
                                                            )
                                                else:
                                                    nlElementSequence = None

                                                nlmass = se.precurmass - mass

                                            else:
                                                nlElementSequence = newChemsc
                                                if se.listPrecurmassSF != []:
                                                    hasFR = True
                                                    for (
                                                        i
                                                    ) in se.listPrecurmassSF:
                                                        for j in newChemsc:
                                                            frElementSequence.append(
                                                                i - j
                                                            )
                                                else:
                                                    frElementSequence = None

                                                nlmass = mass

                                            takeScanEntry = True

                                            if isNL and hasFR:
                                                for nl in nlElementSequence:
                                                    for (
                                                        fr
                                                    ) in frElementSequence:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    fr.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            fr.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2+",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=nl,
                                                            scconst=scconst,
                                                            mass=mass,
                                                            frsc=fr,
                                                            frmass=msmse.mass,
                                                            nlsc=nl,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                            elif isNL and not hasFR:
                                                for nl in nlElementSequence:
                                                    errppm = (
                                                        -(
                                                            (
                                                                (
                                                                    se.precurmass
                                                                    - nl.getWeight()
                                                                )
                                                                - msmse.mass
                                                            )
                                                            * 1000000
                                                        )
                                                        / msmse.mass
                                                    )
                                                    errda = -(
                                                        (
                                                            se.precurmass
                                                            - nl.getWeight()
                                                        )
                                                        - msmse.mass
                                                    )
                                                    if errppm != 0:
                                                        errres = (
                                                            1000000 / errppm
                                                        )
                                                    else:
                                                        errres = 1000000

                                                    if m.precursor:
                                                        precursor = scanEntry.dictMarks[
                                                            m.precursor
                                                        ]
                                                    else:
                                                        precursor = None

                                                    occ = self.mfqlObj.sc.getOccupation(
                                                        msmse.dictIntensity,
                                                        {},
                                                        threshold=self.mfqlObj.options[
                                                            "MSMSthreshold"
                                                        ],
                                                    )
                                                    self.mfqlObj.markIndex += 1
                                                    mark = TypeMark(
                                                        type=1,
                                                        se=se,
                                                        msmse=msmse,
                                                        name=m.name,
                                                        isnl=isNL,
                                                        encodedName="%s:%d"
                                                        % (
                                                            m.name,
                                                            int(msmse.mass),
                                                        ),
                                                        scope="MS2+",
                                                        precursor=m.precursor,
                                                        options=options,
                                                        isSFConstraint=True,
                                                        expAccuraccy=options[
                                                            "tolerance"
                                                        ],
                                                        errppm=errppm,
                                                        errda=errda,
                                                        errres=errres,
                                                        occ=occ,
                                                        binsize=msmse.massWindow,
                                                        charge=msmse.charge,
                                                        chemsc=nl,
                                                        scconst=scconst,
                                                        mass=mass,
                                                        frsc=None,
                                                        frmass=msmse.mass,
                                                        nlsc=nl,
                                                        nlmass=nlmass,
                                                        markIndex=[
                                                            self.mfqlObj.markIndex
                                                        ],
                                                        positionMS=positionMS,
                                                        positionMSMS=positionMSMS,
                                                    )

                                                    notIn = True
                                                    for i in msmse.listMark:
                                                        if mark == i:
                                                            if i.mergeMSMSMarks(
                                                                mark
                                                            ):
                                                                notIn = False

                                                    if notIn:
                                                        msmse.listMark.append(
                                                            mark
                                                        )
                                                    if (
                                                        True
                                                    ):  # not mark in scanEntry.dictMarks[m.name]:
                                                        scanEntry.dictMarks[
                                                            m.name
                                                        ].append(mark)

                                            elif not isNL and hasNL:
                                                for nl in nlElementSequence:
                                                    for fr in newChemsc:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    fr.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            fr.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2+",
                                                            precursor=precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=fr,
                                                            scconst=scconst,
                                                            mass=mass,
                                                            frsc=fr,
                                                            frmass=msmse.mass,
                                                            nlsc=nl,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                                pass

                                            elif not isNL and not hasNL:
                                                for fr in newChemsc:
                                                    errppm = (
                                                        -(
                                                            (
                                                                fr.getWeight()
                                                                - msmse.mass
                                                            )
                                                            * 1000000
                                                        )
                                                        / msmse.mass
                                                    )
                                                    errda = -(
                                                        fr.getWeight()
                                                        - msmse.mass
                                                    )
                                                    if errppm != 0:
                                                        errres = (
                                                            1000000 / errppm
                                                        )
                                                    else:
                                                        errres = 1000000

                                                    if m.precursor:
                                                        precursor = scanEntry.dictMarks[
                                                            m.precursor
                                                        ]
                                                    else:
                                                        precursor = None

                                                    occ = self.mfqlObj.sc.getOccupation(
                                                        msmse.dictIntensity,
                                                        {},
                                                        threshold=self.mfqlObj.options[
                                                            "MSMSthreshold"
                                                        ],
                                                    )
                                                    self.mfqlObj.markIndex += 1
                                                    mark = TypeMark(
                                                        type=1,
                                                        se=se,
                                                        msmse=msmse,
                                                        name=m.name,
                                                        isnl=isNL,
                                                        encodedName="%s:%d"
                                                        % (
                                                            m.name,
                                                            int(msmse.mass),
                                                        ),
                                                        scope="MS2+",
                                                        precursor=precursor,
                                                        options=options,
                                                        isSFConstraint=True,
                                                        expAccuraccy=options[
                                                            "tolerance"
                                                        ],
                                                        errppm=errppm,
                                                        errda=errda,
                                                        errres=errres,
                                                        occ=occ,
                                                        binsize=msmse.massWindow,
                                                        charge=msmse.charge,
                                                        chemsc=fr,
                                                        scconst=scconst,
                                                        mass=mass,
                                                        frsc=fr,
                                                        frmass=msmse.mass,
                                                        nlsc=None,
                                                        nlmass=nlmass,
                                                        markIndex=[
                                                            self.mfqlObj.markIndex
                                                        ],
                                                        positionMS=positionMS,
                                                        positionMSMS=positionMSMS,
                                                    )

                                                    notIn = True
                                                    for i in msmse.listMark:
                                                        if mark == i:
                                                            if i.mergeMSMSMarks(
                                                                mark
                                                            ):
                                                                notIn = False

                                                    if notIn:
                                                        msmse.listMark.append(
                                                            mark
                                                        )
                                                    if (
                                                        True
                                                    ):  # not mark in scanEntry.dictMarks[m.name]:
                                                        scanEntry.dictMarks[
                                                            m.name
                                                        ].append(mark)

                                            # if no precursor scan given
                                            if not scanEntry.encodedName:
                                                scanEntry.encodedName = (
                                                    stdName
                                                    + ":%d"
                                                    % int(se.precurmass)
                                                )

                                            curStatBool = True

                                    # chemical sum composition given
                                    elif isinstance(m, TypeElementSequence):
                                        scconst = None

                                        # given ElementSequence is a Fragment
                                        if m.elementSequence.polarity > 0:
                                            mass = msmse.mass
                                        # given ElementSequence is a NeutralLoss
                                        elif m.elementSequence.polarity == 0:
                                            mass = se.precurmass - msmse.mass
                                            isNL = True
                                        else:
                                            raise Scan_Exception(
                                                "searching a negative "
                                                + "fragment in a positive spectrum makes no sense."
                                            )

                                        fits = False
                                        if isNL:
                                            fits = options[
                                                "tolerance"
                                            ].fitInNL(
                                                mass,
                                                m.elementSequence.getWeight(),
                                                msmse.mass,
                                            )
                                        else:
                                            fits = options["tolerance"].fitIn(
                                                mass,
                                                m.elementSequence.getWeight(),
                                            )

                                        if fits:
                                            newNLChemsc = []
                                            newFRChemsc = []

                                            if not isNL:
                                                newFRChemsc = [
                                                    m.elementSequence
                                                ]
                                                if se.listPrecurmassSF != []:
                                                    for i in se.listMark:
                                                        if (
                                                            i.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                            == m.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                        ):
                                                            newNLChemsc.append(
                                                                i.chemsc
                                                                - m.elementSequence
                                                            )

                                                else:
                                                    if (
                                                        self.mfqlObj.precursor
                                                        and isinstance(
                                                            self.mfqlObj.precursor,
                                                            TypeSFConstraint,
                                                        )
                                                    ):
                                                        newNLChemsc = calcSFbyMass(
                                                            se.precurmass
                                                            - mass,
                                                            self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                m.elementSequence
                                                            ),
                                                            options[
                                                                "tolerance"
                                                            ],
                                                        )
                                                    else:
                                                        newNLChemsc = []
                                                nlmass = se.precurmass - mass

                                            else:
                                                newNLChemsc = [
                                                    m.elementSequence
                                                ]
                                                if se.listPrecurmassSF != []:
                                                    for i in se.listMark:
                                                        if (
                                                            i.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                            == m.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                        ):
                                                            newFRChemsc.append(
                                                                i.chemsc
                                                                - m.elementSequence
                                                            )
                                                else:
                                                    if (
                                                        self.mfqlObj.precursor
                                                        and isinstance(
                                                            self.mfqlObj.precursor,
                                                            TypeSFConstraint,
                                                        )
                                                    ):
                                                        newFRChemsc = calcSFbyMass(
                                                            se.precurmass
                                                            - mass,
                                                            self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                m.elementSequence
                                                            ),
                                                            options[
                                                                "tolerance"
                                                            ],
                                                        )
                                                    else:
                                                        newFRChemsc = []

                                                nlmass = mass

                                            takeScanEntry = True

                                            if newFRChemsc != []:
                                                for i in newFRChemsc:
                                                    if newNLChemsc != []:
                                                        for n in newNLChemsc:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        i.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                i.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if m.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    m.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=m.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    m.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2+",
                                                                precursor=m.precursor,
                                                                options=options,
                                                                isSFConstraint=False,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=m.elementSequence,
                                                                scconst=scconst,
                                                                mass=mass,
                                                                frsc=i,
                                                                frmass=msmse.mass,
                                                                nlsc=n,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    if i.mergeMSMSMarks(
                                                                        mark
                                                                    ):
                                                                        notIn = False

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[m.name]:
                                                                scanEntry.dictMarks[
                                                                    m.name
                                                                ].append(
                                                                    mark
                                                                )

                                                    else:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    m.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            m.elementSequence.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2+",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=m.elementSequence,
                                                            scconst=scconst,
                                                            mass=mass,
                                                            frsc=i,
                                                            frmass=msmse.mass,
                                                            nlsc=None,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                            else:
                                                if newNLChemsc != []:
                                                    for n in newNLChemsc:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    (
                                                                        se.precurmass
                                                                        - n.getWeight()
                                                                    )
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            (
                                                                se.precurmass
                                                                - n.getWeight()
                                                            )
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2+",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=m.elementSequence,
                                                            scconst=None,
                                                            mass=mass,
                                                            frsc=m.elementSequence,
                                                            frmass=msmse.mass,
                                                            nlsc=n,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                                    # 	else:
                                                    # 		raise MyVariableException("Variable %s already defined" % m.name)

                                                ### TODO ###
                                                # The following else branch adds a mark, even if the precursor mass has no
                                                # no sum composition. To simplify things for now, I will switch it off,
                                                # since searches without precursor sf-constrainst are rare. But a solution
                                                # has to be found. The problem is, that LipidX does not allow a mark to
                                                # appear multiple times for one fragment mass.
                                                ###      ###
                                                elif False:
                                                    # else:

                                                    errppm = (
                                                        -(
                                                            (
                                                                m.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            * 1000000
                                                        )
                                                        / msmse.mass
                                                    )
                                                    errda = -(
                                                        m.elementSequence.getWeight()
                                                        - msmse.mass
                                                    )
                                                    if errppm != 0:
                                                        errres = (
                                                            1000000 / errppm
                                                        )
                                                    else:
                                                        errres = 1000000

                                                    if m.precursor:
                                                        precursor = scanEntry.dictMarks[
                                                            m.precursor
                                                        ]
                                                    else:
                                                        precursor = None

                                                    occ = self.mfqlObj.sc.getOccupation(
                                                        msmse.dictIntensity,
                                                        {},
                                                        threshold=self.mfqlObj.options[
                                                            "MSMSthreshold"
                                                        ],
                                                    )
                                                    self.mfqlObj.markIndex += 1
                                                    mark = TypeMark(
                                                        type=1,
                                                        se=se,
                                                        msmse=msmse,
                                                        name=m.name,
                                                        isnl=isNL,
                                                        encodedName="%s:%d"
                                                        % (
                                                            m.name,
                                                            int(msmse.mass),
                                                        ),
                                                        scope="MS2+",
                                                        options=options,
                                                        precursor=m.precursor,
                                                        isSFConstraint=True,
                                                        expAccuraccy=options[
                                                            "tolerance"
                                                        ],
                                                        errppm=errppm,
                                                        errda=errda,
                                                        errres=errres,
                                                        occ=occ,
                                                        binsize=msmse.massWindow,
                                                        charge=msmse.charge,
                                                        chemsc=m.elementSequence,
                                                        scconst=None,
                                                        mass=mass,
                                                        frsc=m.elementSequence,
                                                        frmass=msmse.mass,
                                                        nlsc=None,
                                                        nlmass=nlmass,
                                                        markIndex=[
                                                            self.mfqlObj.markIndex
                                                        ],
                                                        positionMS=positionMS,
                                                        positionMSMS=positionMSMS,
                                                    )

                                                    # else:
                                                    # 	raise MyVariableException("Variable %s already defined" % m.name)
                                                    notIn = True
                                                    for i in msmse.listMark:
                                                        if mark == i:
                                                            if i.mergeMSMSMarks(
                                                                mark
                                                            ):
                                                                notIn = False

                                                    if notIn:
                                                        msmse.listMark.append(
                                                            mark
                                                        )
                                                    if (
                                                        not mark
                                                        in scanEntry.dictMarks[
                                                            m.name
                                                        ]
                                                    ):
                                                        scanEntry.dictMarks[
                                                            m.name
                                                        ].append(mark)

                                            # if no precursor scan given
                                            if not scanEntry.encodedName:
                                                scanEntry.encodedName = (
                                                    stdName
                                                    + ":%d"
                                                    % int(se.precurmass)
                                                )

                                            curStatBool = True

                                    # list of chemical sum composition given
                                    elif isinstance(m, TypeList):
                                        for ml in m.listElementSequence:
                                            # prepare variables as above, but for lists
                                            if ml.elementSequence:
                                                # given ElementSequence is a Fragment
                                                if (
                                                    ml.elementSequence.polarity
                                                    > 0
                                                ):
                                                    mass = msmse.mass
                                                # given ElementSequence is a NeutralLoss
                                                elif (
                                                    ml.elementSequence.polarity
                                                    == 0
                                                ):
                                                    mass = (
                                                        se.precurmass
                                                        - msmse.mass
                                                    )
                                                    isNL = True
                                                else:
                                                    raise Scan_Exception(
                                                        "searching a negative "
                                                        + "fragment in a positive spectrum makes no sense."
                                                    )

                                            fits = False
                                            if isNL:
                                                fits = options[
                                                    "tolerance"
                                                ].fitInNL(
                                                    mass,
                                                    ml.elementSequence.getWeight(),
                                                    msmse.mass,
                                                )
                                            else:
                                                fits = options[
                                                    "tolerance"
                                                ].fitIn(
                                                    mass,
                                                    ml.elementSequence.getWeight(),
                                                )

                                            if fits:
                                                newNLChemsc = []
                                                newFRChemsc = []

                                                if not isNL:
                                                    newFRChemsc = [
                                                        ml.elementSequence
                                                    ]
                                                    if (
                                                        se.listPrecurmassSF
                                                        != []
                                                    ):
                                                        for i in se.listMark:
                                                            if (
                                                                i.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[0]
                                                                == m.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[
                                                                    0
                                                                ]
                                                            ):
                                                                newNLChemsc.append(
                                                                    i.chemsc
                                                                    - m.elementSequence
                                                                )
                                                    else:
                                                        if (
                                                            self.mfqlObj.precursor
                                                            and isinstance(
                                                                self.mfqlObj.precursor,
                                                                TypeSFConstraint,
                                                            )
                                                        ):
                                                            newNLChemsc = calcSFbyMass(
                                                                se.precurmass
                                                                - mass,
                                                                self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                    ml.elementSequence
                                                                ),
                                                                options[
                                                                    "tolerance"
                                                                ],
                                                            )
                                                        else:
                                                            newNLChemsc = []
                                                    nlmass = (
                                                        se.precurmass - mass
                                                    )

                                                else:
                                                    newNLChemsc = [
                                                        ml.elementSequence
                                                    ]
                                                    if (
                                                        se.listPrecurmassSF
                                                        != []
                                                    ):
                                                        for i in se.listMark:
                                                            if (
                                                                i.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[0]
                                                                == m.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[
                                                                    0
                                                                ]
                                                            ):
                                                                newFRChemsc.append(
                                                                    i.chemsc
                                                                    - m.elementSequence
                                                                )
                                                    else:
                                                        if (
                                                            self.mfqlObj.precursor
                                                            and isinstance(
                                                                self.mfqlObj.precursor,
                                                                TypeSFConstraint,
                                                            )
                                                        ):
                                                            newFRChemsc = calcSFbyMass(
                                                                se.precurmass
                                                                - mass,
                                                                self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                    ml.elementSequence
                                                                ),
                                                                options[
                                                                    "tolerance"
                                                                ],
                                                            )
                                                        else:
                                                            newFRChemsc = []

                                                    nlmass = mass

                                                takeScanEntry = True

                                                if newFRChemsc != []:
                                                    for i in newFRChemsc:
                                                        if newNLChemsc != []:
                                                            for (
                                                                n
                                                            ) in newNLChemsc:
                                                                errppm = (
                                                                    -(
                                                                        (
                                                                            ml.elementSequence.getWeight()
                                                                            - msmse.mass
                                                                        )
                                                                        * 1000000
                                                                    )
                                                                    / msmse.mass
                                                                )
                                                                errda = -(
                                                                    ml.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                if errppm != 0:
                                                                    errres = (
                                                                        1000000
                                                                        / errppm
                                                                    )
                                                                else:
                                                                    errres = (
                                                                        1000000
                                                                    )

                                                                if (
                                                                    ml.precursor
                                                                ):
                                                                    precursor = scanEntry.dictMarks[
                                                                        ml.precursor
                                                                    ]
                                                                else:
                                                                    precursor = (
                                                                        None
                                                                    )

                                                                occ = self.mfqlObj.sc.getOccupation(
                                                                    msmse.dictIntensity,
                                                                    {},
                                                                    threshold=self.mfqlObj.options[
                                                                        "MSMSthreshold"
                                                                    ],
                                                                )
                                                                self.mfqlObj.markIndex += (
                                                                    1
                                                                )
                                                                mark = TypeMark(
                                                                    type=1,
                                                                    se=se,
                                                                    msmse=msmse,
                                                                    name=ml.name,
                                                                    isnl=isNL,
                                                                    encodedName="%s:%d"
                                                                    % (
                                                                        ml.name,
                                                                        int(
                                                                            msmse.mass
                                                                        ),
                                                                    ),
                                                                    scope="MS2+",
                                                                    precursor=ml.precursor,
                                                                    options=options,
                                                                    isSFConstraint=False,
                                                                    expAccuraccy=options[
                                                                        "tolerance"
                                                                    ],
                                                                    errppm=errppm,
                                                                    errda=errda,
                                                                    errres=errres,
                                                                    occ=occ,
                                                                    binsize=msmse.massWindow,
                                                                    charge=msmse.charge,
                                                                    chemsc=ml.elementSequence,
                                                                    scconst=None,
                                                                    mass=mass,
                                                                    frsc=i,
                                                                    frmass=msmse.mass,
                                                                    nlsc=n,
                                                                    nlmass=nlmass,
                                                                    markIndex=[
                                                                        self.mfqlObj.markIndex
                                                                    ],
                                                                    positionMS=positionMS,
                                                                    positionMSMS=positionMSMS,
                                                                )

                                                                notIn = True
                                                                for (
                                                                    i
                                                                ) in (
                                                                    msmse.listMark
                                                                ):
                                                                    if (
                                                                        mark
                                                                        == i
                                                                    ):
                                                                        if i.mergeMSMSMarks(
                                                                            mark
                                                                        ):
                                                                            notIn = False

                                                                if notIn:
                                                                    msmse.listMark.append(
                                                                        mark
                                                                    )
                                                                if (
                                                                    True
                                                                ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                    scanEntry.dictMarks[
                                                                        ml.name
                                                                    ].append(
                                                                        mark
                                                                    )

                                                        else:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        ml.elementSequence.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                ml.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if ml.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    ml.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=ml.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    ml.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2+",
                                                                precursor=ml.precursor,
                                                                options=options,
                                                                isSFConstraint=False,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=ml.elementSequence,
                                                                scconst=None,
                                                                mass=mass,
                                                                frsc=i,
                                                                frmass=msmse.mass,
                                                                nlsc=None,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    if i.mergeMSMSMarks(
                                                                        mark
                                                                    ):
                                                                        notIn = False

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                scanEntry.dictMarks[
                                                                    ml.name
                                                                ].append(
                                                                    mark
                                                                )

                                                else:
                                                    if newNLChemsc != []:
                                                        for n in newNLChemsc:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        ml.elementSequence.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                ml.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if ml.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    ml.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=ml.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    ml.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2+",
                                                                precursor=ml.precursor,
                                                                options=options,
                                                                isSFConstraint=False,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=ml.elementSequence,
                                                                scconst=None,
                                                                mass=mass,
                                                                frsc=ml.elementSequence,
                                                                frmass=msmse.mass,
                                                                nlsc=n,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    if i.mergeMSMSMarks(
                                                                        mark
                                                                    ):
                                                                        notIn = False

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                scanEntry.dictMarks[
                                                                    ml.name
                                                                ].append(
                                                                    mark
                                                                )
                                                        # 	else:
                                                        # 		raise MyVariableException("Variable %s already defined" % ml.name)

                                                    else:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    ml.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            ml.elementSequence.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if ml.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                ml.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=ml.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                ml.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2+",
                                                            options=options,
                                                            precursor=ml.precursor,
                                                            isSFConstraint=False,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=ml.elementSequence,
                                                            scconst=None,
                                                            mass=mass,
                                                            frsc=ml.elementSequence,
                                                            frmass=msmse.mass,
                                                            nlsc=None,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        # else:
                                                        # 	raise MyVariableException("Variable %s already defined" % ml.name)
                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                            scanEntry.dictMarks[
                                                                ml.name
                                                            ].append(
                                                                mark
                                                            )

                                                # if no precursor scan given
                                                if not scanEntry.encodedName:
                                                    scanEntry.encodedName = (
                                                        stdName
                                                        + ":%d"
                                                        % int(se.precurmass)
                                                    )

                                                curStatBool = True

                                    # TypeFloat
                                    else:
                                        # given ElementSequence is a Fragment
                                        if m.polarity > 0:
                                            mass = msmse.mass
                                        # given ElementSequence is a NeutralLoss
                                        elif m.polarity == 0:
                                            mass = se.precurmass - msmse.mass
                                            isNL = True
                                        else:
                                            raise Scan_Exception(
                                                "searching a negative "
                                                + "fragment in a positive spectrum makes no sense."
                                            )

                                        fits = False
                                        if isNL:
                                            fits = options[
                                                "tolerance"
                                            ].fitInNL(
                                                mass, m.float, msmse.mass
                                            )
                                        else:
                                            fits = options["tolerance"].fitIn(
                                                mass, m.float
                                            )

                                        if fits:
                                            newNLChemsc = []
                                            newFRChemsc = []

                                            if not isNL:
                                                nlmass = se.precurmass - mass
                                            else:
                                                nlmass = mass

                                            takeScanEntry = True

                                            errppm = (
                                                -(
                                                    (m.float - msmse.mass)
                                                    * 1000000
                                                )
                                                / msmse.mass
                                            )
                                            errda = -(m.float - msmse.mass)
                                            if errppm != 0:
                                                errres = 1000000 / errppm
                                            else:
                                                errres = 1000000

                                            if m.precursor:
                                                precursor = (
                                                    scanEntry.dictMarks[
                                                        m.precursor
                                                    ]
                                                )
                                            else:
                                                precursor = None

                                            occ = self.mfqlObj.sc.getOccupation(
                                                msmse.dictIntensity,
                                                {},
                                                threshold=self.mfqlObj.options[
                                                    "MSMSthreshold"
                                                ],
                                            )
                                            self.mfqlObj.markIndex += 1
                                            mark = TypeMark(
                                                type=1,
                                                se=se,
                                                msmse=msmse,
                                                name=m.name,
                                                isnl=isNL,
                                                encodedName="%s:%d"
                                                % (m.name, int(msmse.mass)),
                                                scope="MS2+",
                                                precursor=m.precursor,
                                                options=options,
                                                isSFConstraint=False,
                                                expAccuraccy=options[
                                                    "tolerance"
                                                ],
                                                errppm=errppm,
                                                errda=errda,
                                                errres=errres,
                                                occ=occ,
                                                binsize=msmse.massWindow,
                                                charge=msmse.charge,
                                                chemsc=None,
                                                scconst=scconst,
                                                mass=mass,
                                                frsc=None,
                                                frmass=msmse.mass,
                                                nlsc=None,
                                                nlmass=nlmass,
                                                markIndex=[
                                                    self.mfqlObj.markIndex
                                                ],
                                                positionMS=positionMS,
                                                positionMSMS=positionMSMS,
                                            )

                                            for i in msmse.listMark:
                                                if mark == i:
                                                    if i.mergeMSMSMarks(mark):
                                                        notIn = False

                                            if (
                                                True
                                            ):  # not mark in scanEntry.dictMarks[m.name]:
                                                scanEntry.dictMarks[
                                                    m.name
                                                ].append(mark)

                                        positionMSMS += 1

                        ### search in negative MS/MS ###

                        # elif m.scope == "MS2-" and se.polarity < 0\
                        # 	and (not m.precursor or (scanEntry.dictMarks.has_key(m.precursor) and\
                        # 	scanEntry.dictMarks[m.precursor] != [])):

                        elif (
                            m.scope == "MS2-"
                            and se.polarity < 0
                            and se.listPrecurmassSF != []
                        ):
                            if not m.name in list(scanEntry.dictMarks.keys()):
                                scanEntry.dictMarks[m.name] = []

                            positionMSMS = 0

                            for msmse in se.listMSMS:
                                ### check for options ###
                                boolPassStep = True

                                # check massrange
                                if "massrange" in options:
                                    if not (
                                        options["massrange"][0] <= msmse.mass
                                        and msmse.mass
                                        <= options["massrange"][1]
                                    ):
                                        boolPassStep = False

                                if boolPassStep:
                                    isNL = False
                                    hasNL = False
                                    hasFR = False
                                    nlElementSequence = []
                                    frElementSequence = []

                                    # sf-constraint given
                                    if isinstance(m, TypeSFConstraint):
                                        scconst = m.elementSequence

                                        # prepare variables for marking by deciding for neutral loss or fragment search
                                        if m.elementSequence:
                                            # given ElementSequence is a Fragment
                                            if m.elementSequence.polarity < 0:
                                                mass = msmse.mass
                                            # given ElementSequence is a NeutralLoss
                                            elif (
                                                m.elementSequence.polarity == 0
                                            ):
                                                mass = (
                                                    se.precurmass - msmse.mass
                                                )
                                                isNL = True
                                            else:
                                                raise SyntaxErrorException(
                                                    "searching a negative "
                                                    + "fragment in a positive spectrum makes no sense."
                                                )

                                        newChemsc = calcSFbyMass(
                                            mass,
                                            m.elementSequence,
                                            options["tolerance"],
                                        )

                                        if newChemsc != []:
                                            # msmse.listChemsc += newChemsc

                                            # calculate other attributes for TypeMark
                                            if not isNL:
                                                frElementSequence = newChemsc
                                                if se.listPrecurmassSF != []:
                                                    hasNL = True
                                                    for (
                                                        i
                                                    ) in se.listPrecurmassSF:
                                                        for j in newChemsc:
                                                            nlElementSequence.append(
                                                                i - j
                                                            )
                                                else:
                                                    nlElementSequence = None

                                                nlmass = se.precurmass - mass

                                            else:
                                                nlElementSequence = newChemsc
                                                if se.listPrecurmassSF != []:
                                                    hasFR = True
                                                    for (
                                                        i
                                                    ) in se.listPrecurmassSF:
                                                        for j in newChemsc:
                                                            frElementSequence.append(
                                                                i - j
                                                            )
                                                else:
                                                    frElementSequence = None

                                                nlmass = mass

                                            takeScanEntry = True

                                            if isNL and hasFR:
                                                for nl in nlElementSequence:
                                                    for (
                                                        fr
                                                    ) in frElementSequence:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    (
                                                                        se.precurmass
                                                                        - nl.getWeight()
                                                                    )
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            (
                                                                se.precurmass
                                                                - nl.getWeight()
                                                            )
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2-",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=nl,
                                                            scconst=scconst,
                                                            mass=mass,
                                                            frsc=fr,
                                                            frmass=msmse.mass,
                                                            nlsc=nl,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                            elif isNL and not hasFR:
                                                for nl in nlElementSequence:
                                                    errppm = (
                                                        -(
                                                            (
                                                                (
                                                                    se.precurmass
                                                                    - nl.getWeight()
                                                                )
                                                                - msmse.mass
                                                            )
                                                            * 1000000
                                                        )
                                                        / msmse.mass
                                                    )
                                                    errda = -(
                                                        (
                                                            se.precurmass
                                                            - nl.getWeight()
                                                        )
                                                        - msmse.mass
                                                    )
                                                    if errppm != 0:
                                                        errres = (
                                                            1000000 / errppm
                                                        )
                                                    else:
                                                        errres = 1000000

                                                    if m.precursor:
                                                        precursor = scanEntry.dictMarks[
                                                            m.precursor
                                                        ]
                                                    else:
                                                        precursor = None

                                                    occ = self.mfqlObj.sc.getOccupation(
                                                        msmse.dictIntensity,
                                                        {},
                                                        threshold=self.mfqlObj.options[
                                                            "MSMSthreshold"
                                                        ],
                                                    )
                                                    self.mfqlObj.markIndex += 1
                                                    mark = TypeMark(
                                                        type=1,
                                                        se=se,
                                                        msmse=msmse,
                                                        name=m.name,
                                                        isnl=isNL,
                                                        encodedName="%s:%d"
                                                        % (
                                                            m.name,
                                                            int(msmse.mass),
                                                        ),
                                                        scope="MS2-",
                                                        precursor=m.precursor,
                                                        options=options,
                                                        isSFConstraint=True,
                                                        expAccuraccy=options[
                                                            "tolerance"
                                                        ],
                                                        errppm=errppm,
                                                        errda=errda,
                                                        errres=errres,
                                                        occ=occ,
                                                        binsize=msmse.massWindow,
                                                        charge=msmse.charge,
                                                        chemsc=nl,
                                                        scconst=scconst,
                                                        mass=mass,
                                                        frsc=None,
                                                        frmass=msmse.mass,
                                                        nlsc=nl,
                                                        nlmass=nlmass,
                                                        markIndex=[
                                                            self.mfqlObj.markIndex
                                                        ],
                                                        positionMS=positionMS,
                                                        positionMSMS=positionMSMS,
                                                    )

                                                    notIn = True
                                                    for i in msmse.listMark:
                                                        if mark == i:
                                                            if i.mergeMSMSMarks(
                                                                mark
                                                            ):
                                                                notIn = False

                                                    if notIn:
                                                        msmse.listMark.append(
                                                            mark
                                                        )
                                                    if (
                                                        True
                                                    ):  # not mark in scanEntry.dictMarks[m.name]:
                                                        scanEntry.dictMarks[
                                                            m.name
                                                        ].append(mark)

                                            elif not isNL and hasNL:
                                                for nl in nlElementSequence:
                                                    for fr in newChemsc:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    fr.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            fr.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2-",
                                                            precursor=precursor,
                                                            options=options,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=fr,
                                                            scconst=scconst,
                                                            mass=mass,
                                                            frsc=fr,
                                                            frmass=msmse.mass,
                                                            nlsc=nl,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )
                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[m.name]:
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                                pass

                                            elif not isNL and not hasNL:
                                                for fr in newChemsc:
                                                    errppm = (
                                                        -(
                                                            (
                                                                fr.getWeight()
                                                                - msmse.mass
                                                            )
                                                            * 1000000
                                                        )
                                                        / msmse.mass
                                                    )
                                                    errda = -(
                                                        fr.getWeight()
                                                        - msmse.mass
                                                    )
                                                    if errppm != 0:
                                                        errres = (
                                                            1000000 / errppm
                                                        )
                                                    else:
                                                        errres = 1000000

                                                    if m.precursor:
                                                        precursor = scanEntry.dictMarks[
                                                            m.precursor
                                                        ]
                                                    else:
                                                        precursor = None

                                                    occ = self.mfqlObj.sc.getOccupation(
                                                        msmse.dictIntensity,
                                                        {},
                                                        threshold=self.mfqlObj.options[
                                                            "MSMSthreshold"
                                                        ],
                                                    )
                                                    self.mfqlObj.markIndex += 1
                                                    mark = TypeMark(
                                                        type=1,
                                                        se=se,
                                                        msmse=msmse,
                                                        name=m.name,
                                                        isnl=isNL,
                                                        encodedName="%s:%d"
                                                        % (
                                                            m.name,
                                                            int(msmse.mass),
                                                        ),
                                                        scope="MS2-",
                                                        precursor=precursor,
                                                        options=options,
                                                        isSFConstraint=True,
                                                        expAccuraccy=options[
                                                            "tolerance"
                                                        ],
                                                        errppm=errppm,
                                                        errda=errda,
                                                        errres=errres,
                                                        occ=occ,
                                                        binsize=msmse.massWindow,
                                                        charge=msmse.charge,
                                                        chemsc=fr,
                                                        scconst=scconst,
                                                        mass=mass,
                                                        frsc=fr,
                                                        frmass=msmse.mass,
                                                        nlsc=None,
                                                        nlmass=nlmass,
                                                        markIndex=[
                                                            self.mfqlObj.markIndex
                                                        ],
                                                        positionMS=positionMS,
                                                        positionMSMS=positionMSMS,
                                                    )

                                                    notIn = True
                                                    for i in msmse.listMark:
                                                        if mark == i:
                                                            if i.mergeMSMSMarks(
                                                                mark
                                                            ):
                                                                notIn = False
                                                    if notIn:
                                                        msmse.listMark.append(
                                                            mark
                                                        )
                                                    if (
                                                        True
                                                    ):  # not mark in scanEntry.dictMarks[m.name]:
                                                        scanEntry.dictMarks[
                                                            m.name
                                                        ].append(mark)

                                            # if no precursor scan given
                                            if not scanEntry.encodedName:
                                                scanEntry.encodedName = (
                                                    stdName
                                                    + ":%d"
                                                    % int(se.precurmass)
                                                )

                                            curStatBool = True

                                    # chemical sum composition given
                                    elif isinstance(m, TypeElementSequence):
                                        scconst = None

                                        # given ElementSequence is a Fragment
                                        if m.elementSequence.polarity < 0:
                                            mass = msmse.mass
                                        # given ElementSequence is a NeutralLoss
                                        elif m.elementSequence.polarity == 0:
                                            mass = se.precurmass - msmse.mass
                                            isNL = True
                                        else:
                                            raise Scan_Exception(
                                                "searching a positive "
                                                + "fragment in a negative spectrum makes no sense."
                                            )

                                        fits = False
                                        if isNL:
                                            fits = options[
                                                "tolerance"
                                            ].fitInNL(
                                                mass,
                                                m.elementSequence.getWeight(),
                                                msmse.mass,
                                            )
                                        else:
                                            fits = options["tolerance"].fitIn(
                                                mass,
                                                m.elementSequence.getWeight(),
                                            )

                                        if fits:
                                            newNLChemsc = []
                                            newFRChemsc = []

                                            if not isNL:
                                                newFRChemsc = [
                                                    m.elementSequence
                                                ]
                                                if se.listPrecurmassSF != []:
                                                    for i in se.listMark:
                                                        if (
                                                            i.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                            == m.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                        ):
                                                            newNLChemsc.append(
                                                                i.chemsc
                                                                - m.elementSequence
                                                            )

                                                else:
                                                    if (
                                                        self.mfqlObj.precursor
                                                        and isinstance(
                                                            self.mfqlObj.precursor,
                                                            TypeSFConstraint,
                                                        )
                                                    ):
                                                        newNLChemsc = calcSFbyMass(
                                                            se.precurmass
                                                            - mass,
                                                            self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                m.elementSequence
                                                            ),
                                                            options[
                                                                "tolerance"
                                                            ],
                                                        )
                                                    else:
                                                        newNLChemsc = []
                                                nlmass = se.precurmass - mass

                                            else:
                                                newNLChemsc = [
                                                    m.elementSequence
                                                ]
                                                if se.listPrecurmassSF != []:
                                                    # carful here, this is actually no right, since only one
                                                    # precursor ion can be for the neutral loss of this particular
                                                    # fragment (of this particular species)
                                                    for i in se.listMark:
                                                        if (
                                                            i.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                            == m.name.split(
                                                                self.mfqlObj.namespaceConnector
                                                            )[0]
                                                        ):
                                                            newFRChemsc.append(
                                                                i.chemsc
                                                                - m.elementSequence
                                                            )
                                                else:
                                                    if (
                                                        self.mfqlObj.precursor
                                                        and isinstance(
                                                            self.mfqlObj.precursor,
                                                            TypeSFConstraint,
                                                        )
                                                    ):
                                                        newFRChemsc = calcSFbyMass(
                                                            se.precurmass
                                                            - mass,
                                                            self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                m.elementSequence
                                                            ),
                                                            options[
                                                                "tolerance"
                                                            ],
                                                        )
                                                    else:
                                                        newFRChemsc = []

                                                nlmass = mass

                                            takeScanEntry = True

                                            if newFRChemsc != []:
                                                for i in newFRChemsc:
                                                    if newNLChemsc != []:
                                                        for n in newNLChemsc:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        m.elementSequence.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                m.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if m.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    m.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=m.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    m.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2-",
                                                                precursor=m.precursor,
                                                                options=options,
                                                                isSFConstraint=False,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=m.elementSequence,
                                                                scconst=None,
                                                                mass=mass,
                                                                frsc=i,
                                                                frmass=msmse.mass,
                                                                nlsc=n,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    if i.mergeMSMSMarks(
                                                                        mark
                                                                    ):
                                                                        notIn = False

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )

                                                            # scanEntry is used to check if the boolean constrains hold
                                                            # from the IDENTIFY section, it than builds the basis vor the
                                                            # variables for SUCHTHAT and/or REPORT
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[m.name]:
                                                                scanEntry.dictMarks[
                                                                    m.name
                                                                ].append(
                                                                    mark
                                                                )

                                                    else:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    m.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            m.elementSequence.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2-",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=False,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=m.elementSequence,
                                                            scconst=None,
                                                            mass=mass,
                                                            frsc=i,
                                                            frmass=msmse.mass,
                                                            nlsc=None,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                            else:
                                                if newNLChemsc != []:
                                                    for n in newNLChemsc:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    m.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            m.elementSequence.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if m.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                m.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=m.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                m.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2-",
                                                            precursor=m.precursor,
                                                            options=options,
                                                            isSFConstraint=False,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=m.elementSequence,
                                                            scconst=None,
                                                            mass=mass,
                                                            frsc=None,
                                                            frmass=msmse.mass,
                                                            nlsc=n,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                if i.mergeMSMSMarks(
                                                                    mark
                                                                ):
                                                                    notIn = (
                                                                        False
                                                                    )

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                            scanEntry.dictMarks[
                                                                m.name
                                                            ].append(
                                                                mark
                                                            )

                                    # li#st of chemical sum composition given
                                    elif isinstance(m, TypeList):
                                        for ml in m.listElementSequence:
                                            # given ElementSequence is a Fragment
                                            if ml.elementSequence.charge < 0:
                                                mass = msmse.mass
                                            # given ElementSequence is a NeutralLoss
                                            elif (
                                                ml.elementSequence.charge == 0
                                            ):
                                                mass = (
                                                    se.precurmass - msmse.mass
                                                )
                                                isNL = True
                                            else:
                                                raise LipidXException(
                                                    "searching a positive "
                                                    + "fragment in a negative spectrum makes no sense."
                                                )

                                            fits = False
                                            if isNL:
                                                fits = options[
                                                    "tolerance"
                                                ].fitInNL(
                                                    mass,
                                                    ml.elementSequence.getWeight(),
                                                    msmse.mass,
                                                )
                                            else:
                                                fits = options[
                                                    "tolerance"
                                                ].fitIn(
                                                    mass,
                                                    ml.elementSequence.getWeight(),
                                                )

                                            if fits:
                                                newNLChemsc = []
                                                newFRChemsc = []

                                                if not isNL:
                                                    newFRChemsc = [
                                                        ml.elementSequence
                                                    ]
                                                    if (
                                                        se.listPrecurmassSF
                                                        != []
                                                    ):
                                                        for i in se.listMark:
                                                            if (
                                                                i.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[0]
                                                                == ml.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[
                                                                    0
                                                                ]
                                                            ):
                                                                newNLChemsc.append(
                                                                    i.chemsc
                                                                    - ml.elementSequence
                                                                )
                                                    else:
                                                        if (
                                                            self.mfqlObj.precursor
                                                            and isinstance(
                                                                self.mfqlObj.precursor,
                                                                TypeSFConstraint,
                                                            )
                                                        ):
                                                            newNLChemsc = calcSFbyMass(
                                                                se.precurmass
                                                                - mass,
                                                                self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                    ml.elementSequence
                                                                ),
                                                                options[
                                                                    "tolerance"
                                                                ],
                                                            )
                                                        else:
                                                            newNLChemsc = []
                                                    nlmass = (
                                                        se.precurmass - mass
                                                    )

                                                else:
                                                    newNLChemsc = [
                                                        ml.elementSequence
                                                    ]
                                                    if (
                                                        se.listPrecurmassSF
                                                        != []
                                                    ):
                                                        for i in se.listMark:
                                                            if (
                                                                i.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[0]
                                                                == ml.name.split(
                                                                    self.mfqlObj.namespaceConnector
                                                                )[
                                                                    0
                                                                ]
                                                            ):
                                                                newFRChemsc.append(
                                                                    i.chemsc
                                                                    - ml.elementSequence
                                                                )
                                                    else:
                                                        if (
                                                            self.mfqlObj.precursor
                                                            and isinstance(
                                                                self.mfqlObj.precursor,
                                                                TypeSFConstraint,
                                                            )
                                                        ):
                                                            newFRChemsc = calcSFbyMass(
                                                                se.precurmass
                                                                - mass,
                                                                self.mfqlObj.precursor.elementSequence.subWoRange(
                                                                    ml.elementSequence
                                                                ),
                                                                options[
                                                                    "tolerance"
                                                                ],
                                                            )
                                                        else:
                                                            newFRChemsc = []

                                                    nlmass = mass

                                                takeScanEntry = True

                                                if newFRChemsc != []:
                                                    for i in newFRChemsc:
                                                        if newNLChemsc != []:
                                                            for (
                                                                n
                                                            ) in newNLChemsc:
                                                                errppm = (
                                                                    -(
                                                                        (
                                                                            ml.elementSequence.getWeight()
                                                                            - msmse.mass
                                                                        )
                                                                        * 1000000
                                                                    )
                                                                    / msmse.mass
                                                                )
                                                                errda = -(
                                                                    ml.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                if errppm != 0:
                                                                    errres = (
                                                                        1000000
                                                                        / errppm
                                                                    )
                                                                else:
                                                                    errres = (
                                                                        1000000
                                                                    )

                                                                if (
                                                                    ml.precursor
                                                                ):
                                                                    precursor = scanEntry.dictMarks[
                                                                        ml.precursor
                                                                    ]
                                                                else:
                                                                    precursor = (
                                                                        None
                                                                    )

                                                                occ = self.mfqlObj.sc.getOccupation(
                                                                    msmse.dictIntensity,
                                                                    {},
                                                                    threshold=self.mfqlObj.options[
                                                                        "MSMSthreshold"
                                                                    ],
                                                                )
                                                                self.mfqlObj.markIndex += (
                                                                    1
                                                                )
                                                                mark = TypeMark(
                                                                    type=1,
                                                                    se=se,
                                                                    msmse=msmse,
                                                                    name=ml.name,
                                                                    isnl=isNL,
                                                                    encodedName="%s:%d"
                                                                    % (
                                                                        ml.name,
                                                                        int(
                                                                            msmse.mass
                                                                        ),
                                                                    ),
                                                                    scope="MS2-",
                                                                    precursor=ml.precursor,
                                                                    options=options,
                                                                    isSFConstraint=True,
                                                                    expAccuraccy=options[
                                                                        "tolerance"
                                                                    ],
                                                                    errppm=errppm,
                                                                    errda=errda,
                                                                    errres=errres,
                                                                    occ=occ,
                                                                    binsize=msmse.massWindow,
                                                                    charge=msmse.charge,
                                                                    chemsc=ml.elementSequence,
                                                                    scconst=None,
                                                                    mass=mass,
                                                                    frsc=i,
                                                                    frmass=msmse.mass,
                                                                    nlsc=n,
                                                                    nlmass=nlmass,
                                                                    markIndex=[
                                                                        self.mfqlObj.markIndex
                                                                    ],
                                                                    positionMS=positionMS,
                                                                    positionMSMS=positionMSMS,
                                                                )

                                                                notIn = True
                                                                for (
                                                                    i
                                                                ) in (
                                                                    msmse.listMark
                                                                ):
                                                                    if (
                                                                        mark
                                                                        == i
                                                                    ):
                                                                        notIn = False

                                                                if notIn:
                                                                    msmse.listMark.append(
                                                                        mark
                                                                    )
                                                                if (
                                                                    True
                                                                ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                    scanEntry.dictMarks[
                                                                        ml.name
                                                                    ].append(
                                                                        mark
                                                                    )

                                                        else:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        ml.elementSequence.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                ml.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if ml.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    ml.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=ml.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    ml.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2-",
                                                                precursor=ml.precursor,
                                                                options=options,
                                                                isSFConstraint=True,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=ml.elementSequence,
                                                                scconst=None,
                                                                mass=mass,
                                                                frsc=i,
                                                                frmass=msmse.mass,
                                                                nlsc=None,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    notIn = (
                                                                        False
                                                                    )

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                scanEntry.dictMarks[
                                                                    ml.name
                                                                ].append(
                                                                    mark
                                                                )

                                                else:
                                                    if newNLChemsc != []:
                                                        for n in newNLChemsc:
                                                            errppm = (
                                                                -(
                                                                    (
                                                                        ml.elementSequence.getWeight()
                                                                        - msmse.mass
                                                                    )
                                                                    * 1000000
                                                                )
                                                                / msmse.mass
                                                            )
                                                            errda = -(
                                                                ml.elementSequence.getWeight()
                                                                - msmse.mass
                                                            )
                                                            if errppm != 0:
                                                                errres = (
                                                                    1000000
                                                                    / errppm
                                                                )
                                                            else:
                                                                errres = (
                                                                    1000000
                                                                )

                                                            if ml.precursor:
                                                                precursor = scanEntry.dictMarks[
                                                                    ml.precursor
                                                                ]
                                                            else:
                                                                precursor = (
                                                                    None
                                                                )

                                                            occ = self.mfqlObj.sc.getOccupation(
                                                                msmse.dictIntensity,
                                                                {},
                                                                threshold=self.mfqlObj.options[
                                                                    "MSMSthreshold"
                                                                ],
                                                            )
                                                            self.mfqlObj.markIndex += (
                                                                1
                                                            )
                                                            mark = TypeMark(
                                                                type=1,
                                                                se=se,
                                                                msmse=msmse,
                                                                name=ml.name,
                                                                isnl=isNL,
                                                                encodedName="%s:%d"
                                                                % (
                                                                    ml.name,
                                                                    int(
                                                                        msmse.mass
                                                                    ),
                                                                ),
                                                                scope="MS2-",
                                                                precursor=ml.precursor,
                                                                options=options,
                                                                isSFConstraint=True,
                                                                expAccuraccy=options[
                                                                    "tolerance"
                                                                ],
                                                                errppm=errppm,
                                                                errda=errda,
                                                                errres=errres,
                                                                occ=occ,
                                                                binsize=msmse.massWindow,
                                                                charge=msmse.charge,
                                                                chemsc=ml.elementSequence,
                                                                scconst=None,
                                                                mass=mass,
                                                                frsc=ml.elementSequence,
                                                                frmass=msmse.mass,
                                                                nlsc=n,
                                                                nlmass=nlmass,
                                                                markIndex=[
                                                                    self.mfqlObj.markIndex
                                                                ],
                                                                positionMS=positionMS,
                                                                positionMSMS=positionMSMS,
                                                            )

                                                            notIn = True
                                                            for (
                                                                i
                                                            ) in (
                                                                msmse.listMark
                                                            ):
                                                                if mark == i:
                                                                    notIn = (
                                                                        False
                                                                    )

                                                            if notIn:
                                                                msmse.listMark.append(
                                                                    mark
                                                                )
                                                            if (
                                                                True
                                                            ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                                scanEntry.dictMarks[
                                                                    ml.name
                                                                ].append(
                                                                    mark
                                                                )
                                                        # 	else:
                                                        # 		raise MyVariableException("Variable %s already defined" % ml.name)

                                                    else:
                                                        errppm = (
                                                            -(
                                                                (
                                                                    ml.elementSequence.getWeight()
                                                                    - msmse.mass
                                                                )
                                                                * 1000000
                                                            )
                                                            / msmse.mass
                                                        )
                                                        errda = -(
                                                            ml.elementSequence.getWeight()
                                                            - msmse.mass
                                                        )
                                                        if errppm != 0:
                                                            errres = (
                                                                1000000
                                                                / errppm
                                                            )
                                                        else:
                                                            errres = 1000000

                                                        if ml.precursor:
                                                            precursor = scanEntry.dictMarks[
                                                                ml.precursor
                                                            ]
                                                        else:
                                                            precursor = None

                                                        occ = self.mfqlObj.sc.getOccupation(
                                                            msmse.dictIntensity,
                                                            {},
                                                            threshold=self.mfqlObj.options[
                                                                "MSMSthreshold"
                                                            ],
                                                        )
                                                        self.mfqlObj.markIndex += (
                                                            1
                                                        )
                                                        mark = TypeMark(
                                                            type=1,
                                                            se=se,
                                                            msmse=msmse,
                                                            name=ml.name,
                                                            isnl=isNL,
                                                            encodedName="%s:%d"
                                                            % (
                                                                ml.name,
                                                                int(
                                                                    msmse.mass
                                                                ),
                                                            ),
                                                            scope="MS2-",
                                                            options=options,
                                                            precursor=ml.precursor,
                                                            isSFConstraint=True,
                                                            expAccuraccy=options[
                                                                "tolerance"
                                                            ],
                                                            errppm=errppm,
                                                            errda=errda,
                                                            errres=errres,
                                                            occ=occ,
                                                            binsize=msmse.massWindow,
                                                            charge=msmse.charge,
                                                            chemsc=ml.elementSequence,
                                                            scconst=None,
                                                            mass=mass,
                                                            frsc=ml.elementSequence,
                                                            frmass=msmse.mass,
                                                            nlsc=None,
                                                            nlmass=nlmass,
                                                            markIndex=[
                                                                self.mfqlObj.markIndex
                                                            ],
                                                            positionMS=positionMS,
                                                            positionMSMS=positionMSMS,
                                                        )

                                                        # else:
                                                        # 	raise MyVariableException("Variable %s already defined" % ml.name)
                                                        notIn = True
                                                        for (
                                                            i
                                                        ) in msmse.listMark:
                                                            if mark == i:
                                                                notIn = False

                                                        if notIn:
                                                            msmse.listMark.append(
                                                                mark
                                                            )
                                                        if (
                                                            True
                                                        ):  # not mark in scanEntry.dictMarks[ml.name]:
                                                            scanEntry.dictMarks[
                                                                ml.name
                                                            ].append(
                                                                mark
                                                            )

                                                    # if no precursor scan given
                                                    if (
                                                        not scanEntry.encodedName
                                                    ):
                                                        scanEntry.encodedName = (
                                                            stdName
                                                            + ":%d"
                                                            % int(
                                                                se.precurmass
                                                            )
                                                        )

                                                    curStatBool = True
                                    # TypeFloat
                                    # elif isinstance(m, TypeFloat):
                                    else:
                                        raise SyntaxErrorException(
                                            "Please define your variable as chemical sum composition in"
                                            + " query %s."
                                            % self.mfqlObj.queryName,
                                            self.mfqlObj.filename,
                                            "",
                                            0,
                                        )

                dictVariables = {}
                scanTermList = []
                for i in self.scanTerm:
                    scanTermList.append(i.list())

                    ## count for a hash number
                    positionMS += 1

                if takeScanEntry:
                    if self.scanTerm[indexM].evaluate(scanEntry):
                        groups[indexM].append(scanEntry)

                # dbgstr  = "\n\n\n**************************************************************\n"
                # dbgstr += "\nQuery: %s" % self.mfqlObj.queryName
                # dbgstr += "\n"
                # dbgout(dbgstr)
                # for se in self.mfqlObj.sc.listSurveyEntry:
                # 	#if se.listMark != []:
                # 	#	dbgstr = "\n%s, %s" % (se.precurmass, se.listMark)
                # 	for msmse in se.listMSMS:
                # 		if msmse.listMark != []:
                # 			isPC = False
                # 			for mark in msmse.listMark:
                # 				if re.match(".*headPC.*", mark.name):
                # 					isPC = True
                # 			if isPC:
                # 				dbgstr += "\n%s" % msmse.listMark
                # 			#if len(msmse.listMark) == 1:
                # 	for mark in msmse.listMark:
                # 		dbgstr += "\n%s %s %s %s" % (mark.name, [x.precurmass for x in mark.se], mark.frsc, mark.nlsc)
                # 	#if se.listMark != []:
                # 		dbgout(dbgstr)

                try:
                    if takeScanEntry:
                        if self.scanTerm[indexM].evaluate(scanEntry):
                            se.listScanEntries.append(scanEntry)
                except AttributeError:
                    raise LipidXException(
                        "Your MasterScan is imported with an old version "
                        + "of LipidXplorer. Please import it again with this version."
                    )

        listResult = groups

        positionPseudoMS = 0
        dictVariables = {}

        scanTermList = []
        for i in self.scanTerm:
            scanTermList.append(i.list())

        self.mfqlObj.dictScanEntries[self.mfqlObj.queryName] = listResult

        return listResult


class TypeMark:
    def __init__(
        self,
        type,
        se,
        msmse,
        isnl,
        name,
        encodedName,
        scope,
        options,
        chemsc,
        scconst,
        mass,
        isSFConstraint,
        expAccuraccy,
        errppm,
        errda,
        errres,
        binsize,
        charge,
        occ,
        frsc,
        frmass,
        nlsc,
        nlmass,
        precursor,
        markIndex,
        positionMS,
        positionMSMS,
    ):
        self.type = type  # 0 - MS, 1 - MS/MS
        self.se = [se]  # the SurveyEntry with the precursor of the Mark
        self.msmse = msmse  # the MSMSEntry, if there is one
        self.name = name  # the marks name
        self.isnl = isnl  # True/False
        self.encodedName = encodedName  # long name
        self.scope = scope
        self.precursor = precursor  # depricated
        self.options = options  # options
        self.isSFConstraint = isSFConstraint  # is it an sc-constraint?
        self.expAccuraccy = (
            expAccuraccy  # is the 'expected' accuracy as given by the user
        )
        self.errppm = errppm  # error in ppm
        self.errda = errda  # error in da
        self.errres = errres  # error in resolution
        self.binsize = binsize  # the binsize referres to the massWindow of SurveyEntry and MSMSEntry
        self.charge = charge  # the ...
        self.occ = occ  # the occupation threshold
        self.chemsc = (
            chemsc  # chemical sum composition. Should always be there!
        )
        self.scconst = scconst  # the sc constraint
        self.mass = mass  # mass of the mark: mass of the fragment if fragment; mass of the given neutral loss else
        self.frsc = frsc  # is None, if one searched for nl, but the precursor mass had no sum composition
        self.isofrsc = (
            frsc  # this is needed as extra variable for isotopic correction
        )
        self.frmass = frmass  # the mass of the fragment
        self.nlsc = nlsc  # is None, if one searched for fr, but the precursor mass had no sum composition
        self.isonlsc = (
            nlsc  # this is needed as extra variable for isotopic correction
        )
        self.nlmass = nlmass  # precursor mass minus fragment mass
        self.markIndex = markIndex
        self.positionMS = positionMS
        self.positionMSMS = positionMSMS
        # self.isobaric = ' '
        self.isobaric = []

        self.isMultiple = False  # TODO

        # this is a very crappy style. The following attribute is just used for the MS/MS isotopic correction
        # where we put together several TypeMarks and store their names. Actually this should be an extra
        # object, but this would make it maybe more complicated and slower.
        self.listNames = []  # TODO

        # generate a hash tuple
        if self.chemsc:
            self.hash = (self.positionMS, self.positionMSMS, self.chemsc)
        elif self.frsc:
            self.hash = (self.positionMS, self.positionMSMS, self.frsc)
        elif self.nlsc:
            self.hash = (self.positionMS, self.positionMSMS, self.nlsc)
        else:
            self.hash = (self.positionMS, self.positionMSMS, None)

        # fill importatent variables
        if self.type == 0:
            self.float = se.precurmass
            self.intensity = se.dictIntensity
        elif self.type == 1:
            if not msmse is None:
                self.float = msmse.mass
                self.intensity = msmse.dictIntensity

    def __repr__(self):
        str = self.encodedName + ":" + self.scope
        return str

    def __cmp__(self, other):
        if isinstance(other, str):
            return self.cmp(self.encodedName.split(":")[0], other)

        if self.encodedName and other.encodedName:
            if self.encodedName == other.encodedName:
                if self.chemsc and other.chemsc:
                    return self.cmp(self.chemsc, other.chemsc)
                else:
                    return self.cmp(self.float, other.float)
            else:
                # return cmp(self.float, other.float)
                return self.cmp(self.encodedName, other.encodedName)

        elif self.name == other.name:
            if self.scope == other.scope:
                if self.se and other.se:
                    if self.se == other.se:
                        if self.msmse and other.msmse:
                            return self.cmp(self.msmse, other.msmse)
                        else:
                            return 0
                    elif self.msmse and other.msmse:
                        return self.cmp(self.msmse, other.msmse)
                    else:
                        return 0
                else:
                    return 0
            else:
                if self.scope == "MS1+" and other.scope == "MS1+":
                    return 0
                if self.scope == "MS2+" and other.scope == "MS2+":
                    return 0
                if self.scope == "MS1+" and other.scope == "MS2+":
                    return 1
                if self.scope == "MS2+" and other.scope == "MS1+":
                    return -1
        else:
            return self.cmp(self.name, other.name)
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

    def diff(self, other):
        """Shows the differences of two marks."""

        str = ""

        if self.se != other.se:
            str += "se: %s, %s \n" % (self.se, other.se)
        if self.msmse != other.msmse:
            str += "msmse: %s, %s\n" % (self.msmse, other.msmse)

        # if isnl is not the same for both marks, than they are different!
        if self.isnl != other.isnl:
            str += "isnl: %s, %s\n" % (self.isnl, other.isnl)
        if self.encodedName != other.encodedName:
            str += "encodedName: %s, %s" % (
                self.encodedName,
                other.encodedName,
            )
        if self.scope != other.scope:
            str += "scope: %s, %s\n" % (self.scope, other.scope)
        # this should never return Fals
        if self.options != other.options:
            str += "options: %s, %s\n" % (self.options, other.options)
        self.isSFConstraint = self.isSFConstraint or other.isSFConstraint
        if self.expAccuraccy != other.expAccuraccy:
            if self.expAccuraccy < other.expAccuraccy:
                self.expAccuraccy = other.expAccuraccy
        if self.errppm != other.errppm:
            str += "errppm: %f, %f\n" % (self.errppm, other.errppm)
        if self.errda != other.errda:
            str += "errda: %f, %f\n" % (self.errda, other.errda)
        if self.errres != other.errres:
            str += "errres: %f, %f\n" % (self.errres, other.errres)
        if self.chemsc != other.chemsc:
            str += "chemsc: %s, %s\n" % (self.chemsc, other.chemsc)
        if self.mass != other.mass:
            str += "mass: %f, %f\n" % (self.mass, other.mass)
        if not self.frsc:
            self.frsc = other.frsc
        if not self.frmass:
            self.frmass = other.frmass
        if not self.nlsc:
            self.nlsc = other.nlsc
        if not self.nlmass:
            self.nlmass = other.nlmass

        # self.isMultiple ???
        # self.listNames ???

        return str

    def mergeMSMSMarks(self, other):
        """Merge two marks. This is important for MS/MS marks, because it
        happens nlsc or frsc are None when a precursor mass has no sum
        composition but another precursor mass for the same mass has one.
        The function returns False, if the marks are different."""

        self.se += other.se
        if not self.msmse:
            self.msmse = other.msmse

        # if isnl is not the same for both marks, than they are different!
        if self.isnl != other.isnl:
            return False
        if self.encodedName != other.encodedName:
            return False
        if self.scope != other.scope:
            return False
        # this should never return False
        if self.options != other.options:
            return False
        self.isSFConstraint = self.isSFConstraint or other.isSFConstraint
        if self.expAccuraccy < other.expAccuraccy:
            self.expAccuraccy = other.expAccuraccy
        if self.errppm != other.errppm:
            return False
        if self.errda != other.errda:
            return False
        if self.errres != other.errres:
            return False
        if self.chemsc != other.chemsc:
            return False
        # if self.mass != other.mass: return False
        if not self.frsc:
            self.frsc = other.frsc
        if not self.frmass:
            self.frmass = other.frmass
        if not self.nlsc:
            self.nlsc = other.nlsc
        if not self.nlmass:
            self.nlmass = other.nlmass

        self.markIndex += other.markIndex
        # self.isMultiple ???
        # self.listNames ???

        return True

    def cmpMassPermutation(self, other):
        return cmp(self.float, other.float)

    def cmpSFPermutation(self, other):
        return cmp(self.chemsc, other.chemsc)

    def cmpMass(self, other):
        # if self.scope == "MS1+" and other.scope == "MS1+":
        # 	return abs(cmp(self.se.precurmass, self.se.precurmass) + cmp(self.chemsc, other.chemsc))
        # if self.scope == "MS2+" and other.scope == "MS2+":
        # 	return abs(cmp(int(self.msmse.mass), int(other.msmse.mass) + cmp(self.chemsc, other.chemsc)))
        if self.scope == "MS1+" and other.scope == "MS1+":
            return cmp(self.encodedName, other.encodedName)
        if self.scope == "MS2+" and other.scope == "MS2+":
            return cmp(self.encodedName, other.encodedName)

        if self.scope == "MS1+" and other.scope == "MS2+":
            return 1
        if self.scope == "MS2+" and other.scope == "MS1+":
            return -1

        if self.scope == "MS1-" and other.scope == "MS1-":
            return cmp(self.encodedName, other.encodedName)
        if self.scope == "MS2-" and other.scope == "MS2-":
            return cmp(self.encodedName, other.encodedName)

        if self.scope == "MS1-" and other.scope == "MS2-":
            return 1
        if self.scope == "MS2-" and other.scope == "MS1-":
            return -1

        # no scope if it is a mass not in IDENTIFIED
        if self.scope == "":
            return -1
        if other.scope == "":
            return 1

    def addName(self, name):
        self.listNames.append(name)


class TypeEmptyMark(TypeMark):
    def __init__(self, name, chemsc, isSFConstraint, mass, scconst):
        TypeMark.__init__(
            self,
            type=-1,
            se=None,
            msmse=None,
            name=name,
            isnl=None,
            encodedName="%s:%s" % (name, "***"),
            chemsc=chemsc,
            scconst=scconst,
            scope="***",
            precursor=None,
            options=None,
            isSFConstraint=isSFConstraint,
            expAccuraccy=None,  # options['tolerance'],
            errppm=None,
            errda=None,
            errres=None,
            occ=None,
            binsize=None,
            charge=0,
            mass=mass,
            frsc=chemsc,
            frmass=mass,
            nlsc=None,
            nlmass=None,
            markIndex=None,
            positionMS=None,
            positionMSMS=None,
        )


class TypeMarkTerm:
    def __init__(self, leftSide, rightSide, boolOp, mfqlObj):
        self.leftSide = leftSide
        self.rightSide = rightSide
        self.operator = boolOp
        self.mfqlObj = mfqlObj

        self.result = None
        self.noOfSymbols = 0

    def evaluate(self, res):
        leftResult = False
        rightResult = False

        if (
            isinstance(self.leftSide, TypeSFConstraint)
            or isinstance(self.leftSide, TypeElementSequence)
            or isinstance(self.leftSide, TypeFloat)
            or isinstance(self.leftSide, TypeList)
        ):
            if (
                self.leftSide.name in list(res.keys())
                and res[self.leftSide.name] != []
            ):
                leftResult = True

        elif isinstance(self.leftSide, TypeMarkTerm):
            leftResult = self.leftSide.evaluate(res)

        if (
            isinstance(self.rightSide, TypeSFConstraint)
            or isinstance(self.rightSide, TypeElementSequence)
            or isinstance(self.rightSide, TypeFloat)
            or isinstance(self.rightSide, TypeList)
        ):
            if (
                self.rightSide.name in list(res.keys())
                and res[self.rightSide.name] != []
            ):
                rightResult = True

        elif isinstance(self.rightSide, TypeMarkTerm):
            rightResult = self.rightSide.evaluate(res)

        if not rightResult:
            rightResult = False
        if not leftResult:
            leftResult = False

        if not self.operator:
            result = rightResult

        elif self.operator == "NOT":
            result = not rightResult

        elif self.operator == "AND":
            result = leftResult and rightResult

        elif self.operator == "OR":
            result = leftResult or rightResult

        elif self.operator == "=>":
            result = leftResult or (not leftResult and rightResult)

        elif self.operator == "<=":
            result = rightResult or (not rightResult and leftResult)

        elif self.operator == "<=>":
            result = leftResult and rightResult

        elif self.operator == "->":
            result = leftResult

        elif self.operator == "<-":
            result = rightResult

        else:
            raise LipidXException("Not a valid Boolean operator.")

        return result
        pass

    def __getitem__(self, item):
        for i in self.list():
            if i.name == item:
                return i

    def list(self):
        l = []
        if (
            isinstance(self.leftSide, TypeSFConstraint)
            or isinstance(self.leftSide, TypeElementSequence)
            or isinstance(self.leftSide, TypeFloat)
            or isinstance(self.leftSide, TypeList)
        ):
            l.append(self.leftSide)
        elif isinstance(self.leftSide, TypeMarkTerm):
            l += self.leftSide.list()

        if (
            isinstance(self.rightSide, TypeSFConstraint)
            or isinstance(self.rightSide, TypeElementSequence)
            or isinstance(self.rightSide, TypeFloat)
            or isinstance(self.rightSide, TypeList)
        ):
            l.append(self.rightSide)
        elif isinstance(self.rightSide, TypeMarkTerm):
            l += self.rightSide.list()

        return l

    def listBool(self):
        l = []
        if (
            isinstance(self.leftSide, TypeSFConstraint)
            or isinstance(self.leftSide, TypeElementSequence)
            or isinstance(self.leftSide, TypeFloat)
            or isinstance(self.leftSide, TypeList)
        ):
            l.append((self.leftSide, self.operator))
        elif isinstance(self.leftSide, TypeMarkTerm):
            l += self.leftSide.list()

        if (
            isinstance(self.rightSide, TypeSFConstraint)
            or isinstance(self.rightSide, TypeElementSequence)
            or isinstance(self.rightSide, TypeFloat)
            or isinstance(self.rightSide, TypeList)
        ):
            l.append((self.rightSide, self.operator))
        elif isinstance(self.rightSide, TypeMarkTerm):
            l += self.rightSide.list()

        return l

    def evaluateStepwise(self, res):
        list = self.listBool()

        return list


class TypeScanEntry:

    """scanEntry is used to check if the boolean constrains hold
    from the IDENTIFY section, it than builds the basis for the
    variables for SUCHTHAT and/or REPORT"""

    def __init__(self, se):
        self.se = se
        self.encodedName = None
        self.chemsc = None
        self.options = None
        self.scope = None
        self.name = None
        self.dictMarks = {}

    def __repr__(self):
        if self.encodedName:
            str = self.encodedName + " > "
        else:
            str = "* > "

        for i in list(self.dictMarks.keys()):
            for m in self.dictMarks[i]:
                str += " " + m.encodedName + "; "
        return str

    def __getitem__(self, item):
        if isinstance(item, int) or isinstance(item, slice):
            return list(self.dictMarks.values())[item]
        else:
            return self.dictMarks[item]

    def __len__(self):
        return len(list(self.dictMarks.keys())) + 1

    def has_key(self, item):
        return item in self.dictMarks

    def keys(self):
        return list(self.dictMarks.keys())
