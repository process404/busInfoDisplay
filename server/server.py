from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import zipfile
from datetime import datetime
from flask import request
from dotenv import load_dotenv
import os
import requests
import json
import xml.etree.ElementTree as ET
from math import radians, cos, sin, sqrt, atan2, degrees


app = Flask(__name__)
CORS(app) 


def process_gtfs(zip_path, lat_min, lat_max, long_min, long_max, banned_stop, route_id_array):

    print(banned_stop)
    # Boundaries in case of duplicates in the region of the gtfs file
    filter_lat_min, filter_lat_max = lat_min, lat_max
    filter_long_min, filter_long_max = long_min, long_max

    # Open the GTFS zip file
    with zipfile.ZipFile(zip_path) as z:
        # Read routes, trips, stop_times, stops, calendar, calendar_dates, and agency
        with z.open('routes.txt') as f:
            routes = pd.read_csv(f)
        with z.open('trips.txt') as f:
            trips = pd.read_csv(f)
        with z.open('stop_times.txt') as f:
            stop_times = pd.read_csv(f)
        with z.open('stops.txt') as f:
            stops = pd.read_csv(f)
        with z.open('calendar.txt') as f:
            calendar = pd.read_csv(f)
        with z.open('calendar_dates.txt') as f:
            calendar_dates = pd.read_csv(f)
        with z.open('agency.txt') as f:  # Reading agency data
            agency = pd.read_csv(f)


    routes_with_agency = pd.merge(routes, agency, on='agency_id', how='left')


    route_ids = route_id_array
    filtered_routes = routes_with_agency[routes_with_agency['route_short_name'].isin(route_ids)]


    filtered_trips = trips[trips['route_id'].isin(filtered_routes['route_id'])]


    trips_with_calendar = pd.merge(filtered_trips, calendar, on='service_id')


    trip_stop_times = pd.merge(trips_with_calendar, stop_times, on='trip_id')
    trip_stops = pd.merge(trip_stop_times, stops, on='stop_id')

    filter_trips = trip_stops[(trip_stops['stop_lat'] >= filter_lat_min) & 
                              (trip_stops['stop_lat'] <= filter_lat_max) & 
                              (trip_stops['stop_lon'] >= filter_long_min) & 
                              (trip_stops['stop_lon'] <= filter_long_max)]


    no_service_dates = calendar_dates[calendar_dates['exception_type'] == 2]

    routes_json = {}
    all_stops = {}


    for route_id, group in filter_trips.groupby('route_id'):
        route_info = filtered_routes[filtered_routes['route_id'] == route_id].iloc[0]
        route_name = route_info['route_short_name']
        operator_name = route_info['agency_name']  # Operator's name for the current route
        routes_json[route_name] = {'journeys': [], 'operator': operator_name}
        
        # Initialize a set to track processed trip_ids for the current route
        processed_trip_ids = set()
        
        for trip_id, trip_group in group.groupby('trip_id'):
            # Check if trip_id has already been processed
            if trip_id in processed_trip_ids:
                continue  # Skip this trip_id as it's already processed
            
            # Add trip_id to the set of processed trip_ids
            processed_trip_ids.add(trip_id)
            
            trip_group_sorted = trip_group.sort_values(by='departure_time')
            trip_service_id = trip_group_sorted['service_id'].iloc[0]
            trip_no_service_dates_strings = no_service_dates[no_service_dates['service_id'] == trip_service_id]['date'].tolist()
            trip_no_service_dates = [datetime.strptime(str(date_int), '%Y%m%d').strftime('%d/%m/%Y') for date_int in trip_no_service_dates_strings]
            journey = {
                'trip_id': trip_id,
                'running_days': trip_group_sorted[['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']].iloc[0].to_dict(),
                'stop_times': trip_group_sorted[['arrival_time', 'departure_time', 'stop_name', 'stop_lat', 'stop_lon']].to_dict('records'),
                'no_service_dates': trip_no_service_dates,
                'destination': trip_group_sorted['trip_headsign'].iloc[0]  # Add the destination to the journey
            }

            print(route_name, journey.get('running_days'))
            routes_json[route_name]['journeys'].append(journey)
            for stop_time in journey['stop_times']:
                stop_name = stop_time['stop_name']
                if stop_name not in all_stops:
                    all_stops[stop_name] = {'routes': set(), 'stop_lat': stop_time['stop_lat'], 'stop_lon': stop_time['stop_lon']}
                all_stops[stop_name]['routes'].add(route_name)


    all_stops_list = [{'stop_name': k, 'routes': list(v['routes']), 'stop_lat': v['stop_lat'], 'stop_lon': v['stop_lon']} for k, v in all_stops.items() if banned_stop is not None and k.lower() != banned_stop.lower()]

 
    final_structure = {"routes": routes_json, "allStops": all_stops_list}

    return final_structure



@app.route('/gtfs-data', methods=['GET'])
def get_gtfs_data():
    zip_path = request.args.get('zip_path')
    lat_min = float(request.args.get('min_lat'))
    lat_max = float(request.args.get('max_lat'))
    long_min = float(request.args.get('min_long'))
    long_max = float(request.args.get('max_long'))
    banned_stop = request.args.get('banned_onward_connection_stop')
    routes_to_include = request.args.getlist('routes_to_include[]')

    print(zip_path, lat_min, lat_max, long_min, long_max, banned_stop,  routes_to_include)

    processed_data = process_gtfs(zip_path, lat_min, lat_max, long_min, long_max, banned_stop, routes_to_include)

    return jsonify(processed_data)
   

