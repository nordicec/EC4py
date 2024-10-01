""" Python module for reading TDMS files produced by LabView and specifically form EC4 DAQ.

    This module contains the public facing API for reading TDMS files produced by EC4 DAQ.
"""
from nptdms import TdmsFile
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter 
from . import util
from .ec_data import EC_Data
from .step_data import Step_Data
from .ec_setup import EC_Setup
from .analysis_levich import Levich

from pathlib import Path
import copy
from .util import Quantity_Value_Unit as QV
from .util_graph import plot_options,quantity_plot_fix, make_plot_2x,make_plot_1x,make_plot_2x_1


STYLE_POS_DL = "bo"
STYLE_NEG_DL = "ro"

class Step_Datas:
    """# Class to analyze CV datas. 
    Class Functions:
    - .plot() - plot data    
    
    ### Analysis:
    - .Levich() - plot data    
    - .KouLev() - Koutechy-Levich analysis    
    - .Tafel() - Tafel analysis data    
    
    ### Options args:
    "area" - to normalize to area
    
    ### Options keywords:
    legend = "name"
    """
    def __init__(self, paths:list[Path] | Path|None = None, **kwargs):
        
        
        if paths is None:
            return
        if isinstance(paths,Path ):
            path_list = [paths]
        else:
            path_list = paths
        self.datas = [Step_Data() for i in range(len(path_list))]
        index=0
        for path in path_list:
            ec = EC_Data(path)
            try:
                self.datas[index].conv(ec,**kwargs)
            finally:
                index=index+1 
        #print(index)
        return
    #############################################################################
    def __getitem__(self, item_index:slice|int) -> Step_Data: 

        if isinstance(item_index, slice):
            step = 1
            start = 0
            stop = len(self.datas)
            if item_index.step:
                step =  item_index.step
            if item_index.start:
                start = item_index.start
            if item_index.stop:
                stop = item_index.stop    
            return [self.datas[i] for i in range(start,stop,step)  ]
        else:
            return self.datas[item_index]
    #############################################################################
    def __setitem__(self, item_index:int, new_Step:Step_Data):
        if not isinstance(item_index, int):
            raise TypeError("key must be an integer")
        self.datas[item_index] = new_Step
    #############################################################################
   
    
################################################################    
    def plot(self, *args, **kwargs):
        """Plot CVs.
            use args to normalize the data
            - area or area_cm
            - rotation
            - rate
            
            #### use kwargs for other settings.
            
            - legend = "name"
            - x_smooth = 10
            - y_smooth = 10
            
            
        """
        p = plot_options(kwargs)
        p.set_title("Steps")
        line, data_plot = p.exe()
        legend = p.legend
        datas = copy.deepcopy(self.datas)
        #CVs = [CV_Data() for i in range(len(paths))]
        data_kwargs = kwargs
        for data in datas:
            #rot.append(math.sqrt(cv.rotation))
            for arg in args:
                data.norm(arg)

            data_kwargs["plot"] = data_plot
            data_kwargs["name"] = data.setup_data.name
            if legend == "_" :
                data_kwargs["legend"] = data.setup_data.name
            p = data.plot(**data_kwargs)
         
        data_plot.legend()
        return data_kwargs
    
    #################################################################################################    
   
    def integrate(self,t_start,t_end,step_nr:int = -1, **kwargs):
        
        
        data_plot_i,data_plot_E, analyse_plot = make_plot_2x_1("Integrate Analysis")
        #########################################################
            # Make plot
        data_kwargs = kwargs
        data_kwargs["plot_i"] = data_plot_i
        data_kwargs["plot_E"] = data_plot_E
        data_kwargs["analyse_plot"] = analyse_plot
        p = plot_options(kwargs)
        charge = [QV()] * len(self.datas)
        #print(data_kwargs)
        for i in range(len(self.datas)):
            if(step_nr>-1):
                step = self.datas[i].get_step(step_nr)
            else:
                step = self.datas[i]
            charge[i] = (step.integrate(t_start,t_end,**data_kwargs))
        return charge
    
    ##################################################################################################################
    def Tafel(self, lims=[-1,1], *args, **kwargs):
        
        return
    
    
    def Levich(self, Time_s_:float=-1, step_nr:int = -1, *args, **kwargs):
        
        data_plot_i,data_plot_E, analyse_plot = make_plot_2x_1("Levich Analysis")
        # CV_plot, analyse_plot = fig.subplots(1,2)
        s = "Steps_i"
        if(step_nr>-1):
            s = s + f" #{step_nr}"
        data_plot_i.title.set_text(s)
        
        data_plot_E.title.set_text('Steps_E')
        analyse_plot.title.set_text('Levich Plot')

        #########################################################
        # Make plot
        data_kwargs = kwargs
        data_kwargs["plot_i"] = data_plot_i
        data_kwargs["plot_E"] = data_plot_E
            
        rot, y, E, y_axis_title, y_axis_unit  = plots_for_rotations(self.datas, Time_s_, step_nr, *args, **data_kwargs)
  
        # Levich analysis
        B_factor = Levich(rot, y, y_axis_unit, y_axis_title, STYLE_POS_DL, "steps", plot=analyse_plot )
        
        print("Levich analysis" )
        #print("dir", "\tpos     ", "\tneg     " )
        print(" :    ",f"\t{y_axis_unit} / rpm^0.5")
        print("slope:", "\t{:.2e}".format(B_factor.value))
        return B_factor
 
 
 
def plots_for_rotations(step_datas: Step_Datas, time_s_: float,step_nr: int =-1, *args, **kwargs):
    rot = []
    y = []
    t = []
    E = []
    # Epot=-0.5
    y_axis_title = ""
    y_axis_unit = ""
    datas = copy.deepcopy(step_datas)
    data_kwargs = kwargs
    # x_qv = QV(1, "rpm^0.5","w")
    plot_i = data_kwargs["plot_i"]
    plot_E = data_kwargs["plot_E"]
    line=[]
    for data in datas:
        # x_qv = cv.rotation
        rot.append(math.sqrt(data.rotation))
        for arg in args:
            data.norm(arg)
        data_kwargs["legend"] = str(f"{float(data.rotation):.0f}")
        if step_nr>-1:
            data = data[step_nr]
        # l, ax = data.plot(**data_kwargs)
        l_i, ax1 = data.plot("Time", "i", plot=plot_i,**data_kwargs)
        l_E, ax2 = data.plot("Time", "E", plot=plot_E,**data_kwargs)
        line.append([l_i,l_E])
        index = data.index_at_time(time_s_)
        # print("INDEX",index)
        t.append(data.Time[index])
        E.append(data.E[index])
        y.append(data.get_current_at_time(time_s_))
        y_axis_title = str(data.i_label)
        y_axis_unit = str(data.i_unit)
    rot = np.array(rot)
    y = np.array(y)
    
    plot_i.plot(t, y, STYLE_POS_DL)
    plot_i.legend()
    plot_E.plot(t, E, STYLE_POS_DL)
    return rot, y, t, y_axis_title, y_axis_unit