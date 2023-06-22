from lx.tools import op
from lx.exceptions import LipidXException, SyntaxErrorException
from lx.mfql.constants import *
from lx.debugger import Debug, DebugSet, DebugUnset, DebugMessage
from copy import deepcopy, copy
from fnmatch import fnmatch
from math import *


class TypeBooleanTerm:
    def __init__(
        self, sign, rightSide, leftSide, boolOp, mfqlObj, environment
    ):
        self.leftSide = leftSide
        self.rightSide = rightSide
        self.boolOp = boolOp
        self.sign = sign
        self.mfqlObj = mfqlObj
        self.environment = environment

    def evaluate(
        self, scane=None, mode=None, vars=None, queryName=None, sc=None
    ):
        # for log
        func = {"func": "BoolTrm.eval"}

        result = []

        if isinstance(self.rightSide, TypeExpr) and isinstance(
            self.leftSide, TypeExpr
        ):
            # log.debug(" * scanEntry: %s * ", scane, extra = func)

            leftResult = self.leftSide.evaluate(
                scane, mode="sc", vars=vars, queryName=queryName
            )
            rightResult = self.rightSide.evaluate(
                scane, mode="sc", vars=vars, queryName=queryName
            )

            # one of both is None (e.g. no mark found for this scane)
            if not leftResult or not rightResult:
                return None

            if self.boolOp == "AND":
                if leftResult != [] and rightResult != []:
                    result.append(vars)

            if self.boolOp == "OR":
                if leftResult != [] or rightResult != []:
                    result.append(vars)

        elif isinstance(self.rightSide, TypeBooleanTerm) and isinstance(
            self.leftSide, TypeBooleanTerm
        ):
            # initiate computation mode for evaluation
            self.mfqlObj.computationMode = "sc"

            leftResult = self.leftSide.evaluate(
                scane, mode="sc", vars=vars, queryName=queryName
            )
            rightResult = self.rightSide.evaluate(
                scane, mode="sc", vars=vars, queryName=queryName
            )

            # one of both is None (e.g. no mark found for this scane)
            if self.boolOp == "AND":
                if leftResult != [] and rightResult != []:
                    result.append(vars)

            if self.boolOp == "OR":
                if leftResult != [] or rightResult != []:
                    result.append(vars)

        elif (
            isinstance(self.rightSide, TypeExpr)
            or isinstance(self.rightSide, TypeBooleanTerm)
        ) and not self.leftSide:
            rightResult = self.rightSide.evaluate(
                scane, mode="sc", vars=vars, queryName=queryName
            )

            # log.debug("L: None", extra = func)
            # log.debug("R: %s", repr(rightResult), extra = func)

            # rightSide returned None (e.g. no mark found)
            ### negative term ###
            if self.sign == False:
                if not rightResult or rightResult == []:
                    result.append(vars)

            ### simple term ###
            else:
                if not (not rightResult or rightResult == []):
                    result.append(vars)

        elif isinstance(self.rightSide, TypeFunction) and not self.leftSide:
            result = self.rightSide.evaluate(
                scane, vars, self.environment, queryName=queryName
            )
            if isinstance(result, bool):
                if result:
                    return [vars]
                else:
                    return []
            else:
                return [vars]

        return result


