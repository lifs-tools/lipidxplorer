import keyword

import wx
import wx.stc as stc

# ----------------------------------------------------------------------

demoText = """\
## This version of the editor has been set up to edit Python source
## code.  Here is a copy of wxPython/demo/Main.py to play with.


"""

# ----------------------------------------------------------------------


if wx.Platform == "__WXMSW__":
    faces = {
        "times": "Times New Roman",
        "mono": "Courier New",
        "helv": "Arial",
        "other": "Comic Sans MS",
        "size": 8,
        "size2": 8,
    }
elif wx.Platform == "__WXMAC__":
    faces = {
        "times": "Times New Roman",
        "mono": "Monaco",
        "helv": "Arial",
        "other": "Comic Sans MS",
        "size": 12,
        "size2": 10,
    }
else:
    faces = {
        "times": "Times",
        "mono": "Courier",
        "helv": "Helvetica",
        "other": "new century schoolbook",
        "size": 12,
        "size2": 10,
    }

keywords = [
    "DEFINE",
    "IDENTIFY",
    "SUCHTHAT",
    "REPORT",
    "WHERE",
    "WITH",
    "DBR",
    "CHG",
    "QUERYNAME",
    "IN",
    "AND",
    "OR",
    "%",
]

keywords.sort()


# ----------------------------------------------------------------------


