"""Syntax check of an MFQL query, without spectra and without running it.

Used by the MFQL editor to mark errors while typing and when saving.

The grammar is not copied: it is taken at import time from lx.mfql.mfqlParser
(its tokens, lexer rules, precedence and the grammar docstrings of every p_*
rule), so this check always accepts exactly what the real parser accepts.
Only the actions are replaced: they build nothing and touch no global state,
which means a check can run at any time, also while a query is running.

On top of the pure grammar, the checks that the real run would otherwise only
report after loading spectra are repeated here, with the same wording:
  * sum composition strings ('C[30..50] H[40..100] ...') must parse
  * tolerance values must be > 0
  * the old "IDENTIFY <name> WHERE" form is rejected
  * every variable used with IN must be DEFINEd
  * every DEFINEd variable must be used in IDENTIFY
  * only one query per file
  * no underscore characters
Characters the lexer cannot read are reported as warnings, because the real
run skips them too.

    problems = check(text)        # [] if the query is fine
    for p in problems:
        print(p.line, p.column, p.severity, p.message)
"""
import re
import threading

from ply import lex, yacc

from lx.mfql import mfqlParser as _grammar
from lx.mfql.chemParser import parseElemSeq


class MFQLProblem:
    """One problem found in a query.

    offset/length are character positions in the checked text; line and
    column are 1-based.
    """

    def __init__(self, message, offset, length, line, column, severity="error"):
        self.message = message
        self.offset = offset
        self.length = max(1, length)
        self.line = line
        self.column = column
        self.severity = severity

    def __repr__(self):
        return "MFQLProblem(line %d, col %d, %s: %s)" % (
            self.line, self.column, self.severity, self.message)


class _Stop(Exception):
    """Raised by the rules to end the check at the first error."""


class _Var:
    """A variable name as it appears in the query, with its position."""

    def __init__(self, name, offset):
        self.name = name
        self.offset = offset


# --------------------------------------------------------------- state ----

class _Run:
    """Everything belonging to one check() call."""

    def __init__(self, text):
        self.text = text
        self.problems = []
        self.query_name = None
        self.num_queries = 0
        self.defined = {}       # name -> offset of the DEFINE name
        self.used = set()

    def add(self, message, offset, length=1, severity="error"):
        line, column = _line_col(self.text, offset)
        self.problems.append(MFQLProblem(message, offset, length, line, column, severity))

    def stop(self, message, offset, length=1):
        self.add(message, offset, length)
        raise _Stop()


_run = None                     # the _Run of the check in progress
_lock = threading.Lock()

_LINE_BREAK = re.compile(r"\r\n|\r|\n")


def _line_col(text, offset):
    offset = max(0, min(offset, len(text)))
    line, start = 1, 0
    for m in _LINE_BREAK.finditer(text, 0, offset):
        line += 1
        start = m.end()
    return line, offset - start + 1


# --------------------------------------------------------------- lexer ----

class _LexerSpec:
    pass


def _t_UNDERSCORE(t):
    r'_'
    _run.stop("No underscore allowed.", t.lexpos)


def _t_error(t):
    ch = t.value[0]
    if ch not in "\r":
        _run.add("Illegal character '%s' (it is ignored when the query runs)." % ch,
                 t.lexpos, 1, "warning")
    t.lexer.skip(1)


# ply looks the rule functions up by their __name__
_t_UNDERSCORE.__name__ = "t_UNDERSCORE"
_t_error.__name__ = "t_error"


def _build_lexer():
    spec = _LexerSpec()
    spec.tokens = _grammar.tokens
    for name in dir(_grammar):
        if not name.startswith("t_"):
            continue
        value = getattr(_grammar, name)
        if name == "t_UNDERSCORE":
            value = _t_UNDERSCORE
        elif name == "t_error":
            value = _t_error
        setattr(spec, name, value)
    return lex.lex(module=spec, reflags=re.I, debug=False, optimize=False,
                   errorlog=lex.NullLogger())


# -------------------------------------------------------------- parser ----

def _value(p):
    return p[1] if len(p) > 1 else None