class TypeExpr:
    def __init__(
        self, leftSide, rightSide, cmpOp, mfqlObj, options, environment
    ):
        self.leftSide = leftSide
        self.rightSide = rightSide
        self.cmpOp = cmpOp
        self.mfqlObj = mfqlObj
        self.options = {}
        self.environment = environment
        if options:
            for opt in options:
                self.options[opt[0]] = opt[1]

    def evaluate(
        self, scane=None, mode=None, vars=None, queryName=None, sc=None
    ):
        # for log
        func = {"func": "Expr.eval"}

        if isinstance(self.leftSide, TypeVariable):
            leftResult = TypeExpression(
                isSingleton=True,
                leftSide=self.leftSide,
                rightSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.leftSide, TypeElementSequence):
            leftResult = TypeExpression(
                isSingleton=True,
                leftSide=self.leftSide,
                rightSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.leftSide, TypeSFConstraint):
            leftResult = TypeExpression(
                isSingleton=True,
                leftSide=self.leftSide,
                rightSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.leftSide, TypeFloat):
            leftResult = TypeExpression(
                isSingleton=True,
                rightSide=None,
                leftSide=self.leftSide,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.leftSide, TypeFunction):
            leftResult = TypeExpression(
                isSingleton=True,
                rightSide=None,
                leftSide=self.leftSide,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        else:
            leftResult = self.leftSide.evaluate(scane, mode, vars, queryName)
            # leftResult = self.leftSide.evaluate()

        if isinstance(self.rightSide, TypeVariable):
            rightResult = TypeExpression(
                isSingleton=True,
                rightSide=self.rightSide,
                leftSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.rightSide, TypeElementSequence):
            rightResult = TypeExpression(
                isSingleton=True,
                rightSide=self.rightSide,
                leftSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.rightSide, TypeSFConstraint):
            rightResult = TypeExpression(
                isSingleton=True,
                rightSide=self.rightSide,
                leftSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.rightSide, TypeFloat):
            rightResult = TypeExpression(
                isSingleton=True,
                rightSide=self.rightSide,
                leftSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        elif isinstance(self.rightSide, TypeFunction):
            rightResult = TypeExpression(
                isSingleton=True,
                rightSide=self.rightSide,
                leftSide=None,
                operator=None,
                environment=self.environment,
                mfqlObj=self.mfqlObj,
            ).evaluate(scane, mode, vars, queryName)

        else:
            rightResult = self.rightSide.evaluate(scane, mode, vars, queryName)
            # rightResult = self.rightSide.evaluate()

        if rightResult and leftResult:
            result = []

            boolResult = False
            if self.cmpOp == "==":
                if leftResult.chemsc and rightResult.chemsc:
                    if leftResult.chemsc == rightResult.chemsc:
                        boolResult = True

                elif (leftResult.chemsc and rightResult.float) or (
                    leftResult.chemsc and rightResult.float == 0
                ):
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            leftResult.chemsc.getWeight(), rightResult.float
                        ):
                            boolResult = True
                    else:
                        if leftResult.chemsc.getWeight() == rightResult.float:
                            boolResult = True

                elif (leftResult.float and rightResult.chemsc) or (
                    leftResult.float == 0 and rightResult.chemsc
                ):
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            rightResult.chemsc.getWeight(), leftResult.float
                        ):
                            boolResult = True
                    else:
                        if rightSide.chemsc.getWeight() == leftResult.float:
                            boolResult = True

                elif (
                    (leftResult.float and rightResult.float)
                    or (leftResult.float and rightResult.float == 0)
                    or (leftResult.float == 0 and rightResult.float)
                    or (leftResult.float == 0 and rightResult.float == 0)
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(i, j):
                            boolResult = True
                    else:
                        if leftResult.float == rightResult.float:
                            boolResult = True

                elif (leftResult.dictIntensity and rightResult.float == 0) or (
                    leftResult.dictIntensity and rightResult.float == 0.0
                ):
                    boolResult = True
                    for key in list(leftResult.dictIntensity.keys()):
                        if (
                            float(leftResult.dictIntensity[key])
                            != rightResult.float
                        ):
                            boolResult = False

                elif (leftResult.float == 0 and rightResult.dictIntensity) or (
                    leftResult.float == 0.0 and rightResult.dictIntensity
                ):
                    boolResult = True
                    for key in list(rightResult.dictIntensity.keys()):
                        if (
                            float(rightResult.dictIntensity[key])
                            != leftResult.float
                        ):
                            boolResult = False

            # perform '>'
            if self.cmpOp == ">":
                if leftResult.chemsc and rightResult.chemsc:
                    if isinstance(
                        leftResult.chemsc, SCConstraint
                    ) and isinstance(rightResult.chemsc, ElementSequence):
                        boolResult = leftResult.chemsc.covers(
                            rightResult.chemsc
                        )

                    else:
                        boolResult = False
                        if (
                            leftResult.chemsc.getWeight()
                            > rightResult.chemsc.getWeight()
                        ):
                            boolResult = True

                elif (leftResult.chemsc and rightResult.float) or (
                    leftResult.chemsc and rightResult.float == 0
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                leftResult.chemsc.getWeight(),
                                rightResult.float,
                            ),
                            leftResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if leftResult.chemsc.getWeight() > rightResult.float:
                            boolResult = True

                elif (leftResult.float and rightResult.chemsc) or (
                    leftResult.float == 0 and rightResult.chemsc
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                rigthResult.chemsc.getWeight(),
                                leftResult.float,
                            ),
                            rightResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if rightResult.chemsc.getWeight() > leftResult.float:
                            boolResult = True

                elif (
                    (leftResult.float and rightResult.float)
                    or (leftResult.float and rightResult.float == 0)
                    or (leftResult.float == 0 and rightResult.float)
                    or (leftResult.float == 0 and rightResult.float == 0)
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(leftResult.float, rightResult.float),
                            leftResult.float,
                        ):
                            boolResult = True
                    else:
                        if leftResult.float > rightResult.float:
                            boolResult = True

                elif leftResult.dictIntensity and rightResult.dictIntensity:
                    boolResult = True
                    if leftResult.flag_dI_regExp or rightResult.flag_dI_regExp:
                        for lkey in leftResult.dictIntensity:
                            for rkey in rightResult.dictIntensity:
                                if (
                                    not leftResult.dictIntensity[lkey]
                                    > rightResult.dictIntensity[rkey]
                                ):
                                    boolResult = False
                    else:
                        for lkey in leftResult.dictIntensity:
                            if (
                                not leftResult.dictIntensity[lkey]
                                > rightResult.dictIntensity[lkey]
                            ):
                                boolResult = False
                                break

                elif (leftResult.float and rightResult.dictIntensity) or (
                    leftResult.float == 0 and rightResult.dictIntensity
                ):
                    boolResult = True
                    for rkey in rightResult.dictIntensity:
                        if (
                            not leftResult.float
                            > rightResult.dictIntensity[rkey]
                        ):
                            boolResult = False
                            break

                elif (leftResult.dictIntensity and rightResult.float) or (
                    leftResult.dictIntensity and rightResult.float == 0
                ):
                    boolResult = True
                    for lkey in leftResult.dictIntensity:
                        if (
                            not leftResult.dictIntensity[lkey]
                            > rightResult.float
                        ):
                            boolResult = False
                            break

            # perform '>='
            if self.cmpOp == ">=":
                if leftResult.chemsc and rightResult.chemsc:
                    if isinstance(
                        leftResult.chemsc, SCConstraint
                    ) and isinstance(rightResult.chemsc, ElementSequence):
                        boolResult = leftResult.chemsc.covers(
                            rightResult.chemsc
                        )
                    else:
                        boolResult = False
                        if (
                            leftResult.chemsc.getWeight()
                            >= rightResult.chemsc.getWeight()
                        ):
                            boolResult = True

                elif (leftResult.chemsc and rightResult.float) or (
                    leftResult.chemsc and rightResult.float == 0
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                leftResult.chemsc.getWeight(),
                                rightResult.float,
                            ),
                            leftResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if leftResult.chemsc.getWeight() >= rightResult.float:
                            boolResult = True

                elif (leftResult.float and rightResult.chemsc) or (
                    leftResult.float == 0 and rightResult.chemsc
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                rigthResult.chemsc.getWeight(),
                                leftResult.float,
                            ),
                            rightResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if rightResult.chemsc.getWeight() >= leftResult.float:
                            boolResult = True

                elif (
                    (leftResult.float and rightResult.float)
                    or (leftResult.float and rightResult.float == 0)
                    or (leftResult.float == 0 and rightResult.float)
                    or (leftResult.float == 0 and rightResult.float == 0)
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(leftResult.float, rightResult.float),
                            leftResult.float,
                        ):
                            boolResult = True
                    else:
                        if leftResult.float >= rightResult.float:
                            boolResult = True

                elif leftResult.dictIntensity and rightResult.dictIntensity:
                    boolResult = True
                    if leftResult.flag_dI_regExp or rightResult.flag_dI_regExp:
                        for lkey in leftResult.dictIntensity:
                            for rkey in rightResult.dictIntensity:
                                if (
                                    not leftResult.dictIntensity[lkey]
                                    >= rightResult.dictIntensity[rkey]
                                ):
                                    boolResult = False
                                    break
                    else:
                        for lkey in leftResult.dictIntensity:
                            if (
                                not leftResult.dictIntensity[lkey]
                                >= rightResult.dictIntensity[lkey]
                            ):
                                boolResult = False
                                break

                elif (leftResult.float and rightResult.dictIntensity) or (
                    leftResult.float == 0 and rightResult.dictIntensity
                ):
                    boolResult = True
                    for rkey in rightResult.dictIntensity:
                        if (
                            not leftResult.float
                            >= rightResult.dictIntensity[lkey]
                        ):
                            boolResult = False
                            break

                elif (leftResult.dictIntensity and rightResult.float) or (
                    leftResult.dictIntensity and rightResult.float == 0
                ):
                    boolResult = True
                    for lkey in leftResult.dictIntensity:
                        if (
                            not leftResult.dictIntensity[lkey]
                            >= rightResult.float
                        ):
                            boolResult = False
                            break

            # perform 'is contained in'
            if self.cmpOp == "<~":
                if leftResult.chemsc and rightResult.chemsc:
                    boolResult = False
                    if (
                        rightResult.type == TYPE_SC_CONSTRAINT
                        and leftResult.type == TYPE_CHEMSC
                    ):
                        boolResult = rightResult.chemsc.covers(
                            leftResult.chemsc
                        )

            if self.cmpOp == "~>":
                if leftResult.chemsc and rightResult.chemsc:
                    boolResult = False
                    if (
                        leftResult.type == TYPE_SC_CONSTRAINT
                        and rightResult.type == TYPE_CHEMSC
                    ):
                        boolResult = leftResult.chemsc.covers(
                            rightResult.chemsc
                        )

            # perform '<'
            if self.cmpOp == "<":
                if leftResult.chemsc and rightResult.chemsc:
                    if (
                        rightResult.type == TYPE_CHEMSC
                        and leftResult.type == TYPE_CHEMSC
                    ):
                        boolResult = False
                        if (
                            leftResult.chemsc.getWeight()
                            < rightResult.chemsc.getWeight()
                        ):
                            boolResult = True

                elif (leftResult.chemsc and rightResult.float) or (
                    leftResult.chemsc and rightResult.float == 0
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                leftResult.chemsc.getWeight(),
                                rightResult.float,
                            ),
                            rightResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if leftResult.chemsc.getWeight() < rightResult.float:
                            boolResult = True

                elif (leftResult.float and rightResult.chemsc) or (
                    leftResult.float == 0 and rightResult.chemsc
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                rigthResult.chemsc.getWeight(),
                                leftResult.float,
                            ),
                            leftResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if rightResult.chemsc.getWeight() < leftResult.float:
                            boolResult = True

                elif (
                    (leftResult.float and rightResult.float)
                    or (leftResult.float and rightResult.float == 0)
                    or (leftResult.float == 0 and rightResult.float)
                    or (leftResult.float == 0 and rightResult.float == 0)
                ):
                    boolResult = False

                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(leftResult.float, rightResult.float),
                            rightResult.float,
                        ):
                            boolResult = True
                    else:
                        if leftResult.float < rightResult.float:
                            boolResult = True

                elif leftResult.dictIntensity and rightResult.dictIntensity:
                    boolResult = True
                    if leftResult.flag_dI_regExp or rightResult.flag_dI_regExp:
                        for lkey in leftResult.dictIntensity:
                            for rkey in rightResult.dictIntensity:
                                if (
                                    not leftResult.dictIntensity[lkey]
                                    < rightResult.dictIntensity[rkey]
                                ):
                                    boolResult = False
                                    break
                    else:
                        for lkey in leftResult.dictIntensity:
                            if (
                                not leftResult.dictIntensity[lkey]
                                < rightResult.dictIntensity[lkey]
                            ):
                                boolResult = False
                                break

                elif (leftResult.float and rightResult.dictIntensity) or (
                    leftResult.float == 0 and rightResult.dictIntensity
                ):
                    boolResult = True
                    for rkey in rightResult.dictIntensity:
                        if (
                            not leftResult.float
                            < rightResult.dictIntensity[lkey]
                        ):
                            boolResult = False
                            break

                elif (leftResult.dictIntensity and rightResult.float) or (
                    leftResult.dictIntensity and rightResult.float == 0
                ):
                    boolResult = True
                    for lkey in leftResult.dictIntensity:
                        if (
                            not leftResult.dictIntensity[lkey]
                            < rightResult.float
                        ):
                            boolResult = False
                            break

            # perform '<='
            if self.cmpOp == "<=":
                if leftResult.chemsc and rightResult.chemsc:
                    if isinstance(
                        rightResult.chemsc, SCConstraint
                    ) and isinstance(leftResult.chemsc, ElementSequence):
                        boolResult = rightResult.chemsc.covers(
                            leftResult.chemsc
                        )
                    else:
                        boolResult = False
                        if (
                            leftResult.chemsc.getWeight()
                            <= rightResult.chemsc.getWeight()
                        ):
                            boolResult = True

                elif (leftResult.chemsc and rightResult.float) or (
                    leftResult.chemsc and rightResult.float == 0
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                leftResult.chemsc.getWeight(),
                                rightResult.float,
                            ),
                            rightResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if leftResult.chemsc.getWeight() <= rightResult.float:
                            boolResult = True

                elif (leftResult.float and rightResult.chemsc) or (
                    leftResult.float == 0 and rightResult.chemsc
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(
                                rigthResult.chemsc.getWeight(),
                                leftResult.float,
                            ),
                            leftResult.chemsc.getWeight(),
                        ):
                            boolResult = True
                    else:
                        if rightResult.chemsc.getWeight() <= leftResult.float:
                            boolResult = True

                elif (
                    (leftResult.float and rightResult.float)
                    or (leftResult.float and rightResult.float == 0)
                    or (leftResult.float == 0 and rightResult.float)
                    or (leftResult.float == 0 and rightResult.float == 0)
                ):
                    boolResult = False
                    if "tolerance" in self.options:
                        if self.options["tolerance"].fitIn(
                            max(leftResult.float, rightResult.float),
                            rightResult.float,
                        ):
                            boolResult = True
                    else:
                        if leftResult.float <= rightResult.float:
                            boolResult = True

                elif leftResult.dictIntensity and rightResult.dictIntensity:
                    boolResult = True
                    if leftResult.flag_dI_regExp or rightResult.flag_dI_regExp:
                        for lkey in leftResult.dictIntensity:
                            for rkey in rightResult.dictIntensity:
                                if (
                                    not leftResult.dictIntensity[lkey]
                                    <= rightResult.dictIntensity[rkey]
                                ):
                                    boolResult = False
                                    break
                    else:
                        for lkey in leftResult.dictIntensity:
                            if (
                                not leftResult.dictIntensity[lkey]
                                <= rightResult.dictIntensity[lkey]
                            ):
                                boolResult = False
                                break

                elif (leftResult.float and rightResult.dictIntensity) or (
                    leftResult.float == 0 and rightResult.dictIntensity
                ):
                    boolResult = True
                    for rkey in rightResult.dictIntensity:
                        if (
                            not leftResult.float
                            <= rightResult.dictIntensity[lkey]
                        ):
                            boolResult = False
                            break

                elif (leftResult.dictIntensity and rightResult.float) or (
                    leftResult.dictIntensity and rightResult.float == 0
                ):
                    boolResult = True
                    for lkey in leftResult.dictIntensity:
                        if (
                            not leftResult.dictIntensity[lkey]
                            <= rightResult.float
                        ):
                            boolResult = False
                            break

            if boolResult:
                result.append(vars)

        else:
            result = []

        return result

        pass


