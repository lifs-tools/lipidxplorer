"""The "... %.2f sec." progress lines must report a duration, not a clock.

Under Python 2 these used time.clock(), which on Windows counted from its own
first call -- so the bare call at the top of startParsing() acted as a reset
and every later call returned elapsed time. time.perf_counter() has a fixed
arbitrary epoch instead, so after the migration the reset did nothing and
every line printed the raw counter: on a machine up for a week, lines read
"IDENTIFY the masses of interest ... 657120.63 sec.".

Importing mfqlParser builds the yacc parser, as the application does.
"""

import time

import pytest

from lx.mfql import mfqlParser


@pytest.fixture
def reset_parse_start():
    saved = mfqlParser._parse_start
    yield
    mfqlParser._parse_start = saved


def test_elapsed_is_zero_before_parsing_starts(reset_parse_start):
    mfqlParser._parse_start = None

    assert mfqlParser._elapsed() == 0.0


def test_elapsed_is_a_duration_not_a_clock_reading(reset_parse_start):
    mfqlParser._parse_start = time.perf_counter()

    elapsed = mfqlParser._elapsed()

    # The bug printed time.perf_counter() itself -- boot-relative, so tens or
    # hundreds of thousands of seconds on any machine with real uptime.
    assert 0.0 <= elapsed < 1.0, f"looks like a raw counter, not a duration: {elapsed}"


def test_elapsed_grows_with_real_time(reset_parse_start):
    mfqlParser._parse_start = time.perf_counter()
    first = mfqlParser._elapsed()
    time.sleep(0.05)
    second = mfqlParser._elapsed()

    assert second > first
    assert second == pytest.approx(first + 0.05, abs=0.04)


def test_every_progress_line_uses_the_helper():
    """Guards against a raw perf_counter() creeping back into a print."""
    source = open(mfqlParser.__file__, encoding="utf-8").read()

    offenders = [
        line.strip()
        for line in source.splitlines()
        if "print(" in line and "time.perf_counter()" in line
    ]

    assert offenders == [], offenders
