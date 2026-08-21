---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3
---


```{code-cell} ipython3
import plotly
```


```{code-cell} ipython3
# read cartesian radar data

path = "./data/radar/cart/20170812"

file = "./data/titan/ascii/Tracks2Ascii20170812.txt"

# not sure if this is needed
z_step = 10

```


```{code-cell} ipython3
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

def ascii_to_df(file):
    
    #open file and extract column names
    f = open(file)
    lines = f.readlines()
    f.close()
    
    label_line_index = None  
    
    for i, line in enumerate(lines):
        if 'labels' in line:
            label_line_index = i
            break  
    labels = lines[label_line_index].split(":", 1)[1].strip().split(",")
    
    #the data lines are the ones that do not start with #
    data_lines = [line.strip() for line in lines if not line.startswith("#")]

    rows = []
    for line in data_lines:
        parts = line.split()
    
        try:
            # Try parsing the polygon count value (always right before 72 values)
            poly_count_index = -73  # 72 floats + 1 count (the column starts with the numnber 72, which is not part of the values)
    
            # Parents and children may be missing
            parent_str = parts[poly_count_index - 2]
            if parent_str == '-':
                parents = []
            else:
                # convert parent_str to list of ints
                parents = [int(str) for str in parent_str.split(",")]  
           
            child_str = parts[poly_count_index - 1]
            if child_str == '-':
                children = []
            else:
                # convert parent_str to list of ints
                children = [int(str) for str in child_str.split(",")]   
    
            # Handle missing values marked as "-"
            #parents = int(parent_str) if parent_str != '-' else np.nan
            #children = int(child_str) if child_str != '-' else np.nan
    
            # Polygon values: skip the count, get the next 72 values
            polygon_values = list(map(float, parts[poly_count_index + 1:]))
    
            # Fixed columns
            fixed_cols = parts[:poly_count_index - 2]
    
            # Combine into one row
            row = fixed_cols + [parents, children, polygon_values]
            rows.append(row)
        except Exception as e:
            print("ERROR: skipping line: ", line)
            continue
    
    
    
    # Final columns: fixed + 3 custom ones
    final_labels = labels[:len(rows[0]) - 3] + ['parents', 'children', 'nPolySidesPolygonRays']
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=final_labels)
    
    # Convert date and time columns to datetime
    df['date_utc'] = pd.to_datetime(
        df['Year'].astype(str) + '-' +
        df['Month'].astype(str).str.zfill(2) + '-' +
        df['Day'].astype(str).str.zfill(2) + ' ' +
        df['Hour'].astype(str).str.zfill(2) + ':' +
        df['Min'].astype(str).str.zfill(2) + ':' +
        df['Sec'].astype(str).str.zfill(2),
        format='%Y-%m-%d %H:%M:%S',
        utc=True
    )
    return df
```


```{code-cell} ipython3
def build_helper_structures(df):

    d = {}

    def addit(x,y):
        if len(y) > 0:
            if x in d:
                d[x].append(y)
            else:
                d[x] = [y]

    # dictionary that associates storms (SimpleNum) with time step
    storms_by_time_step = {}
    # dictionary? dataframe? or just use the original df?  that associates storm (SimpleNum) with centroid, parents, and children
    simple_storm_info = {}

    # use df.apply(lambda x: axis=1)    

#    for row in df:
#        utc = row['date_utc']
#        simple_num = row['SimpleNum']
#        if utc in storms_by_time_step:
#            storms_by_time_step[utc].append(simple_num)
#        else:
#            storms_by_time_step[utc] = [simple_num]

       

    #utc1 = r['date_utc']
    #k1 = utc1.iloc[0].isoformat()
    # df.apply(lambda r: addit(r['date_utc'].isoformat(), r['SimpleNum']), axis = 1)  
    df.apply(lambda r: addit(r['date_utc'].strftime('%Y%m%d_%H%M%S'), r['SimpleNum']), axis = 1) 
    
    # df.apply(lambda r: addit(r['date_utc'], r['SimpleNum']), axis = 1)    

    # print("simple storm lists: ", d)
    
    return d # storms_by_time_step, simple_storm_info

```