class TypeExpression:
    def __init__(
        self,
        leftSide,
        rightSide,
        operator,
        mfqlObj,
        environment,
        isSingleton=False,
        attribute=None,
        item=None,
    ):
        self.leftSide = leftSide
        self.rightSide = rightSide
        self.isSingleton = isSingleton
        self.operator = operator
        self.mfqlObj = mfqlObj
        self.environment = environment
        self.attribute = attribute
        self.item = item

        self.result = None
        self.noOfSymbols = 0

    def evaluate(
        self,
        scane=None,
        mode=None,
        vars=None,
        queryName=None,
        sc=None,
        varname="",
    ):
        vars = self.mfqlObj.currVars

        queryName = self.mfqlObj.queryName
        # queryName = self.mfqlObj.currQuery.name

        # for log
        func = {"func": "Exprssn.eval"}

        leftSide = None
        rightSide = None

        notFound = False

        ### left side ###

        # left side is a variable
        leftSide = []

        if isinstance(self.leftSide, TypeVariable):
            # add namespace
            namespacedVariable = (
                queryName
                + self.mfqlObj.namespaceConnector
                + self.leftSide.variable
            )

            if (
                namespacedVariable
                not in self.mfqlObj.dictDefinitionTable[queryName]
            ):
                raise LipidXException(
                    "The variable %s is not defined with DEFINE."
                    % self.leftSide.variable,
                    queryName,
                    -1,
                )

            # if not (vars.has_key(namespacedVariable) and vars[namespacedVariable]):
            if namespacedVariable in vars and vars[namespacedVariable]:
                # see, if left side is equipped with a attribute
                if self.leftSide.attribute:
                    if vars[namespacedVariable].encodedName != "None":
                        attribute = self.leftSide.attribute
                        try:
                            if attribute.lower() == "error":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errppm,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errppm":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errppm,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errda":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errda,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errres":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errres,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "occ":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].occ,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "binsize":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].binsize,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "charge":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].charge,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "aresolution":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].aresolution,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "anoise":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].anoise,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "exactintensity":
                                dictBeforeIsocoIntensity_holder = {
                                    k: 0
                                    for k in vars[namespacedVariable]
                                    .se[0]
                                    .dictBeforeIsocoIntensity.items()
                                }
                                dictBeforeIsocoIntensity_holder.update(
                                    {
                                        k: v
                                        for se in vars[namespacedVariable].se
                                        for k, v in se.dictBeforeIsocoIntensity.items()
                                    }
                                )
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=None,
                                    dictIntensity=dictBeforeIsocoIntensity_holder,
                                    chemsc=None,
                                    type=TYPE_DICT_INTENS,
                                )

                            elif attribute.lower() == "intensity":
                                if not self.leftSide.item:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=vars[
                                            namespacedVariable
                                        ].intensity,
                                        chemsc=None,
                                        type=TYPE_DICT_INTENS,
                                    )
                                else:
                                    if isinstance(self.leftSide.item, str):
                                        dictIntensity = {}
                                        strSample = self.leftSide.item.strip(
                                            '"'
                                        )
                                        matchFound = False
                                        for key in vars[
                                            namespacedVariable
                                        ].intensity:
                                            if fnmatch(key, strSample):
                                                matchFound = True
                                                dictIntensity[key] = vars[
                                                    namespacedVariable
                                                ].intensity[key]

                                        if matchFound:
                                            leftSide = TypeTmpResult(
                                                options=None,
                                                float=None,
                                                dictIntensity=dictIntensity,
                                                chemsc=None,
                                                type=TYPE_DICT_INTENS,
                                            )

                                            leftSide.flag_dI_regExp = True

                                        else:
                                            leftSide = None

                                    else:
                                        leftSide = TypeTmpResult(
                                            options=None,
                                            float=vars[
                                                namespacedVariable
                                            ].intensity[self.leftSide.item],
                                            dictIntensity=None,
                                            chemsc=None,
                                            type=TYPE_FLOAT,
                                        )

                            elif attribute.lower() == "mass":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].mass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "chemsc":
                                if not self.leftSide.item:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].chemsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].chemsc[
                                                self.leftSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "nlsc":
                                if not self.leftSide.item:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].nlsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].nlsc[
                                                self.leftSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "nlmass":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].nlmass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "frsc":
                                if not self.leftSide.item:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].frsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].frsc[
                                                self.leftSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "frmass":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].frmass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "isobaric":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=None,
                                    string=" @ ".join(
                                        vars[namespacedVariable].isobaric
                                    ),
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_STRING,
                                )

                            elif attribute.lower() == "name":
                                leftSide = TypeTmpResult(
                                    options=None,
                                    float=None,
                                    string=self.mfqlObj.queryName,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_STRING,
                                )

                            elif attribute.lower() == "scconst":
                                if not self.leftSide.item:
                                    leftSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[
                                            namespacedVariable
                                        ].scconst,
                                        type=TYPE_SC_CONSTRAINT,
                                    )
                                else:
                                    raise SyntaxErrorException(
                                        "The attribute .scconst does not "
                                        + "support the [] operator"
                                    )

                            else:
                                raise SyntaxErrorException(
                                    "The attribute %s is not supported "
                                    + "in LipidXplorer" % attribute
                                )

                        except AttributeError as details:
                            print("\nAttributeError:", details)
                            raise LipidXException(
                                "%s has no attribute %s"
                                % (self.leftSide.variable, attribute)
                            )

                    else:
                        leftSide = TypeTmpResult(
                            options=None,
                            float=None,
                            dictIntensity=None,
                            chemsc=None,
                            type=TYPE_NONE,
                        )

                else:  # no attribute given, the standard is the chemical sum composition
                    if not self.leftSide.item:
                        leftSide = TypeTmpResult(
                            options=None,
                            float=None,
                            dictIntensity=None,
                            chemsc=vars[namespacedVariable].chemsc,
                            type=TYPE_CHEMSC,
                        )
                    else:
                        leftSide = TypeTmpResult(
                            options=None,
                            float=float(
                                vars[namespacedVariable].chemsc[
                                    self.leftSide.item
                                ]
                            ),
                            dictIntensity=None,
                            chemsc=None,
                            type=TYPE_FLOAT,
                        )

            else:
                pass
                # raise SyntaxErrorException("Variable %s in query %s does not exist." % (self.leftSide.variable, self.mfqlObj.queryName),
                # 		"",
                # 		None,
                # 		None)

            # log.debug("leftSide: %s", self.environment, leftSide, extra=func)

        # left side is the result of a former TypeExpression
        elif isinstance(self.leftSide, TypeExpression):
            if not self.attribute:
                leftSide = self.leftSide.evaluate(scane, mode, vars, queryName)
            elif self.attribute:
                leftSide = self.leftSide.evaluate(
                    scane, mode, vars, queryName
                )[self.attribute]

        # left side is the result of a former TypeExpression
        elif isinstance(self.leftSide, TypeTmpResult):
            if not self.attribute:
                leftSide = self.leftSide
            else:
                leftSide = self.leftSide[self.attribute]

        # left side is an ElementSequence
        elif isinstance(self.leftSide, TypeElementSequence):
            if not hasattr(self.leftSide, "item"):
                leftSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=self.leftSide.elementSequence,
                    type=TYPE_CHEMSC,
                )
            else:
                leftSide = TypeTmpResult(
                    options=None,
                    float=self.leftSide.elementSequence[self.leftSide.item],
                    dictIntensity=None,
                    chemsc=None,
                    type=TYPE_FLOAT,
                )

        # left side is a float value => switch to float mode
        elif isinstance(self.leftSide, TypeFloat):
            leftSide = TypeTmpResult(
                options=None,
                float=self.leftSide.float,
                dictIntensity=None,
                chemsc=None,
                type=TYPE_FLOAT,
            )

        elif isinstance(self.leftSide, TypeFunction):
            funResult = self.leftSide.evaluate(
                scane, vars, self.environment, queryName
            )

            if isinstance(funResult, TypeTmpResult):
                leftSide = funResult

            elif isinstance(funResult, float):
                leftSide = TypeTmpResult(
                    options=None,
                    float=funResult,
                    dictIntensity=None,
                    chemsc=None,
                    type=TYPE_FLOAT,
                )

            elif isinstance(funResult, type({})):
                leftSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=funResult,
                    chemsc=None,
                    type=TYPE_DICT_INTENS,
                )

            elif isinstance(funResult, ElementSequence):
                leftSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=funResult,
                    type=TYPE_CHEMSC,
                )

            elif isinstance(funResult, str):
                if not funResult == "-----":
                    leftSide = TypeTmpResult(
                        options=None,
                        float=None,
                        dictIntensity=None,
                        chemsc=None,
                        string=funResult,
                        type=TYPE_STRING,
                    )
                else:
                    leftSide = None

            elif isinstance(funResult, bool):
                leftSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=None,
                    string=None,
                    bool=funResult,
                    type=TYPE_BOOL,
                )
            else:
                leftSide = None

            pass

        ### right side ###

        # right side is a variable
        rightSide = []
        if isinstance(self.rightSide, TypeVariable):
            # add namespace
            namespacedVariable = (
                queryName
                + self.mfqlObj.namespaceConnector
                + self.rightSide.variable
            )

            if (
                namespacedVariable
                not in self.mfqlObj.dictDefinitionTable[queryName]
            ):
                raise SyntaxErrorException(
                    "The variable %s is not defined with DEFINE."
                    % self.rightSide.variable,
                    fileName,
                    -1,
                )

            if namespacedVariable in vars and vars[namespacedVariable]:
                # see, if left side is equipped with a attribute
                if self.rightSide.attribute:
                    if vars[namespacedVariable].encodedName != "None":
                        attribute = self.rightSide.attribute
                        try:
                            if attribute.lower() == "error":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errppm,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errppm":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errppm,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errda":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errda,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "errres":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].errres,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "occ":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].occ,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "charge":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].charge,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "aresolution":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].aresolution,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "anoise":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].anoise,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "binsize":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].binsize,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "intensity":
                                if not self.rightSide.item:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=vars[
                                            namespacedVariable
                                        ].intensity,
                                        chemsc=None,
                                        type=TYPE_DICT_INTENS,
                                    )
                                else:
                                    if isinstance(self.rightSide.item, str):
                                        dictIntensity = {}
                                        strSample = self.rightSide.item.strip(
                                            '"'
                                        )
                                        matchFound = False
                                        for key in vars[
                                            namespacedVariable
                                        ].intensity:
                                            if fnmatch(key, strSample):
                                                dictIntensity[key] = vars[
                                                    namespacedVariable
                                                ].intensity[key]
                                                matchFound = True

                                        if matchFound:
                                            rightSide = TypeTmpResult(
                                                options=None,
                                                float=None,
                                                dictIntensity=dictIntensity,
                                                chemsc=None,
                                                type=TYPE_DICT_INTENS,
                                            )
                                            rightSide.flag_dI_regExp = True
                                        else:
                                            rightSide = None

                                    else:
                                        rightSide = TypeTmpResult(
                                            options=None,
                                            float=vars[
                                                namespacedVariable
                                            ].intensity[self.rightSide.item],
                                            dictIntensity=None,
                                            chemsc=None,
                                            type=TYPE_FLOAT,
                                        )

                            elif attribute.lower() == "mass":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].mass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "chemsc":
                                if not self.rightSide.item:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].chemsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].chemsc[
                                                self.rightSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "scconst":
                                if not self.rightSide.item:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[
                                            namespacedVariable
                                        ].scconst,
                                        type=TYPE_SC_CONSTRAINT,
                                    )
                                else:
                                    raise SyntaxErrorException(
                                        "The attribute .scconst does not "
                                        + "support the [] operator"
                                    )

                            elif attribute.lower() == "nlsc":
                                if not self.rightSide.item:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].nlsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].nlsc[
                                                self.rightSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "nlmass":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].nlmass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "frsc":
                                if not self.rightSide.item:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=None,
                                        dictIntensity=None,
                                        chemsc=vars[namespacedVariable].frsc,
                                        type=TYPE_CHEMSC,
                                    )
                                else:
                                    rightSide = TypeTmpResult(
                                        options=None,
                                        float=float(
                                            vars[namespacedVariable].frsc[
                                                self.rightSide.item
                                            ]
                                        ),
                                        dictIntensity=None,
                                        chemsc=None,
                                        type=TYPE_FLOAT,
                                    )

                            elif attribute.lower() == "frmass":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=vars[namespacedVariable].frmass,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_FLOAT,
                                )

                            elif attribute.lower() == "isobaric":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=None,
                                    string=" @ ".join(
                                        vars[namespacedVariable].isobaric
                                    ),
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_STRING,
                                )

                            elif attribute.lower() == "name":
                                rightSide = TypeTmpResult(
                                    options=None,
                                    float=None,
                                    string=self.mfqlObj.queryName,
                                    dictIntensity=None,
                                    chemsc=None,
                                    type=TYPE_STRING,
                                )

                            else:
                                raise SyntaxErrorException(
                                    "The attribute %s is not supported "
                                    + "in LipidXplorer" % attribute
                                )

                        except AttributeError as details:
                            print("\nAttributeError:", details)
                            raise LipidXException(
                                "%s has no attribute %s"
                                % (self.rightSide.variable, attribute)
                            )

                    else:
                        rightSide = TypeTmpResult(
                            options=None,
                            float=None,
                            dictIntensity=None,
                            chemsc=None,
                            type=TYPE_NONE,
                        )

                else:  # no attribute given, the standard is the chemical sum composition
                    if not self.rightSide.item:
                        rightSide = TypeTmpResult(
                            options=None,
                            float=None,
                            dictIntensity=None,
                            chemsc=vars[namespacedVariable].chemsc,
                            type=TYPE_CHEMSC,
                        )
                    else:
                        rightSide = TypeTmpResult(
                            options=None,
                            float=float(
                                vars[namespacedVariable].chemsc[
                                    self.rightSide.item
                                ]
                            ),
                            dictIntensity=None,
                            chemsc=None,
                            type=TYPE_FLOAT,
                        )
            else:
                pass
                # raise SyntaxErrorException("Variable %s in query %s does not exist." % (self.rightSide.variable, self.mfqlObj.queryName),
                # 		"",
                # 		None,
                # 		None)

        # right side is the result of a former TypeExpression
        elif isinstance(self.rightSide, TypeExpression):
            if not self.attribute:
                rightSide = self.rightSide.evaluate(
                    scane, mode, vars, queryName
                )
            else:
                rightSide = self.rightSide.evaluate(
                    scane, mode, vars, queryName
                )[self.attribute]

        # right side is an ElementSequence
        elif isinstance(self.rightSide, TypeElementSequence):
            if not hasattr(self.rightSide, "item"):
                rightSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=self.rightSide.elementSequence,
                    type=TYPE_CHEMSC,
                )
            else:
                rightSide = TypeTmpResult(
                    options=None,
                    float=self.rightSide.elementSequence[self.rightSide.item],
                    dictIntensity=None,
                    chemsc=None,
                    type=TYPE_FLOAT,
                )

        # right side is a float value => switch to float mode
        elif isinstance(self.rightSide, TypeFloat):
            rightSide = TypeTmpResult(
                options=None,
                float=self.rightSide.float,
                dictIntensity=None,
                chemsc=None,
                type=TYPE_FLOAT,
            )

        elif isinstance(self.rightSide, TypeFunction):
            funResult = self.rightSide.evaluate(
                scane, self.mfqlObj.currVars, self.environment, queryName
            )

            if isinstance(funResult, TypeTmpResult):
                rightSide = funResult

            elif isinstance(funResult, float):
                rightSide = TypeTmpResult(
                    options=None,
                    float=funResult,
                    dictIntensity=None,
                    chemsc=None,
                    type=TYPE_FLOAT,
                )

            elif isinstance(funResult, type({})):
                rightSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=funResult,
                    chemsc=None,
                    type=TYPE_DICT_INTENS,
                )

            elif isinstance(funResult, ElementSequence):
                rightSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=funResult,
                    type=TYPE_CHEMSC,
                )

            elif isinstance(funResult, str):
                if not funResult == "-----":
                    rightSide = TypeTmpResult(
                        options=None,
                        float=None,
                        dictIntensity=None,
                        chemsc=None,
                        string=funResult,
                        type=TYPE_STRING,
                    )

            elif isinstance(funResult, bool):
                rightSide = TypeTmpResult(
                    options=None,
                    float=None,
                    dictIntensity=None,
                    chemsc=None,
                    string=None,
                    bool=funResult,
                    type=TYPE_BOOL,
                )
            else:
                rightSide = None

        else:
            # rightSide = None
            pass

        ### calculate the result ###

        # ^^^TODO^^^
        # if a mark is not found, stop
        if notFound:
            return None

        # only one side is given (e.g. a term with only a variable)
        if not leftSide and rightSide and self.isSingleton:
            result = rightSide
            # return result

        # only one side is given (the other one)
        elif not rightSide and leftSide and self.isSingleton:
            result = leftSide
            # return result

        # only one side is given (e.g. a term with only a variable)
        elif not leftSide and rightSide and not self.isSingleton:
            result = None
            # result = rightSide

        # only one side is given (the other one)
        elif not rightSide and leftSide and not self.isSingleton:
            result = None
            # result = leftSide

        elif not leftSide and not rightSide:
            result = None

        else:
            result = None

            tmpResult = []

            if leftSide.isType(TYPE_CHEMSC) and rightSide.isType(TYPE_CHEMSC):
                if not self.operator == "*" and not self.operator == "/":
                    result = TypeTmpResult(
                        options=None,
                        chemsc=op(
                            self.operator, leftSide.chemsc, rightSide.chemsc
                        ),
                        float=None,
                        dictIntensity=None,
                        type=TYPE_CHEMSC,
                    )

                else:
                    raise lpdxUIExceptions.SyntaxErrorException(
                        "Multiplication or division of two elemental compositions is not permitted.",
                        "",
                        queryName,
                        0,
                    )

            elif leftSide.isType(TYPE_CHEMSC) and rightSide.isType(TYPE_FLOAT):
                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=op(
                        self.operator,
                        leftSide.chemsc.getWeight(),
                        rightSide.float,
                    ),
                    dictIntensity=None,
                    type=TYPE_FLOAT,
                )

            elif leftSide.isType(TYPE_FLOAT) and rightSide.isType(TYPE_CHEMSC):
                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=op(
                        self.operator,
                        leftSide.float,
                        rightSide.chemsc.getWeight(),
                    ),
                    dictIntensity=None,
                    type=TYPE_FLOAT,
                )

            elif leftSide.isType(TYPE_FLOAT) and rightSide.isType(TYPE_FLOAT):
                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=op(self.operator, leftSide.float, rightSide.float),
                    dictIntensity=None,
                    type=TYPE_FLOAT,
                )

            elif leftSide.isType(TYPE_DICT_INTENS) and rightSide.isType(
                TYPE_DICT_INTENS
            ):
                dictIntensityResult = {}
                for lkey in list(leftSide.dictIntensity.keys()):
                    dictIntensityResult[lkey] = op(
                        self.operator,
                        leftSide.dictIntensity[lkey],
                        rightSide.dictIntensity[lkey],
                    )

                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=None,
                    dictIntensity=dictIntensityResult,
                    type=TYPE_DICT_INTENS,
                )

            elif leftSide.isType(TYPE_DICT_INTENS) and rightSide.isType(
                TYPE_FLOAT
            ):
                dictIntensityResult = {}
                for lkey in list(leftSide.dictIntensity.keys()):
                    dictIntensityResult[lkey] = op(
                        self.operator,
                        leftSide.dictIntensity[lkey],
                        rightSide.float,
                    )

                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=None,
                    dictIntensity=dictIntensityResult,
                    type=TYPE_DICT_INTENS,
                )

            elif leftSide.isType(TYPE_FLOAT) and rightSide.isType(
                TYPE_DICT_INTENS
            ):
                dictIntensityResult = {}
                for lkey in list(rightSide.dictIntensity.keys()):
                    dictIntensityResult[lkey] = op(
                        self.operator,
                        leftSide.float,
                        rightSide.dictIntensity[lkey],
                    )

                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=None,
                    dictIntensity=dictIntensityResult,
                    type=TYPE_DICT_INTENS,
                )

        if self.item:
            if result.isType(TYPE_CHEMSC):
                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=result.chemsc[self.item],
                    dictIntensity=None,
                    type=TYPE_FLOAT,
                )

            elif result.isType(TYPE_DICT_INTENS):
                result = TypeTmpResult(
                    options=None,
                    chemsc=None,
                    float=result.dictIntensity[self.item],
                    dictIntensity=None,
                    type=TYPE_FLOAT,
                )

        return result


