##plot.py
##  By: Antoine Belley
##  Copyright (C): 2019
##DESCRIPTION
##  Module to make plotting easier
##  Takes an arbritrary number on inputfile that need to be plotted in same figure
##  Note that the delimiter of the input file need to be a type white space (i.e any number of tabs of spaces)
##  Makes a pandas.dataframe to for the concanated data coming from the files


import pandas as pd 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.odr import *


class Dict_font:
  "Class that contains the infos for the fonts use in the plots"
  def __init__(self, family, weight, size):
    self.font = {'family': family,
                 'weight': weight,
                 'size': size,
                 }


class Label_font(Dict_font):
  "Subclass for the labels where the option color is added"
  def __init__(self, family, weight, size, color):
    Dict_font.__init__(self, family, weight, size)
    self.font['color']=color


class easy_plot:
  "Class for creating automatic plots after MNU calculation"

  def __init__(self, output_name, title = None, xlabel ='x', ylabel = 'y', 
               fontfamily = 'Times New Roman', 
               files = [], legends =[], usecols = []):
    self.name = output_name
    self.title = title
    self.xlabel = xlabel
    self.ylabel = ylabel
    self.family = fontfamily
    if len(files) == 0:
      raise IndexError
    else: 
      self.files = files
    self.legends = legends
    if len(self.legends) != len(self.files):
      print("Number of legends does not equal the number of files")
      print("Exiting...")
      exit(1)
    if len(usecols) == 2:       
      data = pd.read_csv(self.files[0], delim_whitespace = True, header = None, usecols=usecols)
      if len(self.files) != 1:
        for x in range(1,len(self.files)):
          df = pd.read_csv(self.files[x], delim_whitespace = True, header = None, usecols=usecols)
          data = pd.concat([data,df], axis = 1)
    else :
        data = pd.read_csv(self.files[0], delim_whitespace = True, header = None)
        if len(self.files) != 1:
          for x in range(1,len(self.files)):
            df = pd.read_csv(self.files[x], delim_whitespace = True, header = None)
            data = pd.concat([data,df], axis = 1)
    data.columns = pd.MultiIndex.from_product([self.legends,[self.xlabel,self.ylabel]])
    self.data_frame = pd.DataFrame(data)
    self.fig = plt.figure()
    self.set_fonts()
    self.set_ploting_fmt()
    self.set_scatter_fmt()
    self.set_error_fmt()


  def help(self):
    print("Class : easy_plot( output_name, title = None, xlabel ='x', ylabel = 'y',  fontfamily = 'Times New Roman', Files=[], Legends=[])")
    print("       DESCRIPTION:")
    print("                     Module to make plotting easier")
    print("")
    print("")
    print("       ARGUMENTS:")
    print("                    ~output_name(str): Name of the output file")
    print("                    ~title(str):       Name of the figure")
    print("                    ~xlabel(str):      Label of the x-axis")
    print("                    ~ylabel(str):      Label of the y-axis")
    print("                    ~fontfamily(str):  Font for the figure")
    print("                    ~files(list):      List of the files to be plotted")
    print("                    ~legends(list):    List of the legends of each line. Should be same len as files.")
    print("")
    print("")
    print("        METHODS:")
    print("                    ~show_data(*args): Prints the data frame containing the values of the inputed files)")
    print("                          Parameter: - *args(str): Files to print. Use 'all' to see the whole database")
    print("")
    print("                    ~get_Data_frame(*args): Return a pandas.DataFrame() containing the value of the inputed files)")
    print("                          Parameter: - *args(str): Files to return. Use 'all' to return the whole database")
    print("")
    print("                    ~set_title_font(weight='normal', color='black', size=18): Creates fontdict for the title)")
    print("                          Parameter: - weight(str):     [ 'normal' | 'bold' | 'heavy' | 'light' | 'ultrabold' | 'ultralight']")
    print("                                     - color(str):      any matplotlib color")
    print("                                     - size(float/str): [ size in points | relative size, e.g., 'smaller', 'x-large' ")
    print("")
    print("                    ~set_axes_font(weight='normal', color='black', size=18): Creates fontdict for the title)")
    print("                          Parameter: - weight(str):     [ 'normal' | 'bold' | 'heavy' | 'light' | 'ultrabold' | 'ultralight']")
    print("                                     - color(str):      any matplotlib color")
    print("                                     - size(float/str): [ size in points | relative size, e.g., 'smaller', 'x-large' ")
    print("")
    print("                    ~set_legend_font(weight='normal', size=18): Creates fontdict for the title)")
    print("                          Parameter: - weight(str):     [ 'normal' | 'bold' | 'heavy' | 'light' | 'ultrabold' | 'ultralight']")
    print("                                     - size(float/str): [ size in points | relative size, e.g., 'smaller', 'x-large' ")
    print("")
    print("                    ~set_plot(*args, rangex = None, rangey = None, show = False, grid = False, **kargs)")
    print("                          Parameter: - *args(str):    Files to plot. Use 'all' to plot the whole database")
    print("                                     - rangex(list):  Enter '[xmin,xmax]' to set limit on x-axis'")
    print("                                     - rangex(list):  Enter '[ymin,ymax]' to set limit on y-axis'")
    print("                                     - show(bool):    Set 'True' to see the plot in addition to saving it.")
    print("                                     - grid(bool):    Set 'True' to see add a grid.")
    print("                                     -**kargs: -color(list):     Input list of colors for each line")
    print("                                               -linestyle(list): Input list of linestyle for each line")


  def show_data(self,*args):
    if len(args) == 1 and list(args)[0] == 'all':
      print(self.data_frame)
    else: 
      dftoshow =[]
      for i in args:
        for j in range(len(self.legends)):
          if i == self.legends[j] or i ==  self.files[j]:
            dftoshow.append(self.legends[j])
      if len(args) != len(dftoshow):
        print('Some of the files pass where unknown...')
        print('Only showing the known ones!')
      print(self.data_frame[dftoshow])


  def get_DataFrame(self,*args):
    if len(args) == 1 and list(args)[0] == 'all':
      print(self.data_frame)
    else: 
      dftoshow =[]
      for i in args:
        for j in range(len(self.legends)):
          if i == self.legends[j] or i ==  self.files[j]:
            dftoshow.append(self.legends[j])
      if len(args) != len(dftoshow):
        print('Some of the files pass where unknown...')
        print('Only showing the known ones!')
      return self.data_frame[dftoshow]

       
  def set_title_font(self, weight='normal', color='black', size=18):
    title_font = Label_font(family = self.family, 
                            weight = weight, color = color, 
                            size = size)
    self.title_font = title_font.font


  def set_axes_font(self, weight='normal', color='black', size=14):
    axes_font = Label_font(family = self.family, 
                           weight = weight, color = color, 
                           size = size)
    self.axes_font = axes_font.font


  def set_legend_font(self, weight='normal', size=10):
    legend_font = Dict_font(family = self.family, 
                            weight = weight, size = size)
    self.legend_font = legend_font.font


  def set_fonts(self):
    self.set_title_font()
    self.set_axes_font()
    self.set_legend_font()


  def set_ploting_fmt(self, linestyle = None , linewidth = None, marker = None, 
                      color = None):
    args = locals()
    plot_fmt =[]
    for j in range(len(self.legends)):
      fmt = {}
      for option, value in args.items():
        if option != "self":
          if value != None:
            fmt[option] = value[j]
            print(fmt)
            plot_fmt.append(fmt)
    self.plot_fmt = plot_fmt


  def set_scatter_fmt(self,  marker = None, markeredgecolor = None ,
                      markeredgewidth = None, markerfacecolor = None ,
                      markerfacecoloralt = None, markersize = None):
    args = locals()
    scatter_fmt =[]
    for j in range(len(self.legends)):
      fmt = {}
      for option, value in args.items():
        if option != "self":
          if value != None:
            fmt[option] = value[j]
            print(fmt)
            scatter_fmt.append(fmt)
    self.scatter_fmt = scatter_fmt


  def set_error_fmt(self, ecolor = None, elinewidth = None,
                    color = None, linestyle = None , linewidth = None, 
                    marker = None, markeredgecolor = None ,
                    markeredgewidth = None, markerfacecolor = None,
                    markerfacecoloralt = None, markersize = None):
    args = locals()
    error_fmt =[]
    for j in range(len(self.legends)):
      fmt = {}
      for option, value in args.items():
        if option != "self":
          if value != None:
            fmt[option] = value[j]
            print(fmt)
            error_fmt.append(fmt)
    self.error_fmt = error_fmt


  def make_plot(self, *args):
    labels = list(zip(self.files,self.legends))
    for j in range(len(self.files)):
      xdata = self.data_frame[self.legends[j]][self.xlabel]
      ydata = self.data_frame[self.legends[j]][self.ylabel]
      try:
        fmt = self.plot_fmt[j]
      except IndexError:
        fmt = {}
      if len(args) == 1 and list(args)[0] == 'all':
        plt.plot(xdata, ydata,
                 label = self.legends[j], **fmt)   
      else:
        for i in args:
          if i == self.legends[j] or i ==  self.files[j]:
            plt.plot(xdata, ydata, 
                     label = labels[j][1],  **fmt)
     

  def make_scatter(self, *args):
    labels = list(zip(self.files,self.legends))
    loc_legends = []
    for j in range(len(self.files)):
      a = 'Data points for ' + self.legends[j] 
      loc_legends.append(a)
      xdata = self.data_frame[self.legends[j]][self.xlabel]
      ydata = self.data_frame[self.legends[j]][self.ylabel]
      try:
        fmt = self.scatter_fmt[j]
      except IndexError:
        fmt = {}
      if len(args) == 1 and list(args)[0] == 'all':
        plt.scatter(xdata,ydata,
                    label = loc_legends[j], **fmt)
      else:
        for i in args:
          if i == self.legends[j] or i ==  self.files[j]:
            plt.scatter(xdata, ydata,
                        label = labels[j][1], **fmt)


  def error_bars(self,*args, xerr,yerr, fmt=''):
    for j in range(len(self.files)):
      xdata = self.data_frame[self.legends[j]][self.xlabel]
      ydata = self.data_frame[self.legends[j]][self.ylabel]
      try:
        fmt = self.error_fmt[j]
      except IndexError:
        fmt = {}
      if len(args) == 1 and list(args)[0] == 'all':
          plt.errorbar(xdata, ydata, 
                       xerr = xerr, yerr = yerr , **fmt)
      else:
        for i in args:
          if i == self.legends[j] or i ==  self.files[j]:
            plt.errorbar(xdata, ydata, 
                         xerr = xerr, yerr = yerr, **fmt)


  def add_line(self, value, fmt={}):
    yline = []
    xline = self.data_frame[self.legends[0]][self.xlabel]
    for x in range(len(xline)):
      y = value
      yline.append(y)
    plt.plot(xline, yline, label = 'Exp = '+ str(value), **fmt)
    

  def plot(self, *args, xerr = None, yerr = None, rangex = None, rangey = None, 
           show = False, grid = False, line = None, path = None, option ='line'):
    if option == 'line':
      self.make_plot(*args)
    elif option == 'scatter':
      self.make_scatter(*args)
    elif option == "scatter_line": 
      self.make_plot(*args)
      self.make_scatter(*args)
    elif option == "error_bars":
      if xerr != None and yerr != None:
        self.error_bars(*args, xerr = xerr, yerr = yerr, fmt = 'none')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "line_error_bars":
      if xerr != None and yerr != None:
        self.error_bars(*args, xerr = xerr, yerr = yerr, fmt='-')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "scatter_error_bars":
      if xerr != None and yerr !=None:
        self.error_bars(*args, xerr = xerr, yerr = yerr, fmt ='o')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "line_scatter_error_bars":
      if xerr != None and yerr !=None:
        self.error_bars(*args, xerr = xerr, yerr = yerr, fmt = '-o')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    else:
      print('Option is not known...')
      print('Choose between: line, scatter, scatter_line')
    if line != None:
      self.add_line(line)
    if self.title != None:
      plt.title(self.title, fontdict = self.title_font)
    plt.xlabel(self.xlabel, fontdict = self.axes_font)
    plt.ylabel(self.ylabel, fontdict = self.axes_font)
    if rangex != None:
      plt.xlim(rangex)
    if rangey != None:
      plt.ylim(rangey)
    plt.legend(prop = self.legend_font)
    if grid == True:
      plt.grid()
    if show == True:
      plt.show()
    if path != None:
      self.fig.savefig(path+'/'+self.name+'.png')
    self.fig.savefig(self.name+'.png')


