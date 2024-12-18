import re
import holoviews as hv
import geoviews as gv
import panel as pn
import param
from holoviews.streams import Selection1D
from bokeh.plotting import figure, output_file, save
from bokeh.io import export_png
from config import STREAMGAGE_SUBSET
import hvplot.pandas 


### Plot Options
map_plot_opts = dict(
    width=1200,
    height=600,
    title='United States Streamgage Map',
    xaxis=None,
    yaxis=None
)


class Map(param.Parameterized):
    '''Instantiate map of CONUS.'''
    states = param.DataFrame(precedence=-1)
    streamgages = param.DataFrame(precedence=-1)
    state_select = param.ListSelector(default=[], label="Select a State(s)")
    basemap_select = param.Selector(default="OSM", objects=gv.tile_sources.tile_sources.keys(), label="Select a Basemap")
    streamgage_type_filter = param.Selector(objects=STREAMGAGE_SUBSET, default="all", label="Filter Streamgages by Type")
    streamgage_id_input = param.String(label='Streamgage Site ID')
    streamgage_id_string = param.String(precedence=-1, default="")
    search_streamgage_id_input = param.Event(label="Search IDs")
    clear_streamgage_id_input = param.Event(label="Clear IDs")
    reset_map = param.Event(label="Reset Map")
    stream = Selection1D(source=None)


    def __init__(self, **params):
        '''
        Initialize the Map class with given parameters.


        Args:
            **params: Keyword arguments for parameter initialization.
        '''
        super().__init__(**params)
        self.stream = Selection1D(source=None)



  

    @param.depends("state_select")
    def display_states(self) -> gv.Polygons:
        '''
        Display map of selected states.


        Returns:
            gv.Polygons: HoloViews Polygons object of the selected states.
        '''
        if self.state_select:
            _states = gv.Polygons(self.states[self.states['shapeName'].isin(self.state_select)])
        else:
            _states = gv.Polygons(self.states)
        return _states


    @param.depends("basemap_select")
    def display_basemap(self):
        '''
        Display the selected basemap.


        Returns:
            gv.TileSource: The selected basemap from tile sources.
        '''
        return gv.tile_sources.tile_sources[self.basemap_select]


    @param.depends("state_select", "streamgage_type_filter", "streamgage_id_string", watch=True)
    def display_streamgages(self) -> gv.Points:
        '''
        Display streamgage points based on the selected filters.


        Returns:
            gv.Points: HoloViews Points object representing streamgages.
        '''
        # Give precedence to streamgage_id_input search
        if len(self.streamgage_id_string) > 0:
            id_list = [pid.strip() for pid in self.streamgage_id_string.split(",")]
            streamgages_to_display = self.streamgages[self.streamgages['site_no'].isin(id_list)]
        else:
            column = self.streamgage_type_filter
            if column != "all":
                streamgages_to_display = self.streamgages[self.streamgages[column] == 1]
            else:
                streamgages_to_display = self.streamgages


            if len(self.state_select) > 0:
                streamgages_to_display = (
                    streamgages_to_display.clip(self.states[self.states['shapeName'].isin(self.state_select)])
                )


        site_gages = gv.Points(streamgages_to_display).opts(
            tools=['hover', 'tap'],
            cmap="Plasma", # stand in and will be changed later
            color="complete_yrs", # stand in and will be changed later
            size=5,# stand in and will be changed later
        )
        self.stream.source = site_gages
        print("Stream source assigned:", self.stream.source)
        return site_gages


    @param.depends("display_states", "display_basemap", "display_streamgages")
    def view(self) -> pn.pane.HoloViews:
        '''
        Merge map components into a display.


        Returns:
            pn.pane.HoloViews: A Panel object containing the complete map view.
        '''
        return pn.pane.HoloViews(
            self.display_basemap() * self.display_states() * self.display_streamgages().opts(**map_plot_opts)
        )
   
    @param.depends("search_streamgage_id_input", watch=True)
    def _update_streamgage_input(self)-> None:
        '''
        Updates the streamgage ID string based on the input provided.
        If the input contains invalid characters (anything other than
        digits, commas, or spaces), a warning notification is displayed.


        Returns:
            None
        '''
        if re.search('[^0-9, ]', self.streamgage_id_input):
            pn.state.notifications.warning("Search included invalid characters. Please see the tooltip (?) for correct formatting.", duration=5000)
        else:
            self.streamgage_id_string = self.streamgage_id_input


    @param.depends("clear_streamgage_id_input", watch=True)
    def _clear_streamgage_input(self)-> None:
        '''
        Clears the streamgage ID input and string.
        This method sets both the input and string attributes to empty.


        Returns:
            None
        '''
        self.streamgage_id_string = ""
        self.streamgage_id_input = ""


    @param.depends("reset_map", watch=True)
    def _reset_map(self) -> None:
        '''
        Resets all parameters to their default values except for a few specified parameters.
        This method iterates through all parameters and resets those that are not explicitly excluded.


        Returns:
            None
        '''
        # loop through all params
        for par in self.param:
            # reset params with inputs
            if par not in ["name", "streamgages", "states", "search_streamgage_id_input", "clear_streamgage_id_input", "reset_map"]:
                setattr(self, par, self.param[par].default)

    def export_to_png(self):
        plot = self.view()
        hv.save(plot.object, 'map_plot.png', fmt = 'png')
        pn.state.notifications.info("The map has been exported to a png", duration=5000)