class TypeMarkTerm:
    def __init__(self, leftSide, rightSide, boolOp, mfqlObj):
        self.leftSide = leftSide
        self.rightSide = rightSide
        self.operator = boolOp
        self.mfqlObj = mfqlObj

        self.result = None
        self.noOfSymbols = 0

    def evaluate(self, callback):
        leftResult = False
        rightResult = False

        if (
            isinstance(self.leftSide, TypeSFConstraint)
            or isinstance(self.leftSide, TypeElementSequence)
            or isinstance(self.leftSide, TypeFloat)
            or isinstance(self.leftSide, TypeList)
        ):
            if self.leftSide.name in res and res[self.leftSide.name] != []:
                leftResult = True

        elif isinstance(self.leftSide, TypeMarkTerm):
            leftResult = self.leftSide.evaluate(callback)

        if (
            isinstance(self.rightSide, TypeSFConstraint)
            or isinstance(self.rightSide, TypeElementSequence)
            or isinstance(self.rightSide, TypeFloat)
            or isinstance(self.rightSide, TypeList)
        ):
            if self.rightSide.name in res and res[self.rightSide.name] != []:
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


class TypeElementSequence:
    def __init__(self, elementSequence, options):
        self.elementSequence = elementSequence
        self.options = options
        self.precursor = None

        self.listMarks = None

    def evaluate(self):
        if self.scan:
            self.listMarks = self.scan.evaluate()

    def addOptions(self, listOptions):
        for op in listOptions:
            if op[0] == "chg":
                self.elementSequence.polarity = op[1]
                self.elementSequence.charge = op[1]
            else:
                self.options[op[0]] = op[1]

    pass