class easy_fit(easy_plot):
  "Subclass of easy_plot. Is used to do automatic fits of data"
  def __init__(self, output_name, function, title = None, xlabel ='x', 
               ylabel = 'y', fontfamily = 'Times New Roman', files = [], 
               legends =[], usecols = [],  xerr = None, yerr = None):
    easy_plot.__init__(self, output_name, title, xlabel, ylabel, 
                       fontfamily, files, legends, usecols)
    self.function = function
    self.xerr = xerr
    self.yerr = yerr
    self.set_fit_fmt()

  def make_fit(self,*args, p0):
    popt = []
    pcov = []
    for j in range(len(self.legends)):
      xdata = self.data_frame[self.legends[j]][self.xlabel]
      ydata = self.data_frame[self.legends[j]][self.ylabel]
      if self.xerr == None and self.yerr == None:
        if len(args) == 1 and list(args)[0] == 'all':
            fit, var = curve_fit(self.function, xdata, ydata, p0 = p0)
        else:
          for i in args:
            if i == self.legends[j] or i ==  self.files[j]:
              fit, var = curve_fit(self.function, xdata, ydata, p0 = p0)
      else:
        model = Model(self.function)
        if len(args) == 1 and list(args)[0] == 'all':
            data = RealData(x = xdata, y = ydata,
                            sx = self.xerr , sy = self.yerr)
        else:
          for i in args:
            if i == self.legends[j] or i ==  self.files[j]:
              data = RealData(x = xdata, y = ydata,
                              sx = self.xerr , sy = self.yerr)

        myodr  = ODR(data = data, model = model, beta0 = p0)
        output = myodr.run()
        popt   = output.beta
        pcov   = output.cov_beta
      popt.append(fit)
      pcov.append(var) 
    self.popt = popt
    self.pcov = pcov

  def set_fit_fmt(self, linestyle = None , linewidth = None, marker = None, 
                      color = None):
    args = locals()
    fit_fmt =[]
    for j in range(len(self.legends)):
      fmt = {}
      for option, value in args.items():
        if option != "self":
          if value != None:
            fmt[option] = value[j]
            print(fmt)
            fit_fmt.append(fmt)
    self.fit_fmt = fit_fmt

  def plot_fit(self, *args, p0 ):
    labels = list(zip(self.files,self.legends))
    self.make_fit(*args, p0 = p0)
    for j in range(len(self.files)):
      xdata = self.data_frame[self.legends[j]][self.xlabel]
      ydata = self.function(xdata, *self.popt[j])
      try:
        fmt = self.fit_fmt[j]
      except IndexError:
        fmt = {}
      if len(args) == 1 and list(args)[0] == 'all':
        plt.plot(xdata, ydata, label = self.legends[j], **fmt)   
      else:
        for i in args:
          if i == self.legends[j] or i ==  self.files[j]:
            plt.plot(xdata, ydata, label = labels[j][1], **fmt)



  def plot(self, *args, p0, rangex = None, rangey = None, 
           show = False, grid = False, option ='fit', path = None):
    self.set_fonts()
    if option == 'scatter':
      self.make_scatter(*args)
    elif option == "fit": 
      self.plot_fit(*args, p0 = p0)
      self.make_scatter(*args)
    elif option == "error_bars":
      if xerr != None and yerr != None:
        self.error_bars(*args, xerr = self.xerr, yerr = self.yerr, fmt = 'none')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "line_error_bars":
      if xerr != None and yerr != None:
        self.error_bars(*args, xerr = self.xerr, yerr = self.yerr, fmt = 'none')
        self.plot_fit(*args, p0 = p0)
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "scatter_error_bars":
      if xerr != None and yerr !=None:
        self.error_bars(*args, xerr = self.xerr, yerr = self.yerr, fmt ='o')
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    elif option == "line_scatter_error_bars":
      if xerr != None and yerr !=None:
        self.error_bars(*args, xerr = self.xerr, yerr = self.yerr, fmt = 'o')
        self.plot_fit(*args, p0= p0, **kargs)
      else:
        print('Need to give values for error bars!!')
        print('Exiting...')
        exit(1)
    else:
      print('Option is not known...')
      print('Choose between: line, scatter, scatter_line')
    if self.title != None:
      plt.title(self.title, fontdict = self.title_font)
    plt.xlabel(self.xlabel, fontdict = self.axes_font)
    plt.ylabel(self.ylabel, fontdict = self.axes_font)
    if rangex != None:
      plt.xlim(rangex)
    if rangey != None:
      plt.ylim(rangey)
    #plt.legend(prop = self.legend_font)
    if grid == True:
      plt.grid()
    if show == True:
      plt.show()
    if path != None:
      self.fig.savefig(path+'/'+self.name+'.png')
    self.fig.savefig(self.name+'.png')


#test = easy_plot('test1', files =['uqFig1MH_magic_qf0.77_nieg250.dat',], legends = ['q=1'])
#test.plot('q=1', show = True, option = 'scatter_line')
#test = easy_plot('test1', title = "NME for 2", files =['uqFig1MH_magic_qf0.77_nieg250.dat','qFig1MH_magic_qf0.77_nieg250.dat'], legends = ['q=1','q=0.77'], xlabel ='Emax', ylabel = 'NME')
#test.plot('all', show = True, grid = True, option ='scatter')