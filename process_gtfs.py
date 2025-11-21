#!/usr/bin/env python3
"""
Process MTA GTFS data to create travel time matrix for subway stations.

This script:
1. Reads GTFS files (stops.txt, stop_times.txt, trips.txt, routes.txt)
2. Builds a graph of subway connections
3. Calculates travel times between all station pairs using Dijkstra's algorithm
4. Outputs JSON files for use in the web visualization

Usage:
    python process_gtfs.py --gtfs-dir ./gtfs_data --output ./travel_times.json
"""

import csv
import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import heapq

@dataclass
class Station:
    id: str
    name: str
    lat: float
    lon: float
    
@dataclass
class Connection:
    from_stop: str
    to_stop: str
    travel_time: float  # minutes
    route: str

def read_stops(gtfs_dir: str) -> Dict[str, Station]:
    """Read stops.txt and return station info."""
    stations = {}
    stops_file = f"{gtfs_dir}/stops.txt"
    
    with open(stops_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include subway stations (location_type = 1 or parent stations)
            # Filter out platform-level stops, keep only station-level
            stop_id = row['stop_id']
            
            # Exclude Staten Island Railway (all S stations)
            if stop_id.startswith('S'):
                continue
            
            # MTA uses parent station IDs - exclude platform-specific stops that end with N or S
            # But keep station IDs that have N or S in the middle (like N06)
            if not (stop_id.endswith('N') or stop_id.endswith('S')):
                stations[stop_id] = Station(
                    id=stop_id,
                    name=row['stop_name'],
                    lat=float(row['stop_lat']),
                    lon=float(row['stop_lon'])
                )
    
    return stations

def build_connections(gtfs_dir: str) -> List[Connection]:
    """Build connections between stations from stop_times and trips."""
    connections = []
    
    # Read trips to get route info
    trip_routes = {}
    with open(f"{gtfs_dir}/trips.txt", 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trip_routes[row['trip_id']] = row['route_id']
    
    # Read stop_times and build connections
    trip_stops = defaultdict(list)
    
    with open(f"{gtfs_dir}/stop_times.txt", 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trip_id = row['trip_id']
            stop_id = row['stop_id']
            
            # Remove direction suffix (N or S) only if it's at the end
            if stop_id.endswith('N') or stop_id.endswith('S'):
                stop_id = stop_id[:-1]
            
            # Exclude Staten Island Railway
            if stop_id.startswith('S'):
                continue
            
            # Parse time
            arrival_time = row['arrival_time']
            h, m, s = map(int, arrival_time.split(':'))
            arrival_minutes = h * 60 + m
            
            trip_stops[trip_id].append((
                int(row['stop_sequence']),
                stop_id,
                arrival_minutes
            ))
    
    # Create connections from sequential stops in each trip
    for trip_id, stops in trip_stops.items():
        if trip_id not in trip_routes:
            continue
            
        route = trip_routes[trip_id]
        stops.sort(key=lambda x: x[0])  # Sort by sequence
        
        for i in range(len(stops) - 1):
            _, from_stop, from_time = stops[i]
            _, to_stop, to_time = stops[i + 1]
            
            travel_time = to_time - from_time
            if travel_time > 0 and travel_time < 30:  # Reasonable travel times only
                connections.append(Connection(
                    from_stop=from_stop,
                    to_stop=to_stop,
                    travel_time=travel_time,
                    route=route
                ))
    
    return connections

def average_connections(connections: List[Connection]) -> Dict[Tuple[str, str], float]:
    """Average multiple connections between same station pairs."""
    connection_times = defaultdict(list)
    
    for conn in connections:
        key = (conn.from_stop, conn.to_stop)
        connection_times[key].append(conn.travel_time)
    
    averaged = {}
    for key, times in connection_times.items():
        averaged[key] = sum(times) / len(times)
    
    return averaged

def dijkstra(graph: Dict[str, List[Tuple[str, float]]], start: str, max_time: float = 40) -> Dict[str, float]:
    """Calculate shortest travel times from start station using Dijkstra's algorithm."""
    distances = {start: 0.0}
    pq = [(0.0, start)]
    visited = set()
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        if current_node in visited:
            continue
        if current_dist > max_time:
            continue
            
        visited.add(current_node)
        
        if current_node not in graph:
            continue
            
        for neighbor, weight in graph[current_node]:
            distance = current_dist + weight
            
            if distance <= max_time and (neighbor not in distances or distance < distances[neighbor]):
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

def build_graph(averaged_connections: Dict[Tuple[str, str], float]) -> Dict[str, List[Tuple[str, float]]]:
    """Build adjacency list graph from connections."""
    graph = defaultdict(list)
    
    for (from_stop, to_stop), time in averaged_connections.items():
        graph[from_stop].append((to_stop, time))
        # Add reverse connection (assuming similar travel time)
        graph[to_stop].append((from_stop, time))
    
    return dict(graph)

def add_transfers(graph: Dict[str, List[Tuple[str, float]]], gtfs_dir: str) -> Dict[str, List[Tuple[str, float]]]:
    """Add transfer connections to the graph."""
    transfers_file = f"{gtfs_dir}/transfers.txt"
    
    try:
        with open(transfers_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                from_stop = row['from_stop_id']
                to_stop = row['to_stop_id']
                
                # Skip Staten Island Railway transfers
                if from_stop.startswith('S') or to_stop.startswith('S'):
                    continue
                
                # Skip self-transfers
                if from_stop == to_stop:
                    continue
                
                # Get transfer time in minutes (default 2 minutes if not specified)
                transfer_time = float(row.get('min_transfer_time', 120)) / 60  # Convert seconds to minutes
                
                # Add transfer connection (bidirectional)
                if from_stop not in graph:
                    graph[from_stop] = []
                if to_stop not in graph:
                    graph[to_stop] = []
                    
                graph[from_stop].append((to_stop, transfer_time))
                graph[to_stop].append((from_stop, transfer_time))
                
    except FileNotFoundError:
        print("Warning: transfers.txt not found, skipping transfer connections")
    
    return graph

def main(gtfs_dir: str, output_file: str):
    print("Reading GTFS data...")
    
    # Read stations
    stations = read_stops(gtfs_dir)
    print(f"Found {len(stations)} stations")
    
    # Build connections
    print("Building connections from trips...")
    connections = build_connections(gtfs_dir)
    print(f"Found {len(connections)} connections")
    
    # Average duplicate connections
    print("Averaging connection times...")
    averaged_connections = average_connections(connections)
    
    # Build graph
    print("Building graph...")
    graph = build_graph(averaged_connections)
    
    # Add transfers
    print("Adding transfer connections...")
    graph = add_transfers(graph, gtfs_dir)
    
    # Calculate travel times from each station
    print("Calculating travel time matrix...")
    travel_times = {}
    
    for i, station_id in enumerate(stations.keys()):
        if i % 10 == 0:
            print(f"Processing station {i+1}/{len(stations)}")
        
        times = dijkstra(graph, station_id, max_time=120)  # Increased to 120 minutes (2 hours)
        travel_times[station_id] = times
    
    # Prepare output
    output = {
        'stations': {
            sid: {
                'id': s.id,
                'name': s.name,
                'lat': s.lat,
                'lon': s.lon
            }
            for sid, s in stations.items()
        },
        'travel_times': travel_times
    }
    
    # Write output
    print(f"Writing to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Done!")
    print(f"\nTo use this data:")
    print(f"1. Copy {output_file} to your web directory")
    print(f"2. Update the HTML to load this JSON file")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Process GTFS data for subway isochrones')
    parser.add_argument('--gtfs-dir', required=True, help='Directory containing GTFS files')
    parser.add_argument('--output', default='travel_times.json', help='Output JSON file')
    
    args = parser.parse_args()
    main(args.gtfs_dir, args.output)