class TypeSFConstraint:
    def __init__(self, elementSequence):
        self.elementSequence = elementSequence

        self.varcontent = None
        self.options = {}
        self.name = ""
        self.scope = ""
        self.precursor = None

        self.listMarks = None

    def addOptions(self, listOptions):
        dbChanged = False
        for op in listOptions:
            if op[0] == "dbr":
                self.elementSequence.lwBoundDbEq = op[1][0].float
                self.elementSequence.upBoundDbEq = op[1][1].float
                dbChanged = True
            elif op[0] == "chg":
                self.elementSequence.polarity = op[1]
                self.elementSequence.charge = op[1]
            else:
                self.options[op[0]] = op[1]

        if not self.elementSequence:
            dbChanged = True

        if not dbChanged:
            raise SyntaxErrorException(
                "ERROR in %s: Without given double bound range,"
                % self.mfqlObj.queryName
                + "no sum composition calculation possible",
                "",
                self.mfqlObj.queryName,
                0,
            )

    def evaluate(self):
        if self.scan:
            self.listMarks = self.scan.evaluate()


class TypeList:
    def __init__(self, list=None):
        self.listElementSequence = list

        self.varcontent = None
        self.options = {}
        self.name = ""
        self.scope = ""
        self.precursor = None

        self.listMarks = None

        self.isMultiple = False
        self.listNames = []

    def __iter__(self):
        return iter(self.listElementSequence)

    def nameList(self):
        for es in self.listElementSequence:
            es.name = self.name

    def addName(self, name):
        self.listNames.append(name)

    def addOptions(self, listOptions):
        for op in listOptions:
            if op[0] == "chg":
                for es in self.listElementSequence:
                    es.polarity = op[1]
                    es.charge = op[1]
                    es.elementSequence.charge = op[1]
            self.options[op[0]] = op[1]

    def evaluate(self):
        if self.scan:
            self.listMarks = self.scan.evaluate()