```{code-cell} ipython3
def get_xy(simple_num, df):
    # l = [(1,10),(2,20),(3,30)]
    storm_df = df[df['SimpleNum'] == str(simple_num)][['VolCentroidX(km)','VolCentroidY(km)']]
    if (storm_df.empty):
        print("ERROR, storm not found: ", simple_num)
        return
    v_x = storm_df['VolCentroidX(km)'].to_list()[0]
    v_y = storm_df['VolCentroidY(km)'].to_list()[0]
    return (float(v_x), float(v_y))
    

# child_x, child_y = prepare_child_connections(df_complete, time_step_key, 'child')
# storms_by_time is a dictionary of storm SimpleNums indexed by time
# e.g.  {Timestamp('2022-05-21 14:59:49+0000', tz='UTC'): ['0', '1', '2', '3'], ...}
def build_lineage(df_complete, storms_by_time, time_step_key, linkage='child'):


    linkage_x = []
    linkage_y = []

    # get the list of storms for the time step
    if time_step_key in storms_by_time:
        storm_simpleNums = storms_by_time[time_step_key]
        # [x] [y] double list comprehension? or just stack and then split?
        #storm_simpleNum 
        #r = all_together.df[all_together.df["SimpleNum"] == '3']
        #vol_centroid_x = 
        [vol_centroid(s,df_complete) for s in storm_simpleNums]
        # linkage_x, linkage_y = vol_centroid('5',df_complete)   # this works

```


```{code-cell} ipython3
def vol_centroid(storm_simple_num, df):

    #storm_df = df[df['SimpleNum'] == storms[0]][['children','parents','VolCentroidX(km)','VolCentroidY(km)']]
    storm_df = df[df['SimpleNum'] == storm_simple_num][['children','parents','VolCentroidX(km)','VolCentroidY(km)']]
    #print("storm_df: ")
    #print(storm_df)

    children = storm_df['children'].to_list()[0]
    parents = storm_df['parents'].to_list()[0]
    v_x = storm_df['VolCentroidX(km)'].to_list()[0]
    v_y = storm_df['VolCentroidY(km)'].to_list()[0]

    # ok, this becomes recursive ... we are performing the same operation on all children, all parents, and then appending to lists

    # storm_parents = df[df['SimpleNum'] == storms[0]]['parents']

    # for each storm simple_num, get the centroid of the children
    children_centroid_xy = [get_xy(s,df) for s in children]  # looks like [(vx,vy), (vx2,vy2) ...] 

    # for each storm simple_num, get the centroid of the parents
    parents_centroid_xy = [get_xy(s,df) for s in parents]  # looks like [(vx,vy), (vx2,vy2) ...] 

    # format (storm_x, child1_x, None, storm_x, child2_x, None, ...)  same for parents and same for y
    # where storm_x = (v_x, v_y), child1_x = (x,y), and None = (None, None)

    lc = []
    for p in children_centroid_xy:
        #print("p: ", p)
        lc.append((v_x, v_y))
        lc.append(p)
        lc.append((None,None))  # None is needed to add breaks in the plotting between sets of (parent,child)

    lp = []
    for p in parents_centroid_xy:
        #print("p: ", p)
        lp.append((v_x,v_y))
        lp.append(p)
        lp.append((None,None))

    l = lc + lp 
    #linkage_x + get_xy()   # [v_x, p_x, None]
    linkage_x = []
    linkage_y = []
    # print("l = ", l)
    if l:     # if not empty 
        linkage_x, linkage_y = zip(*l)
 
    # insert parent (x & y), linkage(x & y), None, None, to make segments
    # add the (simple_num, complex_num) 
    return storm_simple_num, linkage_x, linkage_y


def vol_centroid_w_labels(storm_simple_num, df):

    labels = [] # these are the labels for the arrows: [self, child, None, self, parent, ...]

    #storm_df = df[df['SimpleNum'] == storms[0]][['children','parents','VolCentroidX(km)','VolCentroidY(km)']]
    storm_df = df[df['SimpleNum'] == storm_simple_num][['children','parents','VolCentroidX(km)','VolCentroidY(km)']]
    # print("storm_df: ")
    # print(storm_df)

    children = storm_df['children'].to_list()[0]
    parents = storm_df['parents'].to_list()[0]
    v_x = storm_df['VolCentroidX(km)'].to_list()[0]
    v_y = storm_df['VolCentroidY(km)'].to_list()[0]

    clabels = [(str(storm_simple_num), str(c), "")  for c in children]
    plabels = [(str(p), str(storm_simple_num), "")  for p in parents]

    labels = list(sum(clabels+plabels, ()))

    # ok, this becomes recursive ... we are performing the same operation on all children, all parents, and then appending to lists

    # storm_parents = df[df['SimpleNum'] == storms[0]]['parents']

    # for each storm simple_num, get the centroid of the children
    children_centroid_xy = [get_xy(s,df) for s in children]  # looks like [(vx,vy), (vx2,vy2) ...]

    # for each storm simple_num, get the centroid of the parents
    parents_centroid_xy = [get_xy(s,df) for s in parents]  # looks like [(vx,vy), (vx2,vy2) ...]

    # format (storm_x, child1_x, None, storm_x, child2_x, None, ...)  same for parents and same for y
    # where storm_x = (v_x, v_y), child1_x = (x,y), and None = (None, None)

    lc = []
    for p in children_centroid_xy:
        #print("p: ", p)
        lc.append((v_x, v_y))
        lc.append(p)
        lc.append((None,None))

    lp = []
    for p in parents_centroid_xy:
        #print("p: ", p)
        lp.append(p)
        lp.append((v_x,v_y))
        lp.append((None,None))

    l = lc + lp
    #linkage_x + get_xy()   # [v_x, p_x, None]
    linkage_x = []
    linkage_y = []
    # print("l = ", l)
    if l:     # if not empty
        linkage_x, linkage_y = zip(*l)

    # insert parent (x & y), linkage(x & y), None, None, to make segments
    # add the (simple_num, complex_num)
    return labels, linkage_x, linkage_y


```


