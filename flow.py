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
    height=150,
    title='Flow Plot',
    xaxis=None,
    yaxis=None
)

class FlowPlot(param.Parameterized):
    """Instantiate flow map """
    flow_data = param.DataFrame(precedence=-1)
    site_ids = param.ListSelector(default=[], label = "Selected Site ID")
    start_date = param.Date(default =  dt.datetime(2020,1,1) ,label = "Start Date")
    end_date = param.Date(default =  dt.datetime(2020,1,10),label = "End Date")

    def set_site_id(self, site_id):
        self.site_ids = [site_id]
        self.update_flow_data()

    def __init__(self, **params)-> None:
        '''
        Initializes the class with given parameters.

        Args:
            **params: Keyword arguments for parameter initialization.
        '''
        super().__init__(**params)

    def getflow(self, site_ids, dates)-> any:
        '''
        Fetches the streamflow data for a given site ID and date range.

        Args:
            site_ids (str): The site ID for which to fetch streamflow data.
            dates (Tuple[str, str]): A tuple containing the start and end dates.

        Returns:
            Any: The streamflow data retrieved from NWIS.
        '''
        nwis = NWIS()
        data = nwis.get_streamflow(site_ids, dates)
        return data
    
    @param.depends("site_ids", "start_date", "end_date", watch = True)
    def update_flow_data(self) -> None:
        '''
        Updates flow data when site ID or date range changes.

        Returns:
            None: This method updates the flow_data attribute but does not return a value.
        '''
        start_date = self.start_date
        end_date = self.end_date
        dates = (start_date, end_date)
        id = self.site_ids
        print(id)
        dates = (start_date, end_date)
        self.flow_data = self.getflow(id, dates)

    
    @param.depends("flow_data", watch = True)
    def plot_streamflow(self)-> hv.Overlay:
        '''
        Plots the streamflow data if available.

        Returns:
            hv.Overlay: A HoloViews overlay containing the streamflow curves.
        '''
        if self.flow_data is None or self.flow_data.empty:
            return hv.Curve([]).opts(**flow_plot_opts)

        curves = []
        for column in self.flow_data.columns:
            curve = hv.Curve(self.flow_data[column]).opts(title=f"Streamflow for {column}", xlabel='Date', ylabel='Flow Value')
            curves.append(curve)

        return hv.Overlay(curves).opts(legend_position='right')

    @param.depends("plot_streamflow")
    def view(self) -> pn.pane.HoloViews:
        '''
        Returns a Panel that displays the streamflow plot.

        Returns:
            pn.pane.HoloViews: A Panel object containing the streamflow plot.
        '''
        return pn.pane.HoloViews(self.plot_streamflow(), sizing_mode = 'stretch_width')