class TypeTmpResult:
    def __init__(
        self,
        options,
        type,
        chemsc=None,
        float=0.0,
        dictIntensity=None,
        string="",
    ):  # , type = TYPE_NONE):
        assert not type is None

        self.options = options
        self.chemsc = chemsc
        self.float = float
        self.string = string
        self.dictIntensity = dictIntensity
        self.flag_dI_regExp = False
        self.type = type

    def __repr__(self):
        str = ""
        if self.chemsc:
            str += "%s" % self.chemsc
        elif self.float:
            str += "%s" % self.float
        elif self.dictIntensity:
            str += "%s" % self.dictIntensity
        elif self.string:
            str += "%s" % self.string
        return str

    def __float__(self):
        if self.float:
            return self.float

    def isType(self, type):
        return type == self.type

    def getFloat(self):
        r = False
        if self.float:
            r = self.float
        elif self.dictIntensity:
            r = self.dictIntensity
        return r


class TypeVariable:
    def __init__(self, variable=None, attribute=None, item=None):
        # init
        self.variable = variable
        self.name = variable
        self.attribute = attribute
        self.item = item

        # init as empty
        self.scope = None
        self.scanned = False
        self.options = None

    def __repr__(self):
        return "TypeVariable: " + self.variable


class TypeFunction:
    def __init__(self, name=None, arguments=None, mfqlObj=None, vars=None):
        # init
        self.name = name
        self.arguments = arguments
        self.mfqlObj = mfqlObj
        self.vars = vars
        self.funs = InternFunctions(vars, mfqlObj)
        self.attribute = None

    def evaluate(self, scane, vars, env, queryName, sc=None):
        # from math import *
        if self.name in self.funs.listFuns:
            return self.funs.startFun(self.name, self.arguments, vars)
        else:
            strEval = "%s(" % self.name
            for arg in self.arguments:
                if isinstance(arg, TypeFloat):
                    strEval += "%s," % arg.float
                elif isinstance(arg, TypeString):
                    strEval += "%s," % arg.string
                elif isinstance(arg, TypeVariable):
                    # correct namespace
                    # arg.variable = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + arg.variable
                    namespacedVariable = (
                        self.mfqlObj.queryName
                        + self.mfqlObj.namespaceConnector
                        + arg.variable
                    )

                    if namespacedVariable in vars and vars[namespacedVariable]:
                        # see, if left side is equipped with a attribute
                        if arg.attribute:
                            attribute = arg.attribute
                            try:
                                if attribute.lower() == "error":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].errppm
                                    )

                                if attribute.lower() == "errppm":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].errppm
                                    )

                                if attribute.lower() == "errda":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].errda
                                    )

                                if attribute.lower() == "errres":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].errres
                                    )

                                elif attribute.lower() == "intensity":
                                    strEval += (
                                        "%s,"
                                        % vars[namespacedVariable].intensity
                                    )

                                elif attribute.lower() == "mass":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].mass
                                    )

                                elif attribute.lower() == "occ":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].occ
                                    )

                                elif attribute.lower() == "binsize":
                                    strEval += (
                                        "%f,"
                                        % vars[namespacedVariable].binsize
                                    )

                                elif attribute.lower() == "charge":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].charge
                                    )

                                elif attribute.lower() == "aresolution":
                                    strEval += (
                                        "%f,"
                                        % vars[namespacedVariable].aresolution
                                    )

                                elif attribute.lower() == "anoise":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].anoise
                                    )

                                elif attribute.lower() == "chemsc":
                                    if not arg.item:
                                        strDict = "deepcopy(ElementSequence({"
                                        for sym in vars[
                                            namespacedVariable
                                        ].chemsc.seq:
                                            strDict += "'%s' : %d, " % (
                                                sym.sym,
                                                vars[
                                                    namespacedVariable
                                                ].chemsc[sym.sym],
                                            )
                                        strDict += (
                                            "'chg' : %d}))"
                                            % vars[
                                                namespacedVariable
                                            ].chemsc.charge
                                        )
                                        strEval += "%s," % strDict
                                    else:
                                        strEval += (
                                            "%f,"
                                            % vars[namespacedVariable].chemsc[
                                                arg.item
                                            ]
                                        )

                                elif attribute.lower() == "nlsc":
                                    if not arg.item:
                                        strDict = "deepcopy(ElementSequence({"
                                        for sym in vars[
                                            namespacedVariable
                                        ].nlsc.seq:
                                            strDict += "'%s' : %d, " % (
                                                sym.sym,
                                                vars[namespacedVariable].nlsc[
                                                    sym.sym
                                                ],
                                            )
                                        strDict += (
                                            "'chg' : %d}))"
                                            % vars[
                                                namespacedVariable
                                            ].nlsc.charge
                                        )
                                        strEval += "%s," % strDict
                                    else:
                                        strEval += (
                                            "%f,"
                                            % vars[namespacedVariable].nlsc[
                                                arg.item
                                            ]
                                        )

                                elif attribute.lower() == "nlmass":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].nlmass
                                    )

                                elif attribute.lower() == "frsc":
                                    if not arg.item:
                                        strDict = "deepcopy(ElementSequence({"
                                        for sym in vars[
                                            namespacedVariable
                                        ].frsc.seq:
                                            strDict += "'%s' : %d, " % (
                                                sym.sym,
                                                vars[namespacedVariable].frsc[
                                                    sym.sym
                                                ],
                                            )
                                        strDict += (
                                            "'chg' : %d}))"
                                            % vars[
                                                namespacedVariable
                                            ].frsc.charge
                                        )
                                        strEval += "%s," % strDict
                                    else:
                                        strEval += (
                                            "%f,"
                                            % vars[namespacedVariable].frsc[
                                                arg.item
                                            ]
                                        )

                                elif attribute.lower() == "frmass":
                                    strEval += (
                                        "%f," % vars[namespacedVariable].frmass
                                    )

                            except AttributeError:
                                print("\nAttributeError:", details)
                                raise LipidXException(
                                    "The type of %s is not supported by %s()"
                                    % (arg.variable, self.name)
                                )

                        else:
                            print("\nAttributeError:", details)
                            raise LipidXException(
                                "The type of %s is not supported by %s()"
                                % (arg.variable, self.name)
                            )
                    else:
                        return "-----"

                elif isinstance(arg, TypeExpression):
                    result = arg.evaluate(scane, "", vars, queryName)

                    if result.float:
                        strEval += "%f," % result.float

                    elif result.dictIntensity:
                        strEval += "%s," % result.dictIntensity

                    elif result.chemsc:
                        strDict = "deepcopy(ElementSequence({"
                        for element in list(result.chemsc.values()):
                            strDict += "'%s' : %d, " % (
                                element.sym,
                                element.get_count(),
                            )
                        strDict += "'chg' : %d}))" % result.chemsc.charge
                        strEval += "%s," % strDict

                else:
                    raise LipidXException("Type error with %s" % repr(arg))

                # varCount += 1

            strEval = strEval[:-1]
            strEval += ")"

            # if not self.item:
            # TODO: function should not return a integer
            result = eval(strEval)
            return result

    def __repr__(self):
        return "Func[%s](%s)" % (self.name, self.arguments)


class TypeFloat:
    def __init__(
        self,
        float=None,
        precursor=None,
        mass=None,
        options=None,
        charge=None,
        polarity=None,
    ):
        self.float = float
        self.precursor = precursor
        self.mass = mass

        if options:
            self.options = options
        else:
            self.options = {}

        self.polarity = polarity
        self.charge = charge
        self.elementSequence = None

    def addOptions(self, listOptions):
        for op in listOptions:
            if op[0] == "chg":
                self.polarity = op[1]
            else:
                self.options[op[0]] = op[1]


