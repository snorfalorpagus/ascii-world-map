import json
from functools import partial
from shutil import get_terminal_size
from shapely.geometry import shape, Point
from shapely import ops
import pyproj
import rtree

# read the data into a list of shapely geometries
with open("world-countries.json") as f:
    data = json.load(f)
geoms = [shape(feature["geometry"]) for feature in data["features"]]

# transform the geometries into web mercator
wgs84 = pyproj.Proj(init="EPSG:4326")
webmerc = pyproj.Proj(proj="webmerc")
t = partial(pyproj.transform, wgs84, webmerc)
geoms = [ops.transform(t, geom) for geom in geoms]

# create a spatial index of the geometries
def gen(geoms):
    for n, geom in enumerate(geoms):
        yield n, geom.bounds, geom
index = rtree.index.Index(gen(geoms))

# get the window size
size = get_terminal_size(fallback=(80, 24))
columns = size.columns
lines = size.lines - 1  # allow for prompt at bottom

# calculate the projected extent and pixel size
xmin, ymin = t(-180, -85)
xmax, ymax = t(180, 85)
pixel_width = (xmax - xmin) / columns
pixel_height = (ymax - ymin) / lines

land = "*"
water = " "

for line in range(lines):
    for col in range(columns):
        # get the projected x, y of the pixel centroid
        x = xmin + (col + 0.5) * pixel_width
        y = ymax - (line + 0.5) * pixel_height
        # check for a collision
        objects = [n.object for n in index.intersection((x, y, x, y), objects=True)]
        value = False
        for geom in objects:
            value = geom.intersects(Point(x, y))
            if value:
                break
        print(land if value else water, end="")
    print("")

