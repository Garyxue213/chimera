"""
F1 Race Animator Backend Server
Uses local data for sessions, drivers, and telemetry
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = FastAPI(title="F1 Animation Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local data file
DATA_FILE = Path(__file__).parent / "austin_2025_data.json"

# OpenF1 API base URL
OPENF1_BASE = "https://api.openf1.org/v1"

# Cache for telemetry data
_telemetry_cache = {}
_local_data = {}

# Create session with retry strategy
def get_session_with_retries():
    """Create requests session with exponential backoff for rate limiting."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def api_request(url: str, params: Optional[Dict] = None, delay: float = 0.5) -> Optional[list]:
    """Make API request with rate limiting and retry logic."""
    try:
        time.sleep(delay)  # Rate limiting
        session = get_session_with_retries()
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Austin track bounds (empirically determined from OpenF1 location data)
# Using native OpenF1 coordinate system centered at (0, 0)
AUSTIN_TRACK_BOUNDS = {
    "min_x": -3000,
    "max_x": 2500,
    "min_y": -2500,
    "max_y": 2000,
}

# Pit lane zone (approximate area)
PIT_ZONE = {
    "min_x": 200,
    "max_x": 800,
    "min_y": 1500,
    "max_y": 1800,
}


def normalize_coordinates(x: float, y: float, bounds: Dict) -> tuple:
    """Transform raw OpenF1 coordinates to 0-1000 range using affine transformation."""
    min_x, max_x = bounds["min_x"], bounds["max_x"]
    min_y, max_y = bounds["min_y"], bounds["max_y"]
    range_x = max_x - min_x if max_x > min_x else 1
    range_y = max_y - min_y if max_y > min_y else 1

    # Affine transformation
    norm_x = ((x - min_x) / range_x) * 1000
    norm_y = ((y - min_y) / range_y) * 1000

    # Clamp to bounds
    norm_x = max(0, min(1000, norm_x))
    norm_y = max(0, min(1000, norm_y))

    return norm_x, norm_y


def is_in_pit_lane(x: float, y: float) -> bool:
    """Check if coordinates are in pit lane zone."""
    pit = PIT_ZONE
    return pit["min_x"] <= x <= pit["max_x"] and pit["min_y"] <= y <= pit["max_y"]


def load_local_data():
    """Load Austin sessions and drivers from local JSON file."""
    global _local_data
    if not _local_data and DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            _local_data = json.load(f)
    return _local_data

def get_austin_sessions(year: int = 2025) -> List[Dict]:
    """Get Austin race sessions from local data or recent past races."""
    data = load_local_data()
    sessions = data.get("sessions", []) if data else []

    # If no 2025 sessions, try to fetch from most recent past Austin race
    if not sessions:
        print(f"No local Austin sessions found, attempting to fetch from OpenF1 API...")
        # Query recent Austin GPs (2024, 2023, etc.)
        for past_year in range(2024, 2022, -1):
            all_sessions = api_request(
                f"{OPENF1_BASE}/sessions",
                params={"country_name": "United States", "year": past_year},
                delay=1.0
            )
            if all_sessions:
                # Filter for Austin circuit sessions
                austin_sessions = [s for s in all_sessions if "Austin" in s.get("location", "")]
                if austin_sessions:
                    print(f"Found {len(austin_sessions)} Austin sessions from {past_year}")
                    return austin_sessions

    return sessions


def fetch_drivers_for_session(session_key: int) -> Dict:
    """Get driver information from local data or OpenF1 API."""
    # Try local data first
    data = load_local_data()
    drivers_data = data.get("drivers", {})

    if drivers_data:
        # Build driver map from local data
        driver_map = {}
        for driver_num_str, driver_info in drivers_data.items():
            driver_num = int(driver_num_str)
            driver_map[driver_num] = {
                "name": driver_info.get("name", f"DRV{driver_num}"),
                "code": driver_info.get("code", "???"),
                "team": driver_info.get("team", "Unknown"),
                "color": f"#{driver_info.get('color', '000000')}",
                "number": driver_num,
            }
        return driver_map

    # Fall back to OpenF1 API for driver info
    drivers_api = api_request(
        f"{OPENF1_BASE}/drivers",
        params={"session_key": session_key},
        delay=1.0
    )

    if not drivers_api:
        return {}

    driver_map = {}
    for driver in drivers_api:
        driver_num = driver.get("driver_number")
        if driver_num:
            driver_map[driver_num] = {
                "name": driver.get("full_name", f"DRV{driver_num}"),
                "code": driver.get("name_acronym", "???"),
                "team": driver.get("team_name", "Unknown"),
                "color": "#FFFFFF",
                "number": driver_num,
            }

    return driver_map