class TypeTolerance:
    def __init__(self, kind, t, smallestMass=0.0, delta=0.0):
        """IN: kind -> 'Da', 'res', 'ppm'
        t -> tolerance"""

        assert isinstance(smallestMass, float)
        assert isinstance(delta, float)

        self.smallestMass = smallestMass

        if kind == "Da" or kind == "da":
            self.kind = "Da"
            self.da = t
            self.tolerance = None
            self.ppm = None
        elif kind == "res":
            self.kind = "res"
            self.ppm = 1000000 / t
            self.tolerance = t
            self.da = None
            self.delta = delta
        elif kind == "ppm":
            self.kind = "ppm"
            self.ppm = t
            self.tolerance = 1000000 / t
            self.da = None
        else:
            raise ValueError("Wrong tolerance type given: %s" % kind)

        self.res = self.tolerance  # for more consistency

    def fitIn(self, mass, m):
        """Does mass fit in m +- tolerance? Or else:
        fitIn(<experimental mass>, <theoretical mass>)"""

        if self.kind != "Da":
            t = self.getTinDA(mass)
        else:
            t = self.da

        if mass - t <= m and m <= mass + t:
            return True
        else:
            return False

    def fitInNL(self, mass, m, fragMass):
        """Does mass fit in m +- tolerance?"""

        if self.kind != "Da":
            t = self.getTinDA(fragMass)
        else:
            t = self.da

        if mass - t <= m and m <= mass + t:
            return True
        else:
            return False

    def getTinR(self):
        return self.tolerance

    def getTinPPM(self):
        return self.ppm

    def getTinDA(self, mass):
        if self.kind == "res":
            return mass / (
                (mass - self.smallestMass) * self.delta + self.tolerance
            )
        elif self.kind == "ppm":
            return mass / self.tolerance
        else:
            return self.da

    # 	def res(self):
    # 		return self.tolerance
    #
    # 	def ppm(self):
    # 		return self.ppm
    #
    # 	def da(self, mass):
    # 		return mass / self.tolerance

    def evaluate(self):
        return self.da

    def __repr__(self):
        if self.kind == "Da":
            return "%4.4f Da" % self.da
        else:
            return "%.2f ppm" % self.ppm

    def __cmp__(self, other):
        a = self.__repr__()
        b = other.__repr__()
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

    ##########################################
    # This part is for the functions of MFQL #
    ##########################################


# all functions below are for the use withing a query
def func(float):
    return float**2


def isEven(float):
    if float % 2 == 0:
        return True
    else:
        return False


def isEvenNominal(float):
    f = int(float)
    if f % 2 == 0:
        return True
    else:
        return False


def isOddNominal(float):
    f = int(float)
    if f % 2 == 0:
        return True
    else:
        return False


def isOdd(float):
    if float % 2 == 1:
        return True
    else:
        return False


def sub(sc1, sc2):
    return sc1 - sc2


def sumIntensity(*input):
    result = ""
    return input


# the class for function calls
class InternFunctions:
    def __init__(self, vars, mfqlObj):
        self.listFuns = [
            "sumIntensity",
            "column",
            "avg",
            "abs",
            "score",
            "isStandard",
            "nbsmpls",
            "medianU",
            "medianL",
        ]
        self.listPostFuns = ["isStandard"]
        self.vars = vars
        self.mfqlObj = mfqlObj

    # def startFun(self, fun, args, vars):
    def startFun(self, fun, args, vars):
        currArguments = copy(args)

        ### if it is a postFunction, redirect it to pospostFunction() ###

        if fun == "isStandard" and len(currArguments) == 3:
            # collect arguments
            varName = (
                self.mfqlObj.queryName
                + self.mfqlObj.namespaceConnector
                + currArguments[0].name
            )
            globSample = currArguments[1].string
            scope = currArguments[2].string

            funName = "isStandard"
            funArgs = [
                self.mfqlObj.queryName
                + self.mfqlObj.namespaceConnector
                + currArguments[0].name,
                currArguments[1].string,
                currArguments[2].string,
            ]

            # direct function call to post functions
            if self.mfqlObj.queryName not in self.mfqlObj.dictPostFuns:
                self.mfqlObj.dictPostFuns[self.mfqlObj.queryName] = {
                    funName: funArgs
                }

            return True

        if fun == "isStandard" and len(currArguments) == 2:
            # collect arguments
            varName = (
                self.mfqlObj.queryName
                + self.mfqlObj.namespaceConnector
                + currArguments[0].name
            )
            scope = currArguments[1].string

            funName = "isStandard"
            funArgs = [
                self.mfqlObj.queryName
                + self.mfqlObj.namespaceConnector
                + currArguments[0].name,
                currArguments[1].string,
            ]

            # direct function call to post functions
            if self.mfqlObj.queryName not in self.mfqlObj.dictPostFuns:
                self.mfqlObj.dictPostFuns[self.mfqlObj.queryName] = {
                    funName: funArgs
                }

            return True

        ### evaluate Arguments ###

        boolEvaluated = False

        while not boolEvaluated:
            boolEvaluated = True
            for index in range(len(currArguments)):
                if isinstance(currArguments[index], TypeExpression):
                    currArguments[index] = currArguments[index].evaluate(
                        mode=None,
                        scane=None,
                        vars=self.mfqlObj.currVars,
                        queryName=self.mfqlObj.queryName,
                        sc=self.mfqlObj.sc,
                    )
                elif isinstance(currArguments[index], TypeFloat):
                    leftSide = TypeTmpResult(
                        options=None,
                        type=TYPE_FLOAT,
                        float=currArguments[index].float,
                        dictIntensity=None,
                        chemsc=None,
                    )
                elif isinstance(currArguments[index], TypeTmpResult):
                    pass
                elif isinstance(currArguments[index], TypeVariable):
                    boolEvaluated = False
                    currArguments[index] = TypeExpression(
                        isSingleton=True,
                        leftSide=currArguments[index],
                        rightSide=None,
                        operator=None,
                        environment=self.mfqlObj.queryName,
                        mfqlObj=self.mfqlObj,
                    ).evaluate(
                        mode=None,
                        scane=None,
                        vars=self.mfqlObj.currVars,
                        queryName=self.mfqlObj.queryName,
                        sc=None,
                    )  # self.mfqlObj.sc)
                elif isinstance(currArguments[index], TypeFunction):
                    boolEvaluated = False
                    currArguments[index] = currArguments[index].evaluate(
                        scane,
                        self.mfqlObj.currVars,
                        self.environment,
                        queryName,
                    )
                elif isinstance(currArguments[index], type(0.0)):
                    boolEvaluated = False
                    currArguments[index] = TypeTmpResult(
                        options=None,
                        type=TYPE_FLOAT,
                        float=currArguments[index],
                        dictIntensity=None,
                        chemsc=None,
                    )
        if currArguments[0]:
            ### process functions ###

            if fun == "nbsmpls":
                # generate the result as TypeTmpResult
                result = TypeTmpResult(
                    options=None,
                    type=TYPE_FLOAT,
                    chemsc=None,
                    float=len(self.mfqlObj.sc.listSamples),
                    string=None,
                    dictIntensity=None,
                )

            if fun == "score":
                if self.mfqlObj.sc.options["MSMSaccuracy"].ppm:
                    # collect the intensities, get rid of double entries
                    # first argument is the intensity dictionary
                    sum = 0
                    for arg in currArguments:
                        if arg:
                            sum += abs(arg.errppm)
                        else:
                            sum += 0
                    avg = sum / len(currArguments)

                    score = "%.2f" % (
                        1 - (avg / self.mfqlObj.sc.options["MSMSaccuracy"].ppm)
                    )

                elif self.mfqlObj.sc.options["MSMSaccuracy"].da:
                    # collect the intensities, get rid of double entries
                    # first argument is the intensity dictionary
                    sum = 0
                    for arg in currArguments:
                        if arg:
                            sum += abs(arg.errda)
                        else:
                            sum += 0
                    avg = sum / len(currArguments)

                    score = "%.2f" % (
                        1 - (avg / self.mfqlObj.sc.options["MSMSaccuracy"].da)
                    )

                # generate the result as TypeTmpResult
                result = TypeTmpResult(
                    options=None,
                    type=TYPE_STRING,
                    chemsc=None,
                    float=None,
                    string=score,
                    dictIntensity=None,
                )

            if fun == "avg":
                if len(currArguments) == 1:
                    if currArguments[0].dictIntensity:
                        # collect the intensities, get rid of double entries
                        # first argument is the intensity dictionary
                        sum = 0
                        for key in list(currArguments[0].dictIntensity.keys()):
                            if currArguments[0].dictIntensity[key] != "-1":
                                sum += currArguments[0].dictIntensity[key]
                            else:
                                sum += 0
                        avg = sum / len(
                            list(currArguments[0].dictIntensity.keys())
                        )

                        # generate the result as TypeTmpResult
                        result = TypeTmpResult(
                            options=None,
                            type=TYPE_FLOAT,
                            chemsc=None,
                            float=avg,
                            dictIntensity=None,
                        )

                else:
                    # collect the intensities, get rid of double entries
                    # first argument is the intensity dictionary
                    sum = 0
                    for arg in currArguments:
                        if arg:
                            sum += arg.float
                        else:
                            sum += 0
                    avg = sum / len(currArguments)

                    # generate the result as TypeTmpResult
                    result = TypeTmpResult(
                        options=None,
                        type=TYPE_FLOAT,
                        chemsc=None,
                        float=avg,
                        dictIntensity=None,
                    )

            if fun == "medianU":  # median - take lower median if list is even
                if len(currArguments) == 1:
                    if currArguments[0].dictIntensity:
                        d = sorted(currArguments[0].dictIntensity.values())
                        dl = len(d)

                        if dl % 2 == 1:
                            median = d[(dl + 1) / 2 - 1]
                        else:
                            median = d[dl / 2]  # take upper median

                        # generate the result as TypeTmpResult
                        result = TypeTmpResult(
                            options=None,
                            type=TYPE_FLOAT,
                            chemsc=None,
                            float=median,
                            dictIntensity=None,
                        )

                else:
                    # collect the intensities, get rid of double entries
                    # first argument is the intensity dictionary

                    d = sorted(currArguments)
                    dl = len(d)

                    if dl % 2 == 1:
                        median = d[(dl + 1) / 2 - 1]
                    else:
                        median = d[dl / 2]  # take upper median

                    # generate the result as TypeTmpResult
                    result = TypeTmpResult(
                        options=None,
                        type=TYPE_FLOAT,
                        chemsc=None,
                        float=median,
                        dictIntensity=None,
                    )

            if fun == "medianL":  # median - take lower median if list is even
                if len(currArguments) == 1:
                    if currArguments[0].dictIntensity:
                        d = sorted(currArguments[0].dictIntensity.values())
                        dl = len(d)

                        if dl % 2 == 1:
                            median = d[(dl + 1) / 2 - 1]
                        else:
                            median = d[dl / 2 - 1]  # take lower median

                        # generate the result as TypeTmpResult
                        result = TypeTmpResult(
                            options=None,
                            type=TYPE_FLOAT,
                            chemsc=None,
                            float=median,
                            dictIntensity=None,
                        )

                else:
                    # collect the intensities, get rid of double entries
                    # first argument is the intensity dictionary

                    d = sorted(currArguments)
                    dl = len(d)

                    if dl % 2 == 1:
                        median = d[(dl + 1) / 2 - 1]
                    else:
                        median = d[dl / 2 - 1]  # take lower median

                    # generate the result as TypeTmpResult
                    result = TypeTmpResult(
                        options=None,
                        type=TYPE_FLOAT,
                        chemsc=None,
                        float=median,
                        dictIntensity=None,
                    )

            if fun == "abs":
                if len(currArguments) == 1:
                    if currArguments[0].dictIntensity:
                        # collect the intensities, get rid of double entries
                        # first argument is the intensity dictionary
                        sum = 0
                        for key in list(currArguments[0].dictIntensity.keys()):
                            if currArguments[0].dictIntensity[key] != "-1":
                                currArguments[0].dictIntensity[key] = abs(
                                    currArguments[0].dictIntensity[key]
                                )

                        # generate the result as TypeTmpResult
                        result = TypeTmpResult(
                            options=None,
                            type=TYPE_DICT_INTENS,
                            chemsc=None,
                            float=None,
                            dictIntensity=currArguments[0].dictIntensity,
                        )

                    else:
                        if currArguments[0].float < 0.0:
                            absolute = 0 - currArguments[0].float
                        else:
                            absolute = currArguments[0].float

                        # generate the result as TypeTmpResult
                        result = TypeTmpResult(
                            options=None,
                            type=TYPE_FLOAT,
                            chemsc=None,
                            float=absolute,
                            dictIntensity=None,
                        )
                else:
                    raise AttributeError(
                        "Only one attribute allowed for the function abs()"
                    )

            if fun == "sumIntensity":
                ### sum the given intensities iff the peaks are different ###

                # try:
                # 	# get vars from the functions attributes
                # 	v = []
                # 	for i in currArguments:
                # 		v.append(i)
                # 		varName = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + i.name
                # 		#if vars.has_key(varName):
                # 		#	v.append(vars[varName])
                # except AttributeError as detail:
                # 	raise SyntaxErrorException("ERROR: Function sumIntensity() in %s got wrong"  % self.mfqlObj.queryName +\
                # 		" type of arguments. It should be just the variable names. %s" % detail,
                # 		"",
                # 		self.mfqlObj.queryName,
                # 		0)

                # 	return -1

                v = []
                for i in currArguments:
                    if i.isType(TYPE_DICT_INTENS):
                        v.append(i)
                    else:
                        raise SyntaxErrorException(
                            "ERROR: Function sumIntensity() in %s got wrong"
                            % self.mfqlObj.queryName
                            + " type of arguments. It should be '.intensity'.",
                            "",
                            self.mfqlObj.queryName,
                            0,
                        )

                # collect the intensities, get rid of double entries
                toSum = [v[0]]
                samples = list(v[0].dictIntensity.keys())
                for i in v[1:]:
                    isIn = False
                    for j in toSum:
                        # if i.mass == j.mass:
                        for sample in samples:
                            if (
                                i.dictIntensity[sample]
                                != j.dictIntensity[sample]
                            ):
                                isIn = True

                    if isIn:
                        toSum.append(i)

                # sum the intensities
                dictIntensityResult = {}
                for i in toSum:
                    isotopeMode = True
                    for k in samples:
                        if k in dictIntensityResult:
                            if i.dictIntensity[k] >= 0.0:
                                isotopeMode = False

                            if isotopeMode:
                                dictIntensityResult[k] += i.dictIntensity[k]
                            else:
                                if i.dictIntensity[k] <= 0.0:
                                    pass
                                else:
                                    dictIntensityResult[k] += i.dictIntensity[
                                        k
                                    ]

                        else:
                            dictIntensityResult[k] = i.dictIntensity[k]

                # generate the result as TypeTmpResult
                result = TypeTmpResult(
                    options=None,
                    type=TYPE_DICT_INTENS,
                    chemsc=None,
                    float=None,
                    dictIntensity=dictIntensityResult,
                )

            if fun == "column":
                ### return the intensities of the samples specified with a regular expression ###

                import re

                varName = (
                    self.mfqlObj.queryName
                    + self.mfqlObj.namespaceConnector
                    + currArguments[0].name
                )

                # get vars from the functions attributes
                v = None
                if varName in vars:
                    v = vars[varName]

                dictIntensityResult = {}
                if v:
                    for i in list(v.intensity.keys()):
                        if re.match(currArguments[1].string, i):
                            dictIntensityResult[i] = v.intensity[i]

                # generate the result as TypeTmpResult
                result = TypeTmpResult(
                    options=None,
                    type=TYPE_DICT_INTENS,
                    chemsc=None,
                    float=None,
                    dictIntensity=dictIntensityResult,
                )
                result.flag_dI_regExp = True

            return result

        else:
            return None

    def __getitem__(self, num):
        return self.listFuns[num]


