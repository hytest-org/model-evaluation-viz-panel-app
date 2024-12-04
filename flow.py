import holoviews as hv
hv.extension("bokeh")

import pandas as pd

from pygeohydro import NWIS
import panel as pn
import param
import datetime as dt
from datetime import timedelta

import nest_asyncio
nest_asyncio.apply()

#Plotting ops 1/4 the size of the map
flow_plot_opts = dict(
    width=300,
    height=300,
    title='Flow Plot',
    xaxis=None,
    yaxis=None
)

class FlowPlot(param.Parameterized):
    """Instantiate flow map """
    flow_data = param.DataFrame(precedence=-1)
    site_no = param.String(default=None)
    start_date = param.Date(default =  dt.datetime(2020,1,1) ,label = "Start Date")
    end_date = param.Date(default =  dt.datetime(2020,1,10),label = "End Date")

    
    def __init__(self, **params)-> None:
        '''
        Initializes the class with given parameters.

        Args:
            **params: Keyword arguments for parameter initialization.
        '''
        super().__init__(**params)
        self.nwis = NWIS()


    def getflow(self, site_no, dates)-> any:
        '''
        Fetches the streamflow data for a given site ID and date range.

        Args:
            site_no (str): The site ID for which to fetch streamflow data.
            dates (Tuple[str, str]): A tuple containing the start and end dates.

        Returns:
            Any: The streamflow data retrieved from NWIS.
        '''
        # nwis = NWIS()
        if not site_no:
            print("No site_no Provided")
            return pd.DataFrame()
        try:
            return self.nwis.get_streamflow(site_no, dates)
        except Exception as e:
            print(f"error:{e}")
            return pd.DataFrame()
    
    def set_site_id(self, site_id):
        self.site_no = site_id
        self.update_flow_data()

   
    @param.depends("site_no", "start_date", "end_date", watch = True)
    def update_flow_data(self) -> None:
        '''
        Updates flow data when site ID or date range changes.

        Returns:
            None: This method updates the flow_data attribute but does not return a value.
        '''
        # start_date = self.start_date
        # end_date = self.end_date
        if self.site_no:
            dates = (self.start_date, self.end_date)
            self.flow_data = self.getflow(self.site_no, dates)
        else: 
            self.flow_data = pd.DataFrame()
        

    
    @param.depends("flow_data", watch = True)
    def plot_streamflow(self)-> hv.Overlay:
        '''
        Plots the streamflow data if available.

        Returns:
            hv.Overlay: A HoloViews overlay containing the streamflow curves.
        '''
        if self.flow_data is None or self.flow_data.empty:
            return hv.Curve([]).opts(**flow_plot_opts)

   
        x_axis = self.flow_data.index
        y_axis = self.flow_data.iloc[:, 0]
        
        flow_line = hv.Curve((x_axis, y_axis), label =f"Streamflow for {self.site_no}").opts(**flow_plot_opts)

        return hv.Overlay(flow_line).opts(legend_position='right')

    # @param.depends("plot_streamflow")
    def view(self) -> pn.pane.HoloViews:
        '''
        Returns a Panel that displays the streamflow plot.

        Returns:
            pn.pane.HoloViews: A Panel object containing the streamflow plot.
        '''
        return pn.pane.HoloViews(self.plot_streamflow(), sizing_mode = 'stretch_width')
