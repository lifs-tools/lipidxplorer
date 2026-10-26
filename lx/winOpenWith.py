"""Put LipidXplorer into the Windows "Open with" menu for .mfql files.

LipidXplorer is not installed: it is a folder with LipidXplorer.exe that can
live anywhere. So the exe registers itself, for the current user only
(HKEY_CURRENT_USER, no admin rights), every time it starts. If the exe was
moved, the next start updates the path. Nothing is written when the entries
are already correct.

What the user gets: right-click an .mfql file > Open with > LipidXplorer.
It is NOT made the default program for .mfql; double-click keeps doing what
it did before (if .mfql has no default program yet, Windows asks and lists
LipidXplorer there).

Keys written, all under HKCU\\Software\\Classes:
    Applications\\<exe name>\\shell\\open\\command     "<exe>" "%1"
    Applications\\<exe name>\\FriendlyAppName          LipidXplorer
    Applications\\<exe name>\\SupportedTypes           .mfql
    Applications\\<exe name>\\DefaultIcon              "<exe>",0
    LipidXplorer.MFQL\\shell\\open\\command             "<exe>" "%1"
    LipidXplorer.MFQL                                (default) MFQL query file
    LipidXplorer.MFQL\\DefaultIcon                    "<exe>",0
    .mfql\\OpenWithProgids                           LipidXplorer.MFQL

Only runs in the packaged exe on Windows; does nothing when started from
the Python sources or on another OS.
"""
import os
import sys

PROGID = "LipidXplorer.MFQL"
CLASSES = r"Software\Classes"


def _wanted_values(exe):
    app = os.path.basename(exe)
    command = '"%s" "%%1"' % exe
    icon = '"%s",0' % exe
    return [
        # (key, value name, data)
        (CLASSES + r"\Applications\%s\shell\open\command" % app, "", command),
        (CLASSES + r"\Applications\%s" % app, "FriendlyAppName", "LipidXplorer"),
        (CLASSES + r"\Applications\%s\SupportedTypes" % app, ".mfql", ""),
        (CLASSES + r"\Applications\%s\DefaultIcon" % app, "", icon),
        (CLASSES + "\\" + PROGID, "", "MFQL query file"),
        (CLASSES + "\\" + PROGID + r"\shell\open\command", "", command),
        (CLASSES + "\\" + PROGID + r"\DefaultIcon", "", icon),
        (CLASSES + r"\.mfql\OpenWithProgids", PROGID, ""),
    ]


def register_open_with(exe=None, winreg=None):
    """Write the "Open with" entries if needed. Returns True if anything changed.

    Never raises: a failure only means LipidXplorer is missing from the menu.
    """
    if winreg is None:
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            return False
        import winreg
    exe = os.path.abspath(exe or sys.executable)
    changed = False
    try:
        for key, name, data in _wanted_values(exe):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
                    current = winreg.QueryValueEx(k, name)[0]
            except OSError:
                current = None
            if current != data:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key, 0,
                                        winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, data)
                changed = True
        if changed and sys.platform == "win32":
            import ctypes
            SHCNE_ASSOCCHANGED, SHCNF_IDLIST = 0x08000000, 0x0000
            ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception as e:
        print("Could not add LipidXplorer to 'Open with' for .mfql files: %s" % e)
    return changed
