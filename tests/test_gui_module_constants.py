"""`lx.gui.lpdxGUI.playSound` must be bound on every platform, including
macOS.

`platform.system()` reports 'Darwin' on macOS, which matched none of the
LINUX/CYGWIN_NT/WINDOWS branches that used to be the only places binding
`playSound`. That left the name unbound after import on macOS, so any of
the module's 9 `if playSound:` reads raised NameError the first time a
user hit the matching button -- silently, since the packaged .app has no
console.

This test imports wx (via lx.gui.lpdxGUI), which works locally and under
CI's xvfb-run, but needs a display; it is not meant to run headless with
no X server / no Xvfb at all.
"""

import lx.gui.lpdxGUI as lpdxGUI


def test_play_sound_is_bound_and_boolean():
    assert hasattr(lpdxGUI, "playSound"), (
        "playSound is unbound -- this reproduces the macOS NameError, since "
        "platform.system() == 'Darwin' matches none of the LINUX/CYGWIN_NT/"
        "WINDOWS branches that used to be the only places assigning it"
    )
    assert isinstance(lpdxGUI.playSound, bool)
