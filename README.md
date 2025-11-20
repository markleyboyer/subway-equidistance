# NYC Subway Equidistance Map

An interactive visualization showing travel time zones and equidistant areas between any two NYC subway stations.

## Features

- **Interactive Station Selection**: Click any two subway stations to compare their reach
- **Isochrone Visualization**: See 10, 20, 30, and 40-minute travel zones (subway + walking)
- **Equidistance Zones**: Stations within 5 minutes of being equally reachable from both origins are highlighted in green with white rings
- **Color-Coded Display**: 
  - Yellow areas: Closer to Station A
  - Blue areas: Closer to Station B
  - Green stations with white rings: Equidistant (within 5 minutes)
- **Travel Time Tooltips**: Hover over any station to see exact travel times from both selected stations
- **Dark Theme UI**: Clean, modern interface with black backgrounds
- **Debug Console**: Real-time event tracking visible on screen

## Live Demo

🚇 [View the live demo](https://subway-equidistance.web.app)

## Quick Start

1. Open `subway-equidistance-final.html` in your web browser
2. Click on any subway station to select **Station A** (appears in yellow)
3. Click on a different station to select **Station B** (appears in blue)
4. Watch the map generate isochrones and highlight equidistant zones!
5. Hover over any station to see exact travel times from both origins
6. Click "Reset Selection" to start over

## How It Works

This implementation follows the exact approach used by subwaysheds.com:

1. **Travel Times**: Uses pre-computed subway travel times between all station pairs
2. **Walking Buffers**: Creates walking zones (1.2 m/s = 72 m/min) around reachable stations
3. **Turf.js**: Performs geometric operations to union buffers into isochrone polygons
4. **Visualization**: Displays overlapping zones to show equidistant areas

## Using Real GTFS Data

The current version uses **realistic sample data** for ~20 major NYC stations. To use real MTA data:

### Step 1: Download GTFS Data

```bash
# Download the latest MTA subway GTFS data
curl -o gtfs_subway.zip "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
unzip gtfs_subway.zip -d gtfs_data/
```

### Step 2: Process GTFS Data

```bash
# Install Python dependencies
pip install --break-system-packages csvkit

# Run the processing script
python process_gtfs.py --gtfs-dir ./gtfs_data --output travel_times_full.json
```

This will create `travel_times_full.json` containing travel times for ALL ~470 subway stations!

### Step 3: Update the HTML

1. Open `subway-equidistance-final.html` in a text editor
2. Find the line with the embedded JSON data (search for `"stations"`)
3. Replace that entire JSON object with the contents of `travel_times_full.json`
4. Save and open in your browser

## Data Format

The JSON file contains:

```json
{
  "stations": {
    "station_id": {
      "id": "station_id",
      "name": "Station Name",
      "lat": 40.xxxx,
      "lon": -73.xxxx
    }
  },
  "travel_times": {
    "station_id": {
      "other_station_id": 15.5  // minutes
    }
  }
}
```

## Technical Details

- **Map Library**: MapLibre GL JS (open source)
- **Geometry**: Turf.js for buffer and union operations
- **Travel Time Calculation**: Dijkstra's algorithm on subway network graph
- **Walking Speed**: 1.2 m/s (MTA standard)
- **Time Intervals**: 10, 20, 30, 40 minutes

## Customization Ideas

1. **Add more time intervals**: Modify the `timeIntervals` array in `createIsochrone`
2. **Change colors**: Update the `colorsA` and `colorsB` arrays
3. **Adjust walking speed**: Change the `72` value (meters/minute)
4. **Filter by time of day**: Process GTFS data for specific times (rush hour vs late night)

## Comparison to Original

**Original (subwaysheds.com)**:
- Uses R's `gtfsrouter` package for GTFS processing
- Shows single-station isochrones on hover
- Full coverage of all MTA subway stations

**This Version**:
- Pure JavaScript + Python implementation
- Shows equidistant zones between TWO stations
- Easily customizable and self-contained

## Troubleshooting

**Map doesn't load**: 
- Check browser console (F12) for errors
- Make sure you're not blocking JavaScript

**Stations don't click**:
- Wait for map to fully load (stations should appear)
- Try refreshing the page

**Want more stations**:
- Follow "Using Real GTFS Data" instructions above

## Next Steps

1. **Add all 470 stations**: Process full GTFS data
2. **Add time-of-day selector**: Calculate different travel times for rush hour vs late night
3. **Show actual boundary line**: Calculate and draw the exact equidistant boundary
4. **Add route information**: Show which subway lines serve each zone

## Credits

Inspired by:
- **subwaysheds.com** by Chris Whong - Original NYC subway isochrone visualization
- **chronotrains.com** by Benjamin TD - European train isochrones
- **MTA GTFS data** - Official NYC transit schedules

## License

MIT License - Feel free to modify and use!