```{code-cell} ipython3
import matplotlib                                
matplotlib.use('agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

import numpy as np



# TODO: make a separate module/package for this ...
# then, make it available like this ...
# from colormapf import color_conversion_base, etc.
# 
import matplotlib.colors as colors
from matplotlib.colors import to_rgb

def to_rgb(v):
    return int(v*255)

#
# NOTE:  depends on color map file to convert X11 color names to hex
#
#color_conversion_base = "." 
#file_name = "x11_colors_map.txt"
#conversion_file = color_conversion_base + "/" + file_name
x11_color_name_map = {}  # it is a dictionary
# read the color name to hex conversion file
#f = open(conversion_file, "r")
#for line in f.readlines():
#    x = line.split()
#    x11_color_name_map[x[0]]=x[1]

def normalize_colormap(edges, colors):
    nsteps = int(edges[-1] - edges[0] + 1)
    new_edges = np.linspace(edges[0], edges[-1], nsteps)
    new_colors = []
    for i in range(0, len(edges)-1):
        for ii in range(int(edges[i]), int(edges[i+1])):
            new_colors.append(colors[i])
    return (new_edges, new_colors)

# example using lrose-displays ...
# lrose-displays file format:
# MIN  MAX     NAME (name is ascii text or hex #rrggbb )
# 0      5    yellow

def fetch_lrose_displays_color_scale(color_scale_name, color_scale_base_dir=None):
    if color_scale_base_dir == None:
        color_scale_base = "/usr/local/lrose/share/color_scales" # /home/jovyan/share/lrose-nightly/share/color_scales"
        #color_scale_base = "~/lrose/share/color_scales" # /home/jovyan/share/lrose-nightly/share/color_scales"
    else:
        color_scale_base = color_scale_base_dir
    file_name = color_scale_name    # "zdr_color"    
    color_scale_file = color_scale_base + "/" + file_name
    color_names = []
    edges = []
    # read the color map file
    f = open(color_scale_file, "r")
    for line in f.readlines():
        if line[0] != '#':
            # print(line)
            x = line.split()
            print(x)
            if len(x) >= 3:  # TODO sometimes the color name has multiple words!!! dark slate blue!!!
                color_names.append("".join(x[2:]).lower())
                if len(edges) == 0:
                    edges.append(float(x[0]))
                edges.append(float(x[1]))
    # add the ending edge
    # display(color_names)
    # display(edges)
    # convert the X11 color names to hex
    color_scale_hex = []
    for cname in color_names:
        if cname in x11_color_name_map:
            color_scale_hex.append(x11_color_name_map[cname]) 
        else:
            color_scale_hex.append(colors.to_hex(cname))

    # convert color names to rgb
    #rgb_color = to_rgb("dodgerblue")
    # define color map (matplotlib.colors.ListedColormap)
    try:
        # is this used???
        norm = colors.BoundaryNorm(boundaries=edges, ncolors=len(color_names))
        norm.autoscale(edges)
    # TODO: the edges are NOT uniform the everything steps by 1 except the last goes 12 to 20
        (zcmap, znorm) = colors.from_levels_and_colors(edges, color_scale_hex, extend='neither')
    except ValueError as err:
        print("something went wrong first: ", err)
    print("edges: ")
    print(edges)
    print("colors: ", color_scale_hex)
    return edges, color_scale_hex 

# function:  convert_to_go_colorscale takes edges and colors in hex
#               and converts this information to a colormap format 
#               recognized by Dash graph objects,
#               scatterpolar.
# 
#                colorscale=[(0.00, "red"),   (0.33, "red"),
#                    (0.33, "green"), (0.66, "green"),
#                    (0.66, "blue"),  (1.00, "blue")],
# color_scale_hex:  ['#483d8b', '#000080', '#0000ff', '#0000cd', '#87ceeb', '#006400', '#228b22', '#9acd32', '#bebebe', '#f5deb3', '#ffd700', '#ffff00', '#ff7f50', '#ffa500', '#c71585', '#ff4500', '#ff0000']
# edges:  [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 20.0]
# use for lrose-display and self-defined coloscales
def convert_to_go_colorscale_old(edges, colors_hex):
    colorscale=[]
    max = edges[-1]
    min = edges[0]
    edge_range = np.abs(max-min)
    print("max = ", max, " min = ", min, " edge_range = ", edge_range)
    for i in range(len(edges)-1):
       low = (edges[i]-min)/edge_range
       high = (edges[i+1]-min)/edge_range
       c = colors_hex[i]
       colorscale.append((low, c))
       colorscale.append((high, c))
    return colorscale 

def convert_to_go_colorscale(edges, colors_hex):
    colorscale=[]
    max = edges[-1]
    min = edges[0]
    edge_range = np.abs(max-min)
    print("max = ", max, " min = ", min, " edge_range = ", edge_range)
    for i in range(len(edges)-1):
       low = (edges[i]-min)/edge_range
       high = (edges[i+1]-min)/edge_range
       c = colors_hex[i]
       colorscale.append((low, c))
       colorscale.append((high, c))
    return colorscale 
    
    
# example using matplotlib color maps ...
def convert_to_go_colorscalei_matplotlib(color_scale_name):
# example with colorblind friendly maps (reference Py-ART)
    #plot_color_gradients(
        #"Colorblind Friendly",
        #["LangRainbow12", "HomeyerRainbow", "balance", "ChaseSpectral", "SpectralExtended"],
    #)
    import numpy as np
    #import matplotlib.cm as cm
    
    colormap_function = plt.get_cmap(color_scale_name)
    edges =  np.linspace(0, 1, 20) # how to set the number of colors (256)?
    colors_rgb = colormap_function(edges) # Get 256 colors from the colormap

    # need list of tuples [(edge, color), ...]
    clist = []
    i = 0
    for rgba in colors_rgb.tolist():
        rgb_tuple = tuple(map(to_rgb, rgba[0:3]))
        #clist.append([edges[i], 'rgb'+str(rgb_tuple)])
        clist.append(['rgb'+str(rgb_tuple)])
        i += 1
        
    print(clist) # Output: (256, 4) - 256 colors with RGBA values
    # RGBA values are 
    # rgba(red, green, blue, alpha)
    # The alpha parameter is a number between 0.0 (fully transparent) and 1.0 (not transparent at all):
    return edges, clist  # colorscale_ticks, colorscale_for_go
    # return clist 
    # return convert_to_go_colorscale(edges, colors_hex)

#>>> def to_rgb(v):
#...     return int(v*255)
#
#>>> for rgba in c_rgb.tolist():
#...         list(map(to_rgb, rgba[0:3]))

#    The 'colorscale' property is a colorscale and may be
#    specified as:
#      - A list of colors that will be spaced evenly to create the colorscale.
#        Many predefined colorscale lists are included in the sequential, diverging,
#        and cyclical modules in the plotly.colors package.
#      - A list of 2-element lists where the first element is the
#        normalized color level value (starting at 0 and ending at 1),
#        and the second item is a valid color string.
#        (e.g. [[0, 'green'], [0.5, 'red'], [1.0, 'rgb(0, 0, 255)']])
#      - One of the following named colorscales:
#            ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
#             'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
#             'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
#             'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
#             'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
#             'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
#             'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
#             'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
#             'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
#             'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
#             'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
#             'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
#             'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
#             'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
#             'ylorrd'].
#        Appending '_r' to a named colorscale reverses it.
#


# main entry point here ...
def fetch(color_map_name):
    # is it a matplotlib name?
    
    if color_map_name in plt.colormaps():
        print("matplotlib knows the color scale")
        return convert_to_go_colorscalei_matplotlib(color_map_name)
    # is it an lrose-display name?
    # if ???
    else:
        print("must be an lrose-display color scale")
        #fetch_lrose_displays_color_scale(color_map_name)
        # edges, color_scale_hex = fetch_lrose_displays_color_scale(color_map_name)
        # hardcode the dbz_colors 
        edges = [-20.0, 5.0, 10.0, 20.0, 30.0, 35.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0, 60.0, 65.0, 70.0, 80.0]
        color_scale_hex = ['#404040', '#483d8b', '#005a00', '#007000', '#087fdb', '#1c47e8', '#6e0dc6', '#c80f86', '#c06487', '#d2883b', '#fac431', '#fefa03', '#fe9a58', '#fe5f05', '#fd341c', '#bebebe', '#d3d3d3']
        # edges:  [-20.0, 5.0, 10.0, 20.0, 30.0, 35.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0, 60.0, 65.0, 70.0, 80.0]
        # max =  80.0  min =  -20.0  edge_range =  100.0

        
    # (edges_norm, colors_norm) = colormap_fetch.normalize_colormap(edges, color_scale_hex)
    # cmap = colors.ListedColormap(colors_norm) # (color_scale_hex)
        # print("color_scale_hex: ", color_scale_hex)
        print("edges: ", edges)
        # print("colors_norm: ", colors_norm)
        # print("edges_norm: ", edges_norm)
        colorscale_for_go = convert_to_go_colorscale(edges, color_scale_hex)
        #print("color scale: ")
        #print(colorscale_for_go)
        colorscale_ticks = list(map(int, edges))
        return colorscale_ticks, colorscale_for_go

    # otherwise, return error



```


