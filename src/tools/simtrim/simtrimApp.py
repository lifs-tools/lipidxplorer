import os
import signal
import sys

from tools.simtrim.simtrim import *
from gooey import Gooey, GooeyParser


@Gooey
def main():
    parser = GooeyParser(description="trim the sims from a spectra.")

    parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        help="spectra file with sims",
        metavar="files",
        widget="MultiFileChooser",
    )

    parser.add_argument(
        "-d",
        "--da",
        metavar="custom dalton size to trim",
        action="store",
        type=float,
        default=0,
        help="trim these many daltons from sim, zero to calculate myself",
    )

    parser.add_argument(
        "-s",
        "--start",
        metavar="start of retention time",
        action="store",
        type=float,
        default=0,
        help="time in minutes from where to start the simtrim",
    )

    parser.add_argument(
        "-e",
        "--end",
        metavar="end of retention time",
        action="store",
        type=float,
        default=float("inf"),
        help="time in minutes where to end simtrim",
    )

    args = parser.parse_args()
    for file in args.files:
        try:
            simtrim(
                file,
                args.da,
                start_rt=float(args.start),
                stop_rt=float(args.end),
            )
        except Exception as e:
            print(f"Could not process {file}")
            print(repr(e))


def simtrimTask():
    print("simtrim")
    import time
    import subprocess as sp

    sp.Popen(
        "simtrimApp.py",
        creationflags=sp.DETACHED_PROCESS | sp.CREATE_NEW_PROCESS_GROUP,
        start_new_session=True,
        stdout=sp.DEVNULL,
        stderr=sp.STDOUT,
    )


def openSimtrim():
    simtrimTask()


if __name__ == "__main__" or __name__ == "tools.simtrim.simtrimApp":
    main()