def _action(name, p):
    """Replacement for every p_* rule of mfqlParser."""
    run = _run

    if name in ("p_onlyObj_ID", "p_onlyObj_ID_itemAccess", "p_withAttr_id",
                "p_withAttr_accessItem_", "p_withAttr_accessItem_string"):
        p[0] = _Var(p[1], p.lexpos(1))
        return

    if name == "p_getQueryName":
        run.query_name = p[1]
        run.defined = {}
        run.used = set()
        return

    if name == "p_scriptname":
        run.num_queries += 1
        if run.num_queries > 1:
            run.stop("There is only one query per *.mfql file allowed!", p.lexpos(1), len(p[1]))
        return

    if name in ("p_var_normal", "p_var_emptyVar"):
        run.defined.setdefault(p[2], p.lexpos(2))
        return

    if name == "p_varcontent_sfstring":
        formula = p[1].strip("'")
        try:
            parseElemSeq(formula)
        except Exception as e:      # ValueError / SyntaxErrorException from chemParser
            run.stop(*_formula_error(e, formula, p.lexpos(1) + 1))
        p[0] = p[1]
        return

    if name == "p_tolerancetype":
        if float(p[1]) <= 0.0:
            run.stop("Tolerance value as given in the query '%s' can not be smaller or equal zero"
                     % (run.query_name or ""), p.lexpos(1), len(str(p[1])))
        p[0] = p[1]
        return

    if name == "p_identification_normal_old":
        run.stop("Please remove the query name after 'IDENTIFY'. This is not supported anymore.",
                 p.lexpos(2), len(str(p[2])))

    if name == "p_scan_object":
        obj = p[1]
        if not isinstance(obj, _Var):
            run.stop("Only a DEFINEd variable can be used with IN.", p.lexpos(2), len(p[2]))
        if obj.name not in run.defined:
            run.stop("Variable \"%s\" in query \"%s\" does not exist."
                     % (obj.name, run.query_name or ""), obj.offset, len(obj.name))
        run.used.add(obj.name)
        p[0] = obj
        return

    if name == "p_marks":
        for var, offset in run.defined.items():
            if var not in run.used:
                run.stop("The variable '%s' in query '%s' has to be used in IDENTIFY"
                         % (var, run.query_name or ""), offset, len(var))
        return

    p[0] = _value(p)


def _formula_error(exc, formula, start):
    """Message, offset and length for an error from chemParser.parseElemSeq."""
    detail = getattr(exc, "p_value", None)
    if detail:
        return "Invalid sum composition '%s': %s" % (formula, detail), start, len(formula)
    lines = str(exc).splitlines()
    first = re.sub(r"character\d+:?$", "character", lines[0].strip()) if lines else ""
    first = first.replace("Syntax Error: ", "")
    # chemParser marks the position with a caret line: "    ^"
    caret = next((l.index("^") for l in lines if l.strip() == "^"), None)
    if caret is not None and caret < len(formula):
        if first.endswith("unexpected character"):
            first += " '%s'" % formula[caret]
        return "Invalid sum composition '%s': %s" % (formula, first), start + caret, 1
    return "Invalid sum composition '%s': %s" % (formula, first), start, len(formula)


def _p_error(tok):
    if tok is None:
        _run.stop("Unexpected end of the query. Is the final ';' missing?",
                  max(0, len(_run.text.rstrip()) - 1))
    value = str(tok.value)
    message = "Syntax error at '%s'." % value
    # Most common mistake: a line that does not end with ';'. Then the error
    # is reported at the first word of the next line.
    text = _run.text
    line_start = max(text.rfind("\n", 0, tok.lexpos), text.rfind("\r", 0, tok.lexpos)) + 1
    before = text[:tok.lexpos].rstrip()
    if not text[line_start:tok.lexpos].strip() and before and not before.endswith(";"):
        message += " Is the ';' missing at the end of the line before?"
    _run.stop(message, tok.lexpos, len(value))


def _make_rule(name, original):
    def rule(p):
        _action(name, p)
    rule.__doc__ = original.__doc__
    rule.__name__ = name
    # Same line number as the original rule: ply orders rules by line, and
    # that order decides how grammar conflicts are resolved.
    rule.__code__ = rule.__code__.replace(co_firstlineno=original.__code__.co_firstlineno)
    return rule


class _ParserSpec:
    pass


def _build_parser():
    spec = _ParserSpec()
    spec.tokens = _grammar.tokens
    spec.precedence = _grammar.precedence
    spec.start = "program"
    for name in dir(_grammar):
        if name.startswith("p_") and name != "p_error":
            original = getattr(_grammar, name)
            if callable(original) and original.__doc__:
                setattr(spec, name, _make_rule(name, original))
    spec.p_error = _p_error
    return yacc.yacc(module=spec, debug=False, write_tables=False, optimize=False,
                     errorlog=yacc.NullLogger())


_lexer = None
_parser = None


def _ensure_built():
    global _lexer, _parser
    if _parser is None:
        _lexer = _build_lexer()
        _parser = _build_parser()


# --------------------------------------------------------------- API ------

def _only_comments(text):
    return all(not line.strip() or line.lstrip().startswith("#")
               for line in _LINE_BREAK.split(text))


def check(text):
    """Return a list of MFQLProblem for the query text (empty list: no problem).

    The check stops at the first error; warnings found before it are kept.
    """
    global _run
    if _only_comments(text):
        return []                   # new, empty file: nothing to complain about
    with _lock:
        _ensure_built()
        _run = _Run(text)
        try:
            _lexer.lineno = 1
            _parser.parse(text, lexer=_lexer, tracking=True)
        except _Stop:
            pass
        finally:
            problems, _run = _run.problems, None
    problems.sort(key=lambda p: (p.severity != "error", p.offset))
    return problems