```{code-cell} ipython3

```


```{code-cell} ipython3
import os
import plotly
import matplotlib.pyplot as plt
import xarray as xr
import xradar as xd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import datetime
#import bhs
#import build_lineage
#import colormap_fetch

from datetime import datetime, timezone

def file_list(directory_path):
    files = []
    try:
        # Get all entries (files and directories) in the path
        entries = os.listdir(directory_path)
        for entry in entries:
            full_path = os.path.join(directory_path, entry)
            # Check if the entry is a file
            if os.path.isfile(full_path):
                files.append(entry)
    except FileNotFoundError:
        print(f"Error: Directory not found at '{directory_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")
    return files    

def get_file_date_time(file_name):
    return file_name[4:19]

# df is a dataframe from TITAN ascii file that contains storm polygons
# df['utc', 'polygon_x', 'polygon_y']
def plot_with_timefile_slider(z_step, path, df, df_complete):

    filenames = sorted(file_list(path))
    print("found these data files:")
    print(filenames)
 
    # associate polygons and radar data files by date & time 
    # 'ncf_20220521_145949.nc'   compare to 2022-05-21 14:59:49+00:00
    # create a parallel list of filenames with empty lists to keep the 
    #     row index of associated polygons
    # use the filename times as the keys, and then add the polygon row idx to the list
    associated = {get_file_date_time(f): []  for f in filenames}

    df_sorted = df.sort_values(by=['utc'])

    for idx, row in df_sorted.iterrows():
        poly_date_time = row['utc'].strftime('%Y%m%d_%H%M%S')
        if poly_date_time in associated:
            associated[poly_date_time].append(idx)
        else:
            print("missing data file: ", poly_date_time)        

    # get the storms for each time step
    sbts = build_helper_structures(df_complete)
    
    # Create figure
    fig = go.Figure()
    fig.update_layout(height=600, width=600)
    fig = make_subplots(rows=1, cols=1, shared_xaxes='all', shared_yaxes='all')
    #fig = make_subplots(rows=1, cols=1, shared_xaxes=True, shared_yaxes=True)

    fig.update_layout(yaxis_scaleanchor="x")
    fig.update_layout(
        xaxis_range=[-250, 250],
        yaxis_range=[-250, 250],
        xaxis_autorange=False,
        yaxis_autorange=False
    )
    
    # Add traces, one for each slider step
    #     storm traces are within each tenth (0-9 are for first time step
    #        10 - 19 are all traces for the second file / time step   
    # 
  
    colorscale_ticks, colorscale_for_go = fetch("dbz_color")
    colorscale_labels = list(map(str, colorscale_ticks))  # make the ticks into labels for the color bar
    # colorscale_labels = ["-20","5","10","20","30","35","36","39","42","45","48","51","54","57","60","65","70"]
    # colorscale_ticks = [-20,5,10,20,30,35,36,39,42,45,48,51,54,57,60,65,70]
 
    trace_count = 0
    map_trace_indexes = []

    for step in range(0, len(filenames)):
        file = filenames[step]
        file_path = os.path.join(path, file) 
        print("trying to read data file:", file_path)
        ds = xr.open_dataset(file_path)
        x = ds.x0.data
        y = ds.y0.data

        file_date_time = get_file_date_time(file)
        include_polygons = False
        if include_polygons:
            assoc_polys = associated[file_date_time]
            for p_idx in assoc_polys:
                # p_idx = assoc_polys[0]
                # make a list of concatenated polygons, separated by blank/plug
                fig.add_trace(go.Scatter(x=df['polygon_x'][p_idx], y=df['polygon_y'][p_idx]))
                trace_count += 1

        min = -20
        max = 80
        z_made_up = np.full_like(ds.DBZ.data[0,z_step], 37)

        z_max = np.max(ds.DBZ[0], axis=0, keepdims=True)
        z = np.nan_to_num(z_max[0].data, nan=-20)

        # z_mean = np.mean(ds.DBZ[0], axis=0, keepdims=True)
        # z = np.nan_to_num(z_mean[0].data, nan=-20)
  
        #z_normalized = [(n-min)/(max-min) for n in np.nan_to_num(ds.DBZ.data[0,z_step], nan=-32)]
        fig.add_trace(
            go.Heatmap(
                visible=False,
                x=x, y=y,
                #z=z_made_up, # z needs to be between zmin and zmax
                # z=np.nan_to_num(ds.DBZ.data[0,z_step], nan=-20),   # z needs to be between (zmin,zmax) interval !!! 
                # z_step of 4 in roughly the median height of the storm tracks.
                # z=np.nan_to_num(ds.DBZ.data[0,4], nan=-20),   # z needs to be between (zmin,zmax) interval !!! 
                z = z,
                #z=z_normalized,
                type='heatmap', 
                colorscale=colorscale_for_go,
                #colorscale=[
                #    [0,   'rgb(0,0,255)'],
                #    [0.5, 'rgb(255,0,255)'],
                #    [1,   'rgb(0,255,0)'],
                #    ],
                #line=dict(color="#00CED1", width=6),
                # create a discrete colorscale by setting the same reference point twice in a row
                colorbar=dict(
                    title='dBZ',
                    # lineposition="through",
                    tickvals=colorscale_ticks, # [0,40,80],  # in data coordinates
                    ticktext=colorscale_labels,
                    # lenmode="pixels", len=100,
                ),
                name="v = " + str(step),
                zmin=-20, zmax=80,
                ), row=1, col=1)
        
        trace_count += 1

        if True:  # step < 15:  # works up to 11
            
            time_step = datetime(int(file[4:8]),int(file[8:10]),int(file[10:12]),
                int(file[13:15]),int(file[15:17]),int(file[17:19]),tzinfo=timezone.utc)
            # >>> fns2.isoformat()
            # '2022-05-21T15:05:50+00:00'
    
            # sbts_key = time_step.isoformat()
            sbts_key = time_step.strftime('%Y%m%d_%H%M%S')
            # print("sbts ...:", sbts)
            if sbts_key in sbts:
                # print("key found", sbts_key)
                storm_simple_nums_str = sbts[sbts_key]
    
                storm_simple_nums = storm_simple_nums_str                

                all_storms_t1 = [vol_centroid_w_labels(s,df_complete) for s in storm_simple_nums]
                # !!!!!!! HERE !!!!!!
                #all_storms_t1 = [ ( ['129', '157', ''], (-57.7924, '-55.6891', None), (56.6318, '67.0433', None) ), ([],[],[]),
                #    (['1', '120', '', '1', '121', ''], ('74.2478', 75.3205, None, '74.2478', 74.5952, None), ('-70.1', -64.1667, None, '-70.1', -57.3571, None)),
                #    ([],[],[]),
                #    ([],[],[])
                #    ]
                # It's a threshold thing!  Too many storms in legend? YES!!!
                #all_storms_t1 = [([], [], []),
                #    (['1', '120', '', '1', '121', ''], ('74.2478', 75.3205, None, '74.2478', 74.5952, None), ('-70.1', -64.1667, None, '-70.1', -57.3571, None)),
                #    (['3', '55', ''], ('97.2773', 101.052, None), ('-59.6616', -55.5795, None)), #---
                #    (['4', '55', ''], ('106.732', 101.052, None), ('-53.9638', -55.5795, None)),
                #    (['7', '56', ''], ('91.1563', 104.887, None), ('-31.3067', -2.08517, None)),
                #    (['9', '56', ''], ('90.6349', 104.887, None), ('4.20364', -2.08517, None)),
                #    (['11', '56', ''], ('116.127', 104.887, None), ('3.54015', -2.08517, None)),
                #    (['12', '56', ''], ('101.342', 104.887, None), ('2.16818', -2.08517, None)),
                #    (['13', '77', ''], ('73.6538', 77.5762, None), ('-1.76154', 18.4703, None)),
                #    (['15', '77', ''], ('71.6711', 77.5762, None), ('8.99123', 18.4703, None)),
                #    (['51', '77', ''], ('81.7941', 77.5762, None), ('22.3235', 18.4703, None)),
                #    (['53', '105', ''], ('114.87', 120.864, None), ('-27.9074', 2.13787, None)),
                #    ([], [], []),
                #    (['8', '75', '', '8', '76', ''], ('-0.0580247', -5.08333, None, '-0.0580247', 3.1036, None), ('-18.0753', -19.9167, None, '-18.0753', -11.5811, None)), 
                #    ([], [], []),
                #    ]
                #print("all_storms_t1: ", all_storms_t1)
                
                # add the storm tracks as arrows for this time step
                # fig.add_trace(go.Scatter(x=df['VolCentroidX(km)'], y=df['VolCentroidY(km)'],mode='lines+markers'))
                # df[(df["SimpleNum"] == 3)] 
                # use keyword None to break parents and children into segments
                # format of coordinates: x|y=[current, child, None, current, child, None ...]
                #child_x, child_y = prepare_child_connections(df_complete, time_step_key, 'child')
                #parent_x, parent_y = prepare_parent_connections(df_complete, time_step_key, 'parent')
                #for (simple_num_s, xs, ys) in all_storms_t1:
                for (labels, xs, ys) in all_storms_t1:
                    if len(labels) > 0:
                        name = labels[0]
                        # fig.add_trace(go.Scatter(x=[-100,100,None,-100,100], y=[-100,100,None,-100,-100],
                        fig.add_trace(go.Scatter(x=xs, y=ys, 
                            visible=False,
                            #text=[str(simple_num_s),"end","dummy"], 
                            name=name,
                            text=labels, 
                            #text=str(simple_num_s), 
                            mode="text+lines+markers",
                            # textposition='top right', 
                            textfont=dict(color='white', size=15),
                            marker= dict(size=15,symbol= "arrow-bar-up", angleref="previous",
                            color="white")))
                        fig.update_layout(legend=dict(
                            title_text="Storm Simple Number",
                            orientation="v", # "h",               ### HERE !!!
                            yanchor="top", # "bottom",
                            y=1, # 1.02,
                            xanchor="right",
                            x=1,
                        ))
                        trace_count += 1
    
            else:
                print("no key found", sbts_key)
        
        map_trace_indexes.append(trace_count)

        #fig.add_trace(time_fig, row=1, col=1, secondary_y=False)
    
    # Make 10th trace visible
    #fig.data[0].visible = True
    
    # to make image square 
    fig.update_layout(yaxis_scaleanchor="x")
    #fig.update_xaxes(
    #    scaleanchor="y",
    #    scaleratio=1
    #)
   
    # print("map indexes: ", map_trace_indexes)
 
    # Create and add slider
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                  {"title": "Slider switched to step: " + str(i)}],  # layout attribute
            label=i # filenames[i][13:19]
            #label=filenames[i][13:19]
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        if i in map_trace_indexes:
            file_num = map_trace_indexes.index(i)
            step['label'] = filenames[file_num][13:19]
            end_trace = i
            # fix up the traces, there are more now, with the storm lineage
            if file_num > 0:
                start_polygon_trace = map_trace_indexes[file_num-1] + 1
            else:
                start_polygon_trace = 1
            for j in range(start_polygon_trace,end_trace+1):
                step["args"][0]["visible"][j] = True  # Toggle associated polygon traces to "visible"
            steps.append(step)
    
    sliders = [dict(
        active=0,  # was 1
        currentvalue={"prefix": "time step (HHMMSS): "},
        pad={"t": 50},
        steps=steps
    )]
    
    fig.update_layout(
        sliders=sliders
    )
    
    return fig
```


