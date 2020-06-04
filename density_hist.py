import pandas as pd
import matplotlib.pyplot as plt

class Density():
  """Class to create an histogram of the density of the wf"""
  def __init__(self, file, invert=False):
    if invert == True:
      fac = -1
    else:
      fac = 1
    data = []
    with open(file,'r') as input:
      for line in input:
        if 'Two-body' in line:
          basis = {}
          for line in input:
            try:
              i,vector = self.read_basis(line)
              basis[i] = vector
            except:
              pass
            if 'TBTD' in line:
              for line in input:
                try:
                  i, density = self.read_i_density(line)
                except:
                  break
                for key in [*basis]:
                  if key == i:
                    point = [basis[key][2],fac*density]
                    break
                data.append(point)
    columns = ['J', 'density']
    self.df = pd.DataFrame(data)
    self.df.columns = columns
    self.bars = self.df.groupby('J').agg('sum')


  def read_basis(self, line):
    line_list = line.split()
    i = int(line_list[0])
    a = int(line_list[1])
    b = int(line_list[2])
    J = int(line_list[3])
    return i,[a,b,J]

  def read_i_density(self,line):
    line_list = line.split()
    i       = line_list[0]
    density = line_list[2]
    return int(i),float(density)

  def plot(self):
    bars = self.bars
    bars.reset_index(inplace=True)
    plt.bar(bars['J'], bars["density"])
    plt.axhline(color='k')
    plt.legend()
    plt.xlabel('J')
    plt.ylabel("NME")
    plt.show()