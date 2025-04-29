# PORTUGAL RADIATION PANEL (RADMAP)
# CODE: Pedro Lucas
# FILE: fetch.py

import requests
from datetime import datetime, timedelta
import json
import pandas as pd
import os
import mysql.connector
from dotenv import load_dotenv
import time
import coordinates

locations = []
location_info = []

# Load sensitive information
load_dotenv('.env')
host = os.getenv('MYSQL_HOST')
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database_name = os.getenv('MYSQL_DATABASE')
table_name = os.getenv('MYSQL_TABLE')

# Connect to MariaDB
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database_name
)
cursor = conn.cursor()

# Create table if it doesn't exist
create_table_query = f'''
CREATE TABLE IF NOT EXISTS {table_name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hour VARCHAR(20),
    place VARCHAR(100),
    value FLOAT,
    latitude FLOAT,
    longitude FLOAT
);
'''
cursor.execute(create_table_query)


def fetch():
    url = "https://radnet.apambiente.pt/ajax/dashboard/drawChart.php"

    start_time = datetime.now() - timedelta(hours=2)
    end_time = datetime.now()

    start_time_str = start_time.strftime('%d/%m/%Y %H:%M')
    end_time_str = end_time.strftime('%d/%m/%Y %H:%M')

    params = {
        'txtDataReport_start': start_time_str,
        'txtDataReport_end': end_time_str,
        'jsonEstacoesList': '[1652, 7251168, 1303, 1307, 7593370, 1305, 1201, 7593374, 1311, 1302, 1404, 1310, 1552, 2711862, 1351, 1501, 7593377, 1306, 2711807, 1309, 1304, 1308, 7593380, 1252, 7251171, 1651]'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        try:
            data = response.json()
            info = json.dumps(data)
            return info, start_time_str, end_time_str

        except ValueError:
            print("Error parsing response as JSON.")
    else:
        print(f"Request error: {response.status_code}")

def store(hour, place, value, latitude, longitude):
    # Check if value already exists in MariaDB
    cursor.execute(
        f"SELECT 1 FROM {table_name} WHERE hour=%s AND place=%s AND value=%s",
        (hour, place, value)
    )
    if cursor.fetchone() is None:
        # Insert data into the table
        cursor.execute(
            f"INSERT INTO {table_name} (hour, place, value, latitude, longitude) VALUES (%s, %s, %s, %s, %s)",
            (hour, place, value, latitude, longitude)
        )
        conn.commit()

def data_processing():
    info, hour_init, hour_end = fetch()
    data = json.loads(info)

    for i in range(len(data)):
        locations.append(data[i]["label"])
        location_info.append(data[i]["data"][int(len(data[i]["data"])) - 1][1])

    print(hour_init)
    print(hour_end)
    print(locations)
    print(location_info)
    i = 0
    for location in locations:
        j = 0
        latitude_value, longitude_value = coordinates.coordinates[location]
        value = location_info[i]
        for place in coordinates.coordinates:
            if place == location:
                new_place_name = coordinates.indexed[j]
                break
            if not (latitude_value and longitude_value):
                print(f"Coordinates not found for {location}")
            j += 1
        store(hour_init, new_place_name, value, latitude_value, longitude_value)
        i += 1
        time.sleep(0.2)

# data_processing()