@app.route('/tracking-data', methods=['GET'])
def get_tracking_data():
    load_dotenv()

    min_lat = float(request.args.get('min_lat'))
    max_lat = float(request.args.get('max_lat'))
    min_long = float(request.args.get('min_long'))
    max_long = float(request.args.get('max_long'))

    this_stop_long = float(request.args.get('this_stop_long'))
    this_stop_lat = float(request.args.get('this_stop_lat'))


    request.args.getlist('allstops[]')
    routeNumber = request.args.get('routeNumber')


    env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_file_path)
    api_key = os.getenv('VUE_APP_API_KEY')

    def get_datafeed(api_key):
        bounding_box = f"?boundingBox={min_long},{min_lat},{max_long},{max_lat}&lineRef={routeNumber}"
        url = f"https://data.bus-data.dft.gov.uk/api/v1/datafeed/{bounding_box}&api_key={api_key}"
        print(url)
        response = requests.get(url)

        response_xml = response.text

        def extract_latitude_from_xml(xml_data):
            try:
                namespaces = {'ns': 'http://www.siri.org.uk/siri'}
                root = ET.fromstring(xml_data)
                latitude_element = root.find('.//ns:VehicleLocation/ns:Latitude', namespaces=namespaces)
                latitude = latitude_element.text if latitude_element is not None else None
            except Exception as e:
                print(f"Error extracting latitude from XML: {e}")
                latitude = None
            return latitude

        def extract_longitude_from_xml(xml_data):
            try:
                namespaces = {'ns': 'http://www.siri.org.uk/siri'}
                root = ET.fromstring(xml_data)
                longitude_element = root.find('.//ns:VehicleLocation/ns:Longitude', namespaces=namespaces)
                longitude = longitude_element.text if longitude_element is not None else None
            except Exception as e:
                print(f"Error extracting longitude from XML: {e}")
                longitude = None
            return longitude

        def extract_bearing_from_xml(xml_data):
            try:
                namespaces = {'ns': 'http://www.siri.org.uk/siri'}
                root = ET.fromstring(xml_data)
                bearing_element = root.find('.//ns:Bearing', namespaces=namespaces)
                bearing = float(bearing_element.text) if bearing_element is not None else None
            except Exception as e:
                print(f"Error extracting bearing from XML: {e}")
                bearing = None
            return bearing

        latitude = extract_latitude_from_xml(response_xml)
        longitude = extract_longitude_from_xml(response_xml)

        def haversine(lat1, lon1, lat2, lon2):
            # Radius of the Earth in kilometers
            R = 6371.0
            # Convert latitude and longitude from degrees to radians
            lat1_rad = radians(lat1)
            lon1_rad = radians(lon1)
            lat2_rad = radians(lat2)
            lon2_rad = radians(lon2)
            # Difference in coordinates
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            # Haversine formula
            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c
            return distance
        
        def calculate_bearing(lat1, lon1, lat2, lon2):
            lat1_rad, lat2_rad = radians(lat1), radians(lat2)
            diff_lon_rad = radians(lon2 - lon1)
            x = sin(diff_lon_rad) * cos(lat2_rad)
            y = cos(lat1_rad) * sin(lat2_rad) - (sin(lat1_rad) * cos(lat2_rad) * cos(diff_lon_rad))
            initial_bearing = atan2(x, y)
            initial_bearing = degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360
            return compass_bearing
        
        distance = haversine(float(latitude), float(longitude), float(this_stop_lat), float(this_stop_long))
        bearing_to_stop = calculate_bearing(float(latitude), float(longitude), float(this_stop_lat), float(this_stop_long))
        bus_bearing = extract_bearing_from_xml(response_xml)
        # Define a tolerance for bearing comparison
        bearing_tolerance = 90 # degrees

        meters = distance * 1000
        estimated_time = (distance / 30) * 60 # distance / speed (kmh) * distance

        # Ensure meters is not negative
        meters = max(meters, 0)
        if meters >= 1000:  # Correctly using meters for comparison
            percentage = 0
        else:
            percentage = (1 - (meters / 1000)) * 100

        towardsStop = False
        withinRadius = False

        if abs(bearing_to_stop - bus_bearing) <= bearing_tolerance:
            print("The bus is moving towards the bus stop.")
            towardsStop = True
            withinRadius = False
        else:
            print("The bus is moving away from the bus stop.")

            if meters <= 220:
                towardsStop = True
                withinRadius = True
            else:
                towardsStop = False
                withinRadius = False
        
        finalJson = {
            "latitude": latitude,
            "longitude": longitude,
            "distance": meters,
            "estimated_time": estimated_time,
            "percentage": percentage,
            "towardsStop": towardsStop  ,
            "withinRadius":withinRadius
        }

    
        return jsonify(finalJson)
    

    
    return get_datafeed(api_key)

if __name__ == '__main__':
    app.run(debug=True)
