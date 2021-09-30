try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

"""
https://www.ibm.com/developerworks/community/blogs/jfp/entry/Python_Meets_Julia_Micro_Performance?lang=en
from functools import lru_cache as cache

@cache(maxsize=None)
def fib_cache(n):
"""

C = 12
H = 1.0078250321
N = 14.0030740052
P = 30.97376151
O = 15.9949146221
S = 31.97207069
NA = 22.98976967
D = 2.014101778
CI = 13.0033548378
CL = 34.968852
LI = 7.016003
NI = 15.0001088984
FL = 18.9984032
I = 126.904477
AG = 106.905095
AL = 26.981541
W = 183.950953
TI = 47.947947


@lru_cache(maxsize=None)
def calcsf(args):
    (
        lwBndC,
        upBndC,
        lwBndH,
        upBndH,
        lwBndO,
        upBndO,
        lwBndN,
        upBndN,
        lwBndP,
        upBndP,
        lwBndS,
        upBndS,
        lwBndNa,
        upBndNa,
        lwBndD,
        upBndD,
        lwBndCi,
        upBndCi,
        lwBndCl,
        upBndCl,
        lwBndLi,
        upBndLi,
        lwBndNi,
        upBndNi,
        lwBndF,
        upBndF,
        lwBndI,
        upBndI,
        lwBndAg,
        upBndAg,
        lwBndAl,
        upBndAl,
        lwBndW,
        upBndW,
        lwBndTi,
        upBndTi,
        mass,
        tolerance,
        dbLowerBound,
        dbUpperBound,
        charge,
    ) = args

    #      charge can only be between 0 and 1
    summand_charge = -0.00055 * charge

    upBndC += 1
    upBndH += 1
    upBndO += 1
    upBndP += 1
    upBndN += 1
    upBndS += 1
    upBndNa += 1
    upBndD += 1
    upBndCi += 1
    upBndCl += 1
    upBndLi += 1
    upBndNi += 1
    upBndF += 1
    upBndI += 1
    upBndAg += 1
    upBndAl += 1
    upBndW += 1
    upBndTi += 1

    Htimes2 = 2 * H

    jTi = lwBndTi
    TiBuf = jTi * TI

    listOutSeq = []
    mass_list = []
    dbr_list = []

    while jTi < upBndI:

        jW = lwBndW
        WBuf = jW * W

        while jW < upBndW:

            jAl = lwBndAl
            AlBuf = jAl * AL

            while jAl < upBndAl:

                jAg = lwBndAg
                AgBuf = jAg * AG

                while jAg < upBndAg:

                    jI = lwBndI
                    IBuf = jI * I

                    while jI < upBndI:

                        jF = lwBndF
                        FBuf = jF * FL

                        while jF < upBndF:

                            jCl = lwBndCl
                            ClBuf = jCl * CL

                            while jCl < upBndCl:

                                jLi = lwBndLi
                                LiBuf = jLi * LI

                                while jLi < upBndLi:

                                    jNi = lwBndNi
                                    NiBuf = jNi * NI

                                    while jNi < upBndNi:

                                        jCi = lwBndCi
                                        CiBuf = jCi * CI

                                        while jCi < upBndCi:

                                            jD = lwBndD
                                            DBuf = jD * D

                                            while jD < upBndD:

                                                jP = lwBndP
                                                PBuf = jP * P

                                                while jP < upBndP:

                                                    jS = lwBndS
                                                    SBuf = jS * S

                                                    while jS < upBndS:

                                                        jNa = lwBndNa
                                                        NaBuf = jNa * NA

                                                        while jNa < upBndNa:

                                                            jN = lwBndN
                                                            NBuf = jN * N

                                                            while jN < upBndN:

                                                                jO = lwBndO
                                                                OBuf = jO * O

                                                                while jO < upBndO:

                                                                    jC = lwBndC
                                                                    CBuf = jC * C

                                                                    while jC < upBndC:

                                                                        jH = lwBndH
                                                                        HBuf = jH * H

                                                                        while (
                                                                            jH <= upBndH
                                                                        ):

                                                                            # double bound equivalence
                                                                            cRDB = 2.0 + (
                                                                                (jC * 2)
                                                                                + (
                                                                                    jH
                                                                                    * -1
                                                                                )
                                                                                + (
                                                                                    jCl
                                                                                    * -1
                                                                                )
                                                                                + jN
                                                                                + (
                                                                                    jNa
                                                                                    * -1
                                                                                )
                                                                                + (jP)
                                                                                + (
                                                                                    jD
                                                                                    * -1
                                                                                )
                                                                                + (
                                                                                    jCi
                                                                                    * 2
                                                                                )
                                                                                + (jNi)
                                                                                + (
                                                                                    jLi
                                                                                    * -1
                                                                                )
                                                                                + (
                                                                                    jS
                                                                                    * 4
                                                                                )
                                                                                + (
                                                                                    jI
                                                                                    * 5
                                                                                )
                                                                                + (
                                                                                    jF
                                                                                    * 5
                                                                                )
                                                                            )
                                                                            cRDB = (
                                                                                cRDB
                                                                                / 2.0
                                                                            )

                                                                            if (
                                                                                dbLowerBound
                                                                                <= cRDB
                                                                            ) and (
                                                                                cRDB
                                                                                <= dbUpperBound
                                                                            ):

                                                                                # check if it is the right mass
                                                                                massSum = (
                                                                                    CBuf
                                                                                    + HBuf
                                                                                    + OBuf
                                                                                    + NBuf
                                                                                    + PBuf
                                                                                    + SBuf
                                                                                    + NaBuf
                                                                                    + DBuf
                                                                                    + CiBuf
                                                                                    + ClBuf
                                                                                    + LiBuf
                                                                                    + NiBuf
                                                                                    + FBuf
                                                                                    + IBuf
                                                                                    + summand_charge
                                                                                )
                                                                                if (
                                                                                    charge
                                                                                    != 0
                                                                                ):
                                                                                    m = (
                                                                                        (
                                                                                            abs(
                                                                                                charge
                                                                                            )
                                                                                        )
                                                                                        * mass
                                                                                    )
                                                                                    # tolerance = (abs(charge)) * (tolerance)
                                                                                else:
                                                                                    m = mass

                                                                                # printf("%4.4f\n", cRDB)
                                                                                # printf("jC: %d, jH: %d, jO: %d, jN: %d, jP: %d \n", jC, jH, jO, jN, jP)
                                                                                # printf("massSum: %4.4f m: %4.4f tolerance: %4.4f\n", massSum, m, tolerance)

                                                                                if (
                                                                                    massSum
                                                                                    >= m
                                                                                    - tolerance
                                                                                ):
                                                                                    if (
                                                                                        massSum
                                                                                        <= (
                                                                                            m
                                                                                            + tolerance
                                                                                        )
                                                                                    ):

                                                                                        #                                                                                         print(">>> m/z: {} theor.: {}".format( m, massSum))

                                                                                        # is only valid for charge == [-1, 0, 1]
                                                                                        # printf("massSum: %d, abs(charge) % 2: %d, jN % 2: %d\n", ((int)(abs(massSum)) % 2), (abs(charge) % 2), (jN % 2))
                                                                                        if (
                                                                                            (
                                                                                                (
                                                                                                    (
                                                                                                        (
                                                                                                            (
                                                                                                                int
                                                                                                            )(
                                                                                                                abs(
                                                                                                                    massSum
                                                                                                                )
                                                                                                            )
                                                                                                            % 2
                                                                                                        )
                                                                                                        == (
                                                                                                            (
                                                                                                                abs(
                                                                                                                    charge
                                                                                                                )
                                                                                                                % 2
                                                                                                            )
                                                                                                            + (
                                                                                                                jN
                                                                                                                % 2
                                                                                                            )
                                                                                                        )
                                                                                                        % 2
                                                                                                    )
                                                                                                )
                                                                                                and (
                                                                                                    (
                                                                                                        jH
                                                                                                        + jD
                                                                                                    )
                                                                                                    < 128
                                                                                                )
                                                                                            )
                                                                                            or (
                                                                                                (
                                                                                                    jH
                                                                                                    + jD
                                                                                                )
                                                                                                > 127
                                                                                            )
                                                                                            or (
                                                                                                (
                                                                                                    jD
                                                                                                    + jCi
                                                                                                    + jNi
                                                                                                )
                                                                                                > 0
                                                                                            )
                                                                                        ):  # /* || (jN == 0))*/{

                                                                                            # printf("\nreturn: %d count:%d", i, count)

                                                                                            # if (((jN % 2 != (int)(abs(massSum)) % 2) && abs(charge) % 2 == 1) ||
                                                                                            # ((jN % 2 != (int)(abs(massSum)) % 2) && abs(charge) % 2 == 0)){
                                                                                            #        (abs(charge) % 2 == 0)){
                                                                                            # fprintf(file, "HIT\n")
                                                                                            #
                                                                                            #                                                                                             print("HIT")

                                                                                            mass_list.append(
                                                                                                massSum
                                                                                            )
                                                                                            dbr_list.append(
                                                                                                cRDB
                                                                                            )

                                                                                            listOutSeq_inner = (
                                                                                                []
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jC
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jH
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jO
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jN
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jP
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jS
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jNa
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jD
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jCi
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jCl
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jLi
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jNi
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jF
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jI
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jAg
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jAl
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jW
                                                                                            )
                                                                                            listOutSeq_inner.append(
                                                                                                jTi
                                                                                            )

                                                                                            listOutSeq.append(
                                                                                                listOutSeq_inner
                                                                                            )

                                                                                            # printf("\nmass: %4.4f, cRDB %.1f, lowDB: %.1f, upDB: %.1f\n", massSum, cRDB, dbLowerBound, dbUpperBound)
                                                                            jH += 1
                                                                            HBuf += H
                                                                        jC += 1
                                                                        CBuf += C
                                                                    jO += 1
                                                                    OBuf += O
                                                                jN += 1
                                                                NBuf += N
                                                            jNa += 1
                                                            NaBuf += NA
                                                        jS += 1
                                                        SBuf += S
                                                    jP += 1
                                                    PBuf += P
                                                jD += 1
                                                DBuf += D
                                            jCi += 1
                                            CiBuf += CI
                                        jNi += 1
                                        NiBuf += NI
                                    jLi += 1
                                    LiBuf += LI
                                jCl += 1
                                ClBuf += CL
                            jF += 1
                            FBuf += FL
                        jI += 1
                        IBuf += I
                    jAg += 1
                    AgBuf += AG
                jAl += 1
                AlBuf += AL
            jW += 1
            WBuf += W
        jTi += 1
        TiBuf += TI

    return (mass_list, dbr_list, listOutSeq)
