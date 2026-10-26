"""Show MFQL syntax problems inside an editor tab (wx.stc.StyledTextCtrl).

    mfqlSyntaxMarks.setup(ctrl)          # once, after creating the control
    problems = mfqlSyntaxMarks.check_ctrl(ctrl)   # check and (re)draw marks

Errors get a red wavy underline and a red box under the line with the
message; warnings the same in orange. The marks are not part of the text,
so they never change the file or its "modified" state.
"""
import wx
import wx.stc as stc

from lx.mfql.syntaxParser import checkText as check

INDIC_ERROR = 8                 # 0-7 may be used by lexers
INDIC_WARNING = 9
STYLE_ERROR = 60                # styles used for the annotation boxes
STYLE_WARNING = 61


def setup(ctrl):
    ctrl.IndicatorSetStyle(INDIC_ERROR, stc.STC_INDIC_SQUIGGLE)
    ctrl.IndicatorSetForeground(INDIC_ERROR, wx.Colour(220, 0, 0))
    ctrl.IndicatorSetStyle(INDIC_WARNING, stc.STC_INDIC_SQUIGGLE)
    ctrl.IndicatorSetForeground(INDIC_WARNING, wx.Colour(230, 140, 0))
    size = ctrl.StyleGetSize(stc.STC_STYLE_DEFAULT) or 9
    ctrl.StyleSetSpec(STYLE_ERROR, "fore:#A00000,back:#FFEBEB,size:%d" % size)
    ctrl.StyleSetSpec(STYLE_WARNING, "fore:#8A5300,back:#FFF4E0,size:%d" % size)
    ctrl.AnnotationSetVisible(stc.STC_ANNOTATION_BOXED)


def _clear(ctrl):
    length = ctrl.GetLength()
    for indic in (INDIC_ERROR, INDIC_WARNING):
        ctrl.SetIndicatorCurrent(indic)
        ctrl.IndicatorClearRange(0, length)
    ctrl.AnnotationClearAll()


def is_drawing(ctrl):
    """True while marks are being drawn.

    Drawing indicators and annotations fires EVT_STC_CHANGE just like typing
    does (and the event cannot tell them apart), so the change handler must
    ignore events while this is True.
    """
    return getattr(ctrl, "_mfqlDrawing", False)


def show(ctrl, text, problems):
    """Draw problems found in text (= ctrl.GetText() at check time)."""
    ctrl._mfqlDrawing = True
    try:
        _draw(ctrl, text, problems)
    finally:
        ctrl._mfqlDrawing = False


def clear(ctrl):
    ctrl._mfqlDrawing = True
    try:
        _clear(ctrl)
    finally:
        ctrl._mfqlDrawing = False


def _draw(ctrl, text, problems):
    _clear(ctrl)
    if not problems:
        return
    notes = {}                  # line -> (style, [messages])
    for p in problems:
        # stc positions count UTF-8 bytes, the checker counts characters
        start = len(text[:p.offset].encode("utf-8"))
        length = len(text[p.offset:p.offset + p.length].encode("utf-8")) or 1
        is_error = p.severity == "error"
        ctrl.SetIndicatorCurrent(INDIC_ERROR if is_error else INDIC_WARNING)
        ctrl.IndicatorFillRange(start, length)
        line = ctrl.LineFromPosition(start)
        style, messages = notes.setdefault(line, [STYLE_WARNING, []])
        if is_error:
            notes[line][0] = STYLE_ERROR
        label = "Error" if is_error else "Warning"
        messages.append("%s (line %d): %s" % (label, line + 1, p.message))
    for line, (style, messages) in notes.items():
        ctrl.AnnotationSetText(line, "\n".join(messages))
        ctrl.AnnotationSetStyle(line, style)


def check_ctrl(ctrl):
    """Check the control's text, draw the marks, return the problems."""
    text = ctrl.GetText()
    problems = check(text)
    show(ctrl, text, problems)
    return problems