def fetch_location_data(session_key: int, driver_number: int) -> List[Dict]:
    """Fetch location data for a driver in a session."""
    return api_request(
        f"{OPENF1_BASE}/location",
        params={"session_key": session_key, "driver_number": driver_number},
        delay=1.0  # Longer delay for individual driver requests
    ) or []


def fetch_pit_data(session_key: int) -> Dict:
    """Fetch pit stop data for session."""
    pits = api_request(
        f"{OPENF1_BASE}/pit",
        params={"session_key": session_key},
        delay=1.0
    )

    if not pits:
        return {}

    # Map pit stops by driver
    pit_map = {}
    for pit in pits:
        driver_num = pit["driver_number"]
        if driver_num not in pit_map:
            pit_map[driver_num] = []
        pit_map[driver_num].append({
            "lap": pit["lap_number"],
            "duration": pit["pit_duration"],
            "date": pit["date"],
        })

    return pit_map


def fetch_starting_grid(session_key: int) -> Dict:
    """Fetch starting grid (pole position info)."""
    grid = api_request(
        f"{OPENF1_BASE}/starting_grid",
        params={"session_key": session_key},
        delay=1.0
    )

    if not grid:
        return {}

    # Map grid positions by driver
    grid_map = {}
    for entry in grid:
        grid_map[entry["driver_number"]] = {
            "position": entry["position"],
            "is_pole": entry["position"] == 1,
        }

    return grid_map


def generate_synthetic_telemetry(driver_number: int, track_bounds: Dict, session_duration: int = 3600) -> list:
    """Generate synthetic telemetry following the track racing line."""
    import math
    import random

    telemetry = []

    # Track center for circular motion
    center_x = (track_bounds["min_x"] + track_bounds["max_x"]) / 2
    center_y = (track_bounds["min_y"] + track_bounds["max_y"]) / 2
    radius = (track_bounds["max_x"] - track_bounds["min_x"]) / 2

    # Driver-specific offset for variety
    random.seed(driver_number)
    start_angle = random.random() * 2 * math.pi

    # Generate lap data
    lap_time = 90  # seconds per lap
    num_laps = session_duration // lap_time
    points_per_lap = 300

    for lap in range(num_laps):
        for point in range(points_per_lap):
            # Progress around the track
            angle = start_angle + (lap * 2 * math.pi) + ((point / points_per_lap) * 2 * math.pi)

            # Add slight variation to radius for realistic driving
            radius_var = radius * (0.8 + 0.2 * math.sin(angle * 3))

            # Calculate position
            x = center_x + radius_var * math.cos(angle)
            y = center_y + radius_var * math.sin(angle)

            # Speed varies based on position (slow in corners, fast on straights)
            base_speed = 150 + 100 * math.sin(angle * 4)
            speed = max(50, min(350, base_speed))

            # Time for this point
            time_offset = lap * lap_time + (point / points_per_lap) * lap_time

            telemetry.append({
                "time": time_offset,
                "x": x,
                "y": y,
                "speed": speed,
                "gear": max(1, int((speed / 300) * 8)),
                "throttle": min(1.0, (speed - 50) / 250),
                "brake": max(0, min(1.0, (300 - speed) / 200)),
                "drs": speed > 280,
                "lapNumber": lap + 1,
                "in_pit": False,
            })

    return telemetry


