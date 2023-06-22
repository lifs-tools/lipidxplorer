# Parsers
(
    NAME,
    NUM,
    EOS,
    SP,
    NUMPAREN,
    RANGE,
    ENUM,
    SLPAREN,
    SRPAREN,
    SIMI,
    DB,
    CHARGE,
) = list(range(12))

import re
from copy import deepcopy

# from lx.exceptions import SyntaxErrorException
from chemsc import (
    ElementSequence,
    sym2elt,
    RangeElement,
    ConstElement,
    SCConstraint,
)

_lexer = re.compile(
    r"[A-Z][a-wyz]*|\d+|[\{\}]|<EOS>|\s|\[\d{1,6}\.\.\d{1,6}\]|\[\d{1,6}(,\d{1,6})*\]|;|db\([-+]?\d{1,3}(\.\d{1,4})?,[+-]?\d{1,3}(\.\d{1,4})?\)|chg\([+-]?\d\)"
).match


class Tokenizer:
    def __init__(self, input):
        self.input = input + "<EOS>"
        self.i = 0

    def gettoken(self):
        global ttype, tvalue
        self.lasti = self.i

        m = _lexer(self.input, self.i)

        if m is None:
            self.error("Syntax Error: unexpected character" + repr(self.i))
        self.i = m.end()
        tvalue = m.group()
        if tvalue == "{":
            ttype = SLPAREN
        elif tvalue == "}":
            ttype = SRPAREN
        elif tvalue == ";":
            ttype = SIMI
        elif tvalue == "<EOS>":
            ttype = EOS
        elif "0" <= tvalue[0] <= "9":
            ttype = NUM
            tvalue = int(tvalue)
        elif tvalue == " ":
            ttype = SP
        elif re.compile(
            "\s?db\([-+]?\d{1,3}(\.\d{1,4})?,[+-]?\d{1,3}(\.\d{1,4})?\)"
        ).match(tvalue):
            ttype = DB
        elif re.compile("\s?chg\([+-]?\d\)").match(tvalue):
            ttype = CHARGE
        elif re.compile("\[\d{1,6}\]").match(tvalue):
            ttype = NUMPAREN
        elif re.compile("\[\d{1,6}\.\.\d{1,6}\]").match(tvalue):
            ttype = RANGE
        elif re.compile("\[\d{1,6}(,\d{1,6})*\]").match(tvalue):
            ttype = ENUM
        else:
            ttype = NAME

    def error(self, msg):
        emsg = msg + ":\n"
        emsg = emsg + self.input[:-5] + "\n"  # strip <EOS>
        emsg = emsg + " " * self.lasti + "^\n"
        raise ValueError(emsg)


def parseElemSeq(s):
    global t, ttype, tvalue
    t = Tokenizer(s)
    t.gettoken()
    seq = parse_sequence()
    if ttype != EOS:
        t.error("expected end of input")
    return seq


def parse_sequence():
    global t, ttype, tvalue
    seq = ElementSequence()
    zeroFlag = False
    isSFConstraint = False
    while ttype in (NAME, SP, RANGE, ENUM, DB, CHARGE):
        # parenthesized expression or straight name
        if ttype == NAME:
            if tvalue in sym2elt:
                thisguy = deepcopy(sym2elt[tvalue])
            # thisguy.set_count(1)
            else:
                t.error("'" + tvalue + "' is not an element symbol")
            t.gettoken()
        # followed by optional count
        if ttype == RANGE:
            r = re.compile("\[(\d{1,6})\.\.(\d{1,6})\]").match(tvalue)
            if not thisguy:
                raise SyntaxErrorException(
                    "No space is allowed between an element and its count or range",
                    None,
                    None,
                    None,
                )
            thisguy.__class__ = RangeElement
            thisguy.set_range(int(r.group(1)), int(r.group(2)) + 1)
            isSFConstraint = True
            del r
            t.gettoken()
        if ttype == ENUM:
            l = []
            # r = re.compile("\[(\d+,\s*)+(\d+)\]").match(tvalue)
            r = re.compile("\[(\d{1,6})((,\d{1,6})*)\]").match(tvalue)
            l.append(int(r.groups()[0]))
            for i in r.group(2).split(","):
                if i != "":
                    l.append(int(i))
            if not thisguy:
                raise SyntaxErrorException(
                    "No space is allowed between an element and its count or range",
                    None,
                    None,
                    None,
                )
            thisguy.__class__ = RangeElement
            thisguy.set_enum(l)
            isSFConstraint = True
            del r
            t.gettoken()
        if ttype == NUM:
            if tvalue == 0:
                # set zeroFlag if NUM read is zero, so we need not to append the element
                zeroFlag = True
            else:
                if not thisguy:
                    raise SyntaxErrorException(
                        "No space is allowed between an element and its count or range",
                        None,
                        None,
                        None,
                    )
                thisguy.__class__ = ConstElement
                thisguy.set_count(tvalue)
            t.gettoken()
        if ttype == NUMPAREN:
            r = re.compile("\[(\d{1,6})\]").match(tvalue)
            v = int(r.groups()[0])
            if v == 0:
                # set zeroFlag if NUM read is zero, so we need not to append the element
                zeroFlag = True
            else:
                thisguy.__class__ = ConstElement
                thisguy.set_count(v)
            t.gettoken()
            del r
            del v
        if ttype == SP:
            t.gettoken()

        # add the element to the sum form
        if not zeroFlag:
            if thisguy:
                seq.append(thisguy)
            thisguy = None
            zeroFlag = False

        # after sum form there comes the optional options
        if ttype == DB:
            # if double bond range is given, it is a SCConstraint
            seq.__class__ = SCConstraint

            # to prevent the algorithm adding more elements
            zeroFlag = True
            match = re.compile(
                "\s?db\(([-+]?\d{1,3}\.\d{1,4}),([+-]?\d{1,3})\)"
            )
            if match.match(tvalue):
                r = match.match(tvalue)
                seq.set_db(float(r.group(1)), int(r.group(2)))
            match = re.compile("\s?db\(([-+]?\d{1,3}),([+-]?\d{1,3})\)")
            if match.match(tvalue):
                r = match.match(tvalue)
                seq.set_db(int(r.group(1)), int(r.group(2)))
            match = re.compile(
                "\s?db\(([-+]?\d{1,3}\.\d{1,4}),([+-]?\d{1,3}\.\d{1,4})\)"
            )
            if match.match(tvalue):
                r = match.match(tvalue)
                seq.set_db(float(r.group(1)), float(r.group(2)))
            match = re.compile(
                "\s?db\(([-+]?\d{1,3}),([+-]?\d{1,3}\.\d{1,4})\)"
            )
            if match.match(tvalue):
                r = match.match(tvalue)
                seq.set_db(int(r.group(1)), float(r.group(2)))
            t.gettoken()
        if ttype == CHARGE:
            # to prevent the algorithm adding more elements
            zeroFlag = True
            r = re.compile("chg\(([+-]?\d)\)").match(tvalue)
            seq.set_charge(int(r.group(1)))
            t.gettoken()
    if len(seq) == 0:
        t.error("empty sequence")

    if isSFConstraint:
        seq.__class__ = SCConstraint
        for i in seq._seq:
            if not seq._seq[i].__class__ == RangeElement:
                seq._seq[i].__class__ = RangeElement
                seq._seq[i].set_count(seq._seq[i]._count)

    return seq


if __name__ == "__main__":
    res = parseElemSeq("C[30..80] H[40..300] O[10] N[1] P[1]")
    print(res["H"])
