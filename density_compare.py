import argparse
from density_hist import Density
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('file1',     help = 'Density file created by nutbar')
parser.add_argument('file2',     help = 'Density file created by nutbar')
parser.add_argument('-i1', '--inverted1', action ='store_true', default=False, help='Invert the sign of the values to make comparing easier')
parser.add_argument('-i2', '--inverted2', action ='store_true', default=False, help='Invert the sign of the values to make comparing easier')
args = parser.parse_args()

Bar_plot1 = Density(args.file1, args.inverted1)
Bar_plot2 = Density(args.file2, args.inverted2)

width = 0.35  # the width of the bars
Bar_plot1.bars.reset_index(inplace=True)
Bar_plot2.bars.reset_index(inplace=True)
fig, ax = plt.subplots()
rects1 = ax.bar(Bar_plot1.bars['J'] - width/2, Bar_plot1.bars['density'], width, label='EM(1.8/2.0)', color ='#e00543')
rects2 = ax.bar(Bar_plot2.bars['J'] + width/2, Bar_plot2.bars['density'], width, label=r'$NN+3N_{lnl}$', color ='#87a11f')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_xlabel('J', size = 14)
ax.set_ylabel(r'$M^{0\nu}$', size= 14)
ax.set_xticks(Bar_plot1.bars['J'])
ax.legend()
plt.axhline(color='k')

fig.tight_layout()

plt.show()