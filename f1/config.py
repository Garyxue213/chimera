"""Configuration and constants for F1 Austin GP Simulation"""

# Austin Circuit of the Americas
CIRCUIT = {
    'name': 'Circuit of the Americas',
    'location': 'Austin, Texas, USA',
    'lap_length_km': 5.513,
    'total_laps': 56,
    'race_distance_km': 308.405,
    'drs_zones': 2,
    'lap_record_seconds': 5400  # Approximate
}

# 2025 F1 Season - Austin GP (Oct 18-19)
SESSION_DATES = {
    'saturday_date': '2025-10-18',
    'sunday_date': '2025-10-19',
    'saturday_session': 'FP3-Q',  # Practice & Qualifying
    'sunday_session': 'Race'
}

# Expected drivers (top teams 2025)
TOP_TEAMS = {
    'Red Bull': ['Max Verstappen', 'Sergio Pérez'],
    'Mercedes': ['Lewis Hamilton', 'George Russell'],
    'Ferrari': ['Charles Leclerc', 'Carlos Sainz'],
    'McLaren': ['Lando Norris', 'Oscar Piastri'],
    'Aston Martin': ['Fernando Alonso', 'Lance Stroll']
}

# Tire compounds
TIRE_COMPOUNDS = {
    'soft': {'degradation_rate': 0.15, 'max_laps': 25},
    'medium': {'degradation_rate': 0.10, 'max_laps': 35},
    'hard': {'degradation_rate': 0.07, 'max_laps': 50}
}

# Weather conditions
WEATHER = {
    'clear': {'grip_factor': 1.0, 'rain_probability': 0.0},
    'cloudy': {'grip_factor': 0.98, 'rain_probability': 0.1},
    'light_rain': {'grip_factor': 0.85, 'rain_probability': 0.5},
    'rain': {'grip_factor': 0.70, 'rain_probability': 0.9}
}

# Simulation parameters
SIMULATION = {
    'random_seed': 42,
    'pit_stop_time_seconds': 23,
    'drs_advantage_percent': 0.02,
    'overtake_threshold': 0.15,  # Time delta threshold for overtake attempt
    'safety_car_probability': 0.05
}
