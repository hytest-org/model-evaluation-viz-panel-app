import geopandas as gpd
import geoviews as gv
import holoviews as hv
import pandas as pd
import panel as pn
from config import EX_STATES
from map import Map
from flow import FlowPlot
from holoviews.streams import Selection1D

pn.extension(notifications=True)
hv.extension("bokeh")

# notifications
pn.state.notifications.position = 'top-center'

### PATHS  # noqa: E266
states_path = "./data/geoBoundaries-USA-ADM1_simplified.geojson"
streamgages_path = "./data/streamflow_gages_v1_n5390.csv"

### DATA  # noqa: E266
# read GeoJSON file
def _get_state_data(_filepath: str) -> tuple[gpd.GeoDataFrame, list]:
    '''
    Read in state geographies from a specified file path.

    Args:
        _filepath (str): The file path to the geospatial data file containing state geometries.

    Returns:
        tuple[gpd.GeoDataFrame, list]: A tuple containing:
            - A GeoDataFrame with the state geometries, excluding specified states.
            - A sorted list of unique state names from the GeoDataFrame.
    '''
    # create 
    _states = gpd.read_file(_filepath)
    _states = _states[~_states['shapeName'].isin(EX_STATES)]
    _states_list = list(_states['shapeName'].unique())
    _states_list.sort()
    return _states, _states_list

states_data, states_list = _get_state_data(states_path)

def _get_streamgage_data(_filepath: str) -> gpd.GeoDataFrame:
    '''
    Reads streamflow data from a .csv and filters it based on the 'gagesII_class==ref'.
    Args:
        _filepath (str): Path to the .csv file 
    Returns:
        gpd.GeoDataFrame: the filtered geopandas data file
    '''
    # read lat-long or xy data using pandas read_csv
    read_data = pd.read_csv(_filepath, dtype=dict(site_no=str, nldi=int, swim=int, gfv1d1=int))

    # filter
    filtered_data = read_data[read_data['gagesII_class'] == 'Ref']
    # now turn into a geodataframe
    filtered_gdf = gpd.GeoDataFrame(filtered_data,  # noqa: W291
                                    geometry=gpd.points_from_xy(filtered_data.dec_long_va, filtered_data.dec_lat_va),
                                    crs="EPSG:4326"  # most data is exported in EPSG:4326
    )
    return filtered_gdf

streamgage_data = _get_streamgage_data(streamgages_path)
tabs =pn.Tabs(('None'))
class Mediator:
    def __init__(self, map_inst, flow_inst, tabs):
        self.map = map_inst
        self.flow = flow_inst
        self.map.stream.param.watch(self.handle_tap, 'index')
        print(f"Watching: {self.map.stream.param.watchers}")
        self.map.stream.param.watch(self.test_tap, 'index')
        self.tabs = tabs

    def test_tap(self, event):
        print(f"Tap event triggered with data:{event.new}")    
    def handle_tap(self, event):
        if event.new: 
            selected_index = event.new[0]
            print(f"Tapped Index: {selected_index}")
            site_no = self.map.streamgages.iloc[selected_index]['site_no']
            print(f"Selected {site_no}")
            self.flow.set_site_id(site_no)
            new_tab_name = f"Flow for Site {site_no}"
            self.tabs.append((new_tab_name, self.flow.view))
            


map_inst = Map(states = states_data, streamgages = streamgage_data)
flow_inst = FlowPlot()
mediator = Mediator(map_inst,flow_inst, tabs)
### WIDGET OPTIONS  # noqa: E266

export_flow_button = pn.widgets.Button(name = "📈  Export the flow plot to image")
export_flow_button.on_click(lambda event: flow_inst.export_to_png())
footer = pn.pane.Markdown("""For questions about this application, visit the [Hytest Repo](https://github.com/hytest-org/hytest/issues)""" ,width=500, height =20)

export_map_button = pn.widgets.Button(name = "🖼️ Export map to image")
export_map_button.on_click(lambda event: map_inst.export_to_png())
map_inst.param.state_select.objects = states_list
flow_tab = flow_inst.view
tabs =pn.Tabs(('Map',map_inst.view), ('Flow',flow_tab))
model_eval = pn.template.MaterialTemplate(
    title="HyTEST Model Evaluation",
    sidebar=[
        map_inst.param, flow_inst.param.start_date, flow_inst.param.end_date,footer],
    main=[tabs,export_map_button, export_flow_button],

)
model_eval.servable()