def build_telemetry_for_session(session_key: int) -> Dict:
    """Build complete telemetry dataset for session from OpenF1 API or synthetic."""
    print(f"Building telemetry for session {session_key} (fetching official data)...")

    # Fetch drivers
    drivers = fetch_drivers_for_session(session_key)
    if not drivers:
        return {"drivers": {}, "session_key": session_key, "data_points": 0}

    # Try to fetch pit data and grid (may be empty for future sessions)
    pit_data = fetch_pit_data(session_key)
    grid_data = fetch_starting_grid(session_key)

    drivers_data = {}
    total_points = 0

    for driver_number, driver_info in drivers.items():
        print(f"  Processing driver {driver_number} ({driver_info['name']})...")

        # Try to fetch official telemetry data from OpenF1 API
        location_data = fetch_location_data(session_key, driver_number)

        if not location_data:
            # Fall back to synthetic telemetry based on track
            print(f"    → No OpenF1 data, generating synthetic telemetry...")
            telemetry = generate_synthetic_telemetry(driver_number, AUSTIN_TRACK_BOUNDS)
        else:
            # Transform location data to telemetry (use official API data)
            telemetry = []
            start_time = None
            for idx, loc in enumerate(location_data):
                x_raw = loc.get("x", 0)
                y_raw = loc.get("y", 0)

                # Skip if still at origin
                if x_raw == 0 and y_raw == 0:
                    continue

                # Parse timestamp (handle ISO format strings from OpenF1 API)
                date_val = loc.get("date")
                if isinstance(date_val, str):
                    # ISO format timestamp, convert to seconds since start
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                        timestamp = dt.timestamp()
                        if start_time is None:
                            start_time = timestamp
                        time_offset = timestamp - start_time
                    except:
                        time_offset = float(idx)
                else:
                    time_offset = float(date_val) if date_val else float(idx)

                # Check if in pit lane
                in_pit = is_in_pit_lane(x_raw, y_raw)

                # Build telemetry point with official data from API (use native OpenF1 coordinates)
                telemetry_point = {
                    "time": time_offset,
                    "x": x_raw,
                    "y": y_raw,
                    "speed": loc.get("speed", 0),  # Official speed from API
                    "gear": loc.get("gear", 0),    # Official gear from API
                    "throttle": loc.get("throttle", 0),  # Official throttle
                    "brake": loc.get("brake", 0),  # Official brake
                    "drs": loc.get("drs", False),  # Official DRS status
                    "lapNumber": loc.get("lap_number", 1),  # Official lap number
                    "in_pit": in_pit,
                }
                telemetry.append(telemetry_point)

        # Get driver's pole position status
        grid_info = grid_data.get(driver_number, {"position": 20, "is_pole": False})

        # Get driver's pit stops
        pits = pit_data.get(driver_number, [])

        drivers_data[str(driver_number)] = {
            "name": driver_info["name"],
            "code": driver_info["code"],
            "number": driver_number,
            "team": driver_info["team"],
            "color": driver_info["color"],
            "telemetry": telemetry,
            "pole_position": grid_info["is_pole"],
            "grid_position": grid_info["position"],
            "pit_stops": pits,
        }

        total_points += len(telemetry)
        print(f"    ✓ {len(telemetry)} points ({len(pits)} pit stops)")

    print(f"✓ Session {session_key} complete: {len(drivers_data)} drivers, {total_points} total points")

    return {
        "drivers": drivers_data,
        "session_key": session_key,
        "data_points": total_points,
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "source": "OpenF1 API"}


@app.get("/api/austin-sessions")
@app.get("/api/animation-sessions")
def get_austin_races():
    """Get all available Austin race sessions (2025)."""
    sessions = get_austin_sessions(year=2025)
    return {
        "sessions": [
            {
                "session_key": s["session_key"],
                "session_name": s.get("name", "Session"),
                "session_type": s.get("session_type", "Unknown"),
                "date": s.get("date", ""),
                "country": s.get("country_name", "United States"),
            }
            for s in sessions
        ]
    }


@app.get("/api/animation-telemetry/{session_key}")
def get_animation_telemetry(session_key: int):
    """Get telemetry data for animation."""
    # Check cache
    if session_key in _telemetry_cache:
        print(f"Cache hit for session {session_key}")
        return _telemetry_cache[session_key]

    # Build telemetry from OpenF1
    telemetry_data = build_telemetry_for_session(session_key)

    # Cache it
    _telemetry_cache[session_key] = telemetry_data

    return telemetry_data