class TypeObject:
    def __init__(self, **argv):
        """IN: (<attribute name> = <value>,)*
        The attributes define the type of the object.
        """

        if "mass" in argv:
            self.mass = argv["mass"]
        if "float" in argv:
            self.float = argv["float"]

        if "error" in argv:
            self.error = argv["error"]
        else:
            self.error = None

        if "polarity" in argv:
            self.polarity = argv["polarity"]
        if "sumComposition" in argv:
            self.sumComposition = argv["sumComposition"]

        if "elementSequence" in argv:
            self.elementSequence = lpdxParser.parseElemSeq(
                argv["elementSequence"]
            )
            # self.elementSequence = argv['elementSequence']
        else:
            self.elementSequence = lpdxChemsf.ElementSequence()

        if "retentionTime" in argv:
            self.retentionTime = argv["retentionTime"]
        else:
            self.retentionTime = None  # ordered float

        if "scope" in argv:
            self.scope = argv["scope"]
        else:
            self.scope = None  # r'MS[12][+-]'

        if "hasMSMS" in argv:
            self.hasMSMS = argv["hasMSMS"]
        else:
            self.hasMSMS = None

        if "sfconstraint" in argv:
            self.sfconstraint = argv["sfconstraint"]
        else:
            self.sfconstraint = None

        if "intensity" in argv:
            self.intensity = argv["intensity"]
        else:
            self.intensity = None  # ordered float or dictionary

        if "relIntensity" in argv:
            self.relIintensity = argv["relIintensity"]
        else:
            self.relIintensity = None  # ordered float or dictionary

        if "neutralPart" in argv:
            self.neutralPart = argv["neutralPart"]
        if "chargedPart" in argv:
            self.chargedPart = argv["chargedPart"]

        if "variable" in argv:
            self.variable = argv["variable"]
        else:
            self.variable = None

        if "varcontent" in argv:
            self.varcontent = argv["varcontent"]
        else:
            self.varcontent = None

        if "tolerance" in argv:
            self.tolerance = argv["tolerance"]
        else:
            self.tolerance = None

        if "attribute" in argv:
            self.attribute = argv["attribute"]
        else:
            self.attribute = None

        if "item" in argv:
            self.item = argv["item"]
        else:
            self.item = None

        self.options = {}


class TypeString(TypeObject):
    def __init__(self, string):
        self.string = string