```{code-cell} ipython3
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# extract the polygons from the data frame and convert to cartesian coords

# Convert date and time columns to datetime
#df['date_utc'] = pd.to_datetime(
#    df['Year'].astype(str) + '-' +
#    df['Month'].astype(str).str.zfill(2) + '-' +
#    df['Day'].astype(str).str.zfill(2) + ' ' +
#    df['Hour'].astype(str).str.zfill(2) + ':' +
#    df['Min'].astype(str).str.zfill(2) + ':' +
#    df['Sec'].astype(str).str.zfill(2),
#    format='%Y-%m-%d %H:%M:%S',
#    utc=True
#)

def get_polygons_cart(df):

    utc_list = []
    polygons_x_list = []
    polygons_y_list = []

    for idx, row in df.iterrows():
        centroid_x = float(row['VolCentroidX(km)'])
        centroid_y = float(row['VolCentroidY(km)'])
        centroid_z = float(row['VolCentroidZ(km)'])
        rays = row['nPolySidesPolygonRays']
        
        if not rays or len(rays) == 0:
            continue  
        
        angles = np.deg2rad(np.arange(0, 360, 5))  # 72 vertices at every 5 degrees
        rays = np.array(rays, dtype=float) #from centroid to vertex
        
        # Rays in km to degrees
        ray_x = rays * np.cos(angles)
        ray_y = rays * np.sin(angles)
    
        # Approximate conversion from km to degrees lat/lon
        #lat_vertices = lat_centroid + ray_y / 111
        #lon_vertices = lon_centroid + ray_x / (111 * np.cos(np.deg2rad(lat_centroid)))
 
        y_vertices = centroid_y + ray_y
        x_vertices = centroid_x + ray_x

        # add the first point to the end of the list to complete the polygon
        y_vertices = np.append(y_vertices, y_vertices[0])
        x_vertices = np.append(x_vertices, x_vertices[0])
    
        ##polygon_points = list(zip(lon_vertices, lat_vertices))
        #polygon_points = list(zip(x_vertices, y_vertices))
        
        #poly = Polygon(polygon_points)
        #time_idx = np.where(timesteps == row['date_utc'])[0][0]
        time_utc = row['date_utc']
  
        utc_list.append(time_utc) 
        polygons_x_list.append(x_vertices) 
        polygons_y_list.append(y_vertices) 

        #ax.add_geometries([poly], crs=ccrs.PlateCarree(),
        #                  edgecolor=palette[time_idx], facecolor='none', linewidth=1)
        
        #ax.plot(lon_centroid, lat_centroid, marker='o',color='grey', markersize=1.5, transform=ccrs.PlateCarree())
    
      
   
    d = {'utc': utc_list, 'polygon_x': polygons_x_list, 'polygon_y': polygons_y_list}
    df = pd.DataFrame(data=d)  
    
    return df  

```


```{code-cell} ipython3

df = ascii_to_df(file)
df.sort_values('date_utc')

df_polys = get_polygons_cart(df)

fig = plot_with_timefile_slider(z_step, path, df_polys, df)
```


```{code-cell} ipython3
#fig.show(renderer="jupyterlab")
```


```{code-cell} ipython3
#fig.show(renderer="iframe")
```


```{code-cell} ipython3
fig
```
