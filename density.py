import argparse
from density_hist import Density

parser = argparse.ArgumentParser()
parser.add_argument('file',     help = 'Density file created by nutbar')
parser.add_argument('-i', '--inverted', action ='store_true', default=False, help='Invert the sign of the values to make comparing easier')
args = parser.parse_args()

Bar_plot = Density(args.file, args.inverted)
Bar_plot.plot()