@app.get("/api/race-results/{session_key}")
def get_race_results(session_key: int):
    """Get final race results from official OpenF1 API results endpoint."""
    try:
        # Fetch official race results from OpenF1 API
        results_data = api_request(
            f"{OPENF1_BASE}/results",
            params={"session_key": session_key},
            delay=1.0
        )

        if not results_data:
            # Fallback to telemetry-based calculation if no official results
            print(f"Warning: No official results found for session {session_key}, using telemetry fallback")
            return get_race_results_from_telemetry(session_key)

        # Transform OpenF1 results to our format
        results = []
        for result in results_data:
            # Skip drivers who DNF or didn't participate
            if result.get("position") is None or result.get("status") == "Retired":
                continue

            results.append({
                "driver_number": result.get("driver_number"),
                "name": result.get("driver_name", "Unknown"),
                "code": result.get("name_acronym", "???"),
                "team": result.get("team_name", "Unknown"),
                "color": result.get("team_color", "#FFFFFF"),
                "position": result.get("position"),
                "points": result.get("points", 0),
                "status": result.get("status", "Finished"),
                "laps_completed": result.get("laps_completed", 0)
            })

        # Ensure sorted by position
        results.sort(key=lambda x: x.get("position", 999))

        return {"session_key": session_key, "results": results}

    except Exception as e:
        print(f"Error fetching official results: {e}")
        # Fallback to telemetry-based results
        return get_race_results_from_telemetry(session_key)


def get_race_results_from_telemetry(session_key: int):
    """Fallback: Calculate race results from telemetry data."""
    telemetry = get_animation_telemetry(session_key)

    results = []
    for driver_id, driver_data in telemetry.get("drivers", {}).items():
        if not driver_data.get("telemetry"):
            continue

        # Get last telemetry point to determine final position
        last_point = driver_data["telemetry"][-1]
        final_lap = last_point.get("lapNumber", 0)
        final_position = last_point.get("x", 0)  # x coordinate on track
        total_points = len(driver_data.get("telemetry", []))

        results.append({
            "driver_number": driver_data.get("number"),
            "name": driver_data.get("name"),
            "code": driver_data.get("code"),
            "team": driver_data.get("team"),
            "color": driver_data.get("color"),
            "final_lap": final_lap,
            "final_position": final_position,
            "total_telemetry_points": total_points,
            "pit_stops": len(driver_data.get("pit_stops", []))
        })

    # Sort by laps (descending), then by position within final lap (descending x = further along)
    results.sort(key=lambda x: (-x["final_lap"], -x["final_position"]))

    # Add finishing position
    for position, result in enumerate(results, 1):
        result["position"] = position

    return {"session_key": session_key, "results": results}


@app.get("/api/track/{session_key}")
def get_track(session_key: int):
    """Get track geometry from OpenF1 API."""
    try:
        session = requests.get(
            f"{OPENF1_BASE}/sessions",
            params={"session_key": session_key},
            timeout=10
        ).json()

        if not session:
            return {"error": "Session not found", "track": []}

        circuit_key = session[0].get("circuit_key")
        if not circuit_key:
            return {"error": "Circuit data not found", "track": []}

        # Fetch circuit data
        circuit = requests.get(
            f"{OPENF1_BASE}/circuits",
            params={"circuit_key": circuit_key},
            timeout=10
        ).json()

        if not circuit:
            return {"error": "Circuit geometry not found", "track": []}

        circuit_data = circuit[0]
        track_geometry = circuit_data.get("track_geometry", [])

        return {
            "session_key": session_key,
            "circuit_name": circuit_data.get("circuit_name"),
            "circuit_short_name": circuit_data.get("circuit_short_name"),
            "country_name": circuit_data.get("country_name"),
            "track": track_geometry  # Array of {x, y, z} coordinates
        }
    except Exception as e:
        return {"error": str(e), "track": []}


@app.on_event("startup")
async def startup_event():
    """Warm cache with Austin sessions on startup."""
    def warm_cache():
        print("🔥 Preloading telemetry data for all sessions...")
        # Directly preload known session keys
        session_keys = [9608, 9617]  # Qualifying and Race

        for session_key in session_keys:
            try:
                print(f"  Loading session {session_key}...")
                get_animation_telemetry(session_key)
                print(f"  ✓ Session {session_key} cached")
            except Exception as e:
                print(f"  ✗ Error loading session {session_key}: {e}")

        print("✓ Data preload complete")

    # Run in background thread
    cache_thread = threading.Thread(target=warm_cache, daemon=True)
    cache_thread.start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