class PythonSTC(stc.StyledTextCtrl):

    fold_symbols = 2

    def __init__(
        self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0
    ):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.CmdKeyAssign(ord("B"), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord("N"), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        self.SetLexer(stc.STC_LEX_PYTHON)
        # self.SetKeyWords(0, " ".join(keyword.kwlist))
        self.SetKeyWords(0, " ".join(keywords))

        # self.SetProperty("fold", "1")
        self.SetProperty("fold", "0")
        self.SetProperty("tab.timmy.whinge.level", "0")
        self.SetMargins(0, 0)

        self.SetViewWhiteSpace(False)
        # self.SetBufferedDraw(False)
        self.SetViewEOL(False)
        self.SetEOLMode(stc.STC_EOL_CRLF)
        # self.SetUseAntiAliasing(True)

        # self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        # self.SetEdgeColumn(78)
        self.SetEdgeMode(stc.STC_EDGE_NONE)

        # Setup a margin to hold fold markers
        # self.SetFoldFlags(16)  ###  WHAT IS THIS VALUE?  WHAT ARE THE OTHER FLAGS?  DOES IT MATTER?
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        if self.fold_symbols == 0:
            # Arrow pointing right for contracted folders, arrow pointing down for expanded
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_ARROWDOWN, "black", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDER, stc.STC_MARK_ARROW, "black", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, "black", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, "black", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, "white", "black"
            )

        elif self.fold_symbols == 1:
            # Plus for contracted folders, minus for expanded
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_MINUS, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDER, stc.STC_MARK_PLUS, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY, "white", "black"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, "white", "black"
            )

        elif self.fold_symbols == 2:
            # Like a flattened tree control using circular headers and curved joins
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_CIRCLEMINUS, "white", "#404040"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDER, stc.STC_MARK_CIRCLEPLUS, "white", "#404040"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "#404040"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERTAIL,
                stc.STC_MARK_LCORNERCURVE,
                "white",
                "#404040",
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEREND,
                stc.STC_MARK_CIRCLEPLUSCONNECTED,
                "white",
                "#404040",
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPENMID,
                stc.STC_MARK_CIRCLEMINUSCONNECTED,
                "white",
                "#404040",
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERMIDTAIL,
                stc.STC_MARK_TCORNERCURVE,
                "white",
                "#404040",
            )

        elif self.fold_symbols == 3:
            # Like a flattened tree control using square headers
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, "white", "#808080"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, "white", "#808080"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "#808080"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, "white", "#808080"
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEREND,
                stc.STC_MARK_BOXPLUSCONNECTED,
                "white",
                "#808080",
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPENMID,
                stc.STC_MARK_BOXMINUSCONNECTED,
                "white",
                "#808080",
            )
            self.MarkerDefine(
                stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, "white", "#808080"
            )

        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        # Make some styles,  The lexer defines what each style is used for, we
        # just have to define what each style looks like.  This set is adapted from
        # Scintilla sample property files.

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(
            stc.STC_STYLE_LINENUMBER,
            "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces,
        )
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(
            stc.STC_P_DEFAULT, "fore:#000000,face:%(helv)s,size:%(size)d" % faces
        )
        # Comments
        # self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(other)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#2F9F2F,size:%(size)d" % faces)
        # Number
        # self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#2F5F5F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(
            stc.STC_P_STRING, "fore:#7F3F7F,face:%(helv)s,size:%(size)d" % faces
        )
        # Single quoted string
        self.StyleSetSpec(
            stc.STC_P_CHARACTER, "fore:#AF8F00,face:%(helv)s,size:%(size)d" % faces
        )
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(
            stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces
        )
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(stc.STC_C_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(
            stc.STC_P_IDENTIFIER, "fore:#000000,face:%(helv)s,size:%(size)d" % faces
        )
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#5F9F5F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(
            stc.STC_P_STRINGEOL,
            "fore:#000000,face:%(helv)s,back:#CFCFCF,eol,size:%(size)d" % faces,
        )

        self.SetCaretForeground("BLACK")

        # for auto completion
        self.nb_of_letters = 0

    def OnKeyPressed(self, event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()

        # is in [A-Za-z] ?
        if not event.ControlDown() and (
            (key >= 65 and key <= 90) or (key >= 97 and key <= 122)
        ):
            self.nb_of_letters += 1

        # is space, shift or ctrl (do nothing)
        elif key == 32 or key == 306 or key == 308:
            pass

        # is ctrl + letter (do nothing)
        elif event.ControlDown() and (
            (key >= 65 and key <= 90) or (key >= 97 and key <= 122)
        ):
            pass

        # all other cases (reset counter)
        else:
            self.nb_of_letters = 0

        self.AutoCompSetChooseSingle(False)
        if key == 32 and event.ControlDown():  # space and ctrl
            pos = self.GetCurrentPos()

            # Tips
            if event.ShiftDown():
                self.CallTipSetBackground("yellow")
                self.CallTipShow(
                    pos,
                    "lots of of text: blah, blah, blah\n\n"
                    "show some suff, maybe parameters..\n\n"
                    "fubar(param1, param2)",
                )
            # Code completion
            else:
                self.AutoCompShow(self.nb_of_letters, " ".join(keywords))

        elif key == 104 and event.ControlDown():  # 'h' and ctrl
            pos = self.GetCurrentPos()
            l = self.GetCurLine()
            if "DEFINE" in l[0]:
                self.CallTipShow(
                    pos + 4,
                    "lots of of text: blah, blah, blah\n\n"
                    "show some suff, maybe parameters..\n\n"
                    "fubar(param1, param2)",
                )
        else:
            event.Skip()

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if (
            charBefore
            and chr(charBefore) in "[]{}()"
            and styleBefore == stc.STC_P_OPERATOR
        ):
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if (
                charAfter
                and chr(charAfter) in "[]{}()"
                and styleAfter == stc.STC_P_OPERATOR
            ):
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1 and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)
            # pt = self.PointFromPosition(braceOpposite)
            # self.Refresh(True, wxRect(pt.x, pt.y, 5,5))
            # print pt
            # self.Refresh(False)

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if (
                level & stc.STC_FOLDLEVELHEADERFLAG
                and (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE
            ):

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum + 1, lastChild)

            lineNum = lineNum + 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels - 1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels - 1)
                    else:
                        line = self.Expand(line, False, force, visLevels - 1)
            else:
                line = line + 1

        return line


# ----------------------------------------------------------------------

_USE_PANEL = 1
