from lx1_refactored import sim_trim
from gooey import Gooey, GooeyParser


@Gooey
def main():
    parser = GooeyParser(description='trim the sims from a spectra.')

    parser.add_argument(
        'spectra file with sims',
        metavar='file',
        widget='FileChooser')

    parser.add_argument(
        '-d', '--da',
        metavar='custom dalton size to trim',
        action='store',
        default = 0,
        help='trim these many daltons from sim, zero to calculate myself')

    args = parser.parse_args()
    sim_trim.simtrim(args.file, args.da)
    

if __name__ == "__main__":
    main()
