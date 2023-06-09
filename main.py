import geopandas as gpd
import laspy
import json
from shapely.geometry import Polygon
from copy import deepcopy
import pyogrio



                                '''part 1: extract the lost buildings footprints '''
''' to use this function one has to have a point cloud containing the buildings that were lost and a shapefile containing the 
    footprints of the buildings extracted from a cityjson model using the ciyjson loader plugin in qgis for example'''' 

def extracting_lost_footprints(fp, pc, threshold, disappeared_fp):
    # read the shapefile containing footprints
    footprints = gpd.read_file(fp)
    footprints.to_crs("EPSG:28992")

    # read the point cloud
    point_cloud = laspy.read(pc)

    # create a GeoDataFrame from the x,y coordinates of the point cloud
    points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
        point_cloud.x, point_cloud.y), crs="EPSG:28992")

    # checking if a certain threshold of points intersect with each polygon in the footprints, if the condition is filled the polygons are appended into a geodataframe
    filtered_polys = []
    for poly in footprints.geometry:
        poly_points = points[points.intersects(poly)]
        if len(poly_points) >= threshold:
            filtered_polys.append(poly)
        output = gpd.GeoDataFrame(
            geometry=filtered_polys,  crs="EPSG:28992")

    # Perform a spatial join between filtered_clipped and model_footprints based on the geometry
    output = gpd.sjoin(output, footprints,
                       how="inner", predicate="within")

    return output.to_file(disappeared_fp)

  
  
                             '''part 2: delete the lost buildings from the CityJSON file'''
    
 def delete_lost_from_model(fp_lost, model, output_model):
    # read the CityJSON file
    with open(model) as file:
        cityjson_data = json.load(file)

    # Read the shapefile containing footprints
    footprints = gpd.read_file('disappeared_buildings.shp')

    # Get the attributes from the shapefile that correspond to the buildings' identifiers
    building_ids = footprints['uid']
    building_ids = list(building_ids)

    children_ids = footprints['children']
    children_ids = list(children_ids)
    children_ids = [item[2:-2] for item in children_ids]
    children_ids = [item.split("', '") for item in children_ids]
    children_ids1 = []
    for elem in children_ids:
        if isinstance(elem, list) and len(elem) > 1:
            children_ids1.extend([sub_elem] for sub_elem in elem)
        else:
            children_ids1.append(elem)
    children_ids1 = [item[0] for item in children_ids1]

    # Create a new CityJSON object
    new_cityjson_data = deepcopy(cityjson_data)

    # Remove buildings based on matching with the foorprints' identifiers in the disappeared_buildings.shp file
    for (key, value) in cityjson_data['CityObjects'].items():
        if key in building_ids:
            new_cityjson_data['CityObjects'].pop(key)

    for (key, value) in cityjson_data['CityObjects'].items():
        if key in children_ids1:
            new_cityjson_data['CityObjects'].pop(key)

    # Save the new CityJSON file
    with open(output_model, 'w') as file:
        json.dump(new_cityjson_data, file)
