from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import zipfile
from datetime import datetime
import numpy as np


app = Flask(__name__)
CORS(app)  # Enable CORS


def process_gtfs(zip_path):
    # Boundaries in case of duplicates in the region of the gtfs file
    filter_lat_min, filter_lat_max = 53.55, 53.57
    filter_long_min, filter_long_max = -2.89, -2.87

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

    # Merge routes with agency to include operator names
    routes_with_agency = pd.merge(routes, agency, on='agency_id', how='left')

    # Filter routes for the specified route IDs
    route_ids = ['2A', '337', '312', '311', 'EL1', '5', '6', '152', '375', '385']
    filtered_routes = routes_with_agency[routes_with_agency['route_short_name'].isin(route_ids)]

    # Map trips to filtered routes
    filtered_trips = trips[trips['route_id'].isin(filtered_routes['route_id'])]

    # Merge trips with calendar to include running day information
    trips_with_calendar = pd.merge(filtered_trips, calendar, on='service_id')

    # Join trips with stop times, then join with stops to get locations
    trip_stop_times = pd.merge(trips_with_calendar, stop_times, on='trip_id')
    trip_stops = pd.merge(trip_stop_times, stops, on='stop_id')

    filter_trips = trip_stops[(trip_stops['stop_lat'] >= filter_lat_min) & 
                              (trip_stops['stop_lat'] <= filter_lat_max) & 
                              (trip_stops['stop_lon'] >= filter_long_min) & 
                              (trip_stops['stop_lon'] <= filter_long_max)]

    # Assuming calendar_dates DataFrame is already loaded and filtered for exception_type of 2
    no_service_dates = calendar_dates[calendar_dates['exception_type'] == 2]

    routes_json = {}
    all_stops = {}

    for route_id, group in filter_trips.groupby('route_id'):
        route_info = filtered_routes[filtered_routes['route_id'] == route_id].iloc[0]
        route_name = route_info['route_short_name']
        operator_name = route_info['agency_name']  # Operator's name for the current route
        routes_json[route_name] = {'journeys': [], 'operator': operator_name}
        for trip_id, trip_group in group.groupby('trip_id'):
            trip_group_sorted = trip_group.sort_values(by='departure_time')
            trip_service_id = trip_group_sorted['service_id'].iloc[0]
            trip_no_service_dates_strings = no_service_dates[no_service_dates['service_id'] == trip_service_id]['date'].tolist()
            trip_no_service_dates = [datetime.strptime(str(date_int), '%Y%m%d').strftime('%d/%m/%Y') for date_int in trip_no_service_dates_strings]
            journey = {
                'trip_id': trip_id,
                'running_days': trip_group_sorted[['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']].iloc[0].to_dict(),
                'stop_times': trip_group_sorted[['arrival_time', 'departure_time', 'stop_name']].to_dict('records'),
                'no_service_dates': trip_no_service_dates
            }
            routes_json[route_name]['journeys'].append(journey)
            for stop_time in journey['stop_times']:
                stop_name = stop_time['stop_name']
                if stop_name not in all_stops:
                    all_stops[stop_name] = {'routes': set()}
                all_stops[stop_name]['routes'].add(route_name)

    # Convert all_stops to the required list format and include route names as a list
    all_stops_list = [{'stop_name': k, 'routes': list(v['routes'])} for k, v in all_stops.items()]

    # Combine routes_json and all_stops_list into the final structure
    final_structure = {"routes": routes_json, "allStops": all_stops_list}

    return final_structure



@app.route('/gtfs-data', methods=['GET'])
def get_gtfs_data():
    processed_data = process_gtfs('../src/assets/itm_north_west_gtfs.zip')
    return jsonify(processed_data)

if __name__ == '__main__':
    app.run(debug=True)

