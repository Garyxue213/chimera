"""
FastF1 Data Fetcher for Austin US Grand Prix 3
Fetches comprehensive telemetry and lap data for all drivers
"""

import fastf1
import json
import os
from datetime import datetime
import pandas as pd

class F1DataFetcher:
    def __init__(self, cache_dir='./cache'):
        """Initialize FastF1 with caching"""
        self.cache_dir = cache_dir
        fastf1.Cache.enable_cache(cache_dir)

    def fetch_session(self, year=2024, gp='Austin', session_type='Q'):
        """
        Fetch session data
        session_type: 'Q' = Qualifying, 'SQ' = Sprint Qualifying, 'S' = Sprint/Race
        """
        print(f"Fetching {session_type} for {gp} {year}...")

        # Map session names
        session_map = {
            'Q': 'Qualifying',
            'SQ': 'Sprint Qualifying',
            'S': 'Sprint'
        }

        try:
            session = fastf1.get_session(year, gp, session_type)
            session.load()
            print(f"✅ Loaded {session_map.get(session_type, session_type)} session")
            return session
        except Exception as e:
            print(f"❌ Error fetching session: {e}")
            return None

    def process_lap_telemetry(self, lap):
        """Extract detailed telemetry for a single lap"""
        try:
            telemetry = lap.get_car_data().add_distance()

            return {
                'max_speed': float(telemetry['Speed'].max()),
                'avg_speed': float(telemetry['Speed'].mean()),
                'max_rpm': float(telemetry['RPM'].max()),
                'avg_rpm': float(telemetry['RPM'].mean()),
                'drs_activations': int((telemetry['DRS'] > 0).sum()) if 'DRS' in telemetry else 0,
                'max_throttle': float(telemetry['Throttle'].max()) if 'Throttle' in telemetry else 0,
                'brake_events': int((telemetry['Brake'] > 0).sum()) if 'Brake' in telemetry else 0,
                'speed_trace': telemetry['Speed'].tolist() if len(telemetry) > 0 else [],
            }
        except Exception as e:
            print(f"Error processing telemetry: {e}")
            return {}

    def extract_driver_laps(self, session, driver_id):
        """Extract all laps for a specific driver with detailed analysis"""
        try:
            laps = session.laps.pick_driver(driver_id)

            driver_data = {
                'driver_id': driver_id,
                'session': session.name,
                'date': str(session.date),
                'laps': [],
                'summary': {
                    'total_laps': len(laps),
                    'best_lap_time': None,
                    'average_lap_time': None,
                    'total_pbs': 0,
                    'avg_max_speed': 0,
                    'avg_avg_speed': 0
                }
            }

            lap_times = []
            speeds = []

            for idx, lap in laps.iterlaps():
                # Skip invalid laps
                if pd.isna(lap['LapTime']):
                    continue

                lap_time_seconds = lap['LapTime'].total_seconds()
                lap_times.append(lap_time_seconds)

                telemetry = self.process_lap_telemetry(lap)

                if 'max_speed' in telemetry:
                    speeds.append(telemetry['max_speed'])

                lap_entry = {
                    'lap_number': int(lap['LapNumber']),
                    'lap_time_seconds': round(lap_time_seconds, 3),
                    'lap_time_formatted': str(lap['LapTime']),
                    'sector_1_seconds': lap['Sector1Time'].total_seconds() if pd.notna(lap['Sector1Time']) else 0,
                    'sector_2_seconds': lap['Sector2Time'].total_seconds() if pd.notna(lap['Sector2Time']) else 0,
                    'sector_3_seconds': lap['Sector3Time'].total_seconds() if pd.notna(lap['Sector3Time']) else 0,
                    'compound': lap['Compound'],
                    'tire_life': int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else 0,
                    'is_pit_lap': True if lap['PitOutTime'] is not pd.NaT else False,
                    'speed_trap': float(lap['SpeedST']) if pd.notna(lap['SpeedST']) else 0,
                    'telemetry': telemetry,
                    'is_pb': lap['IsPersonalBest'] if 'IsPersonalBest' in lap else False,
                }

                driver_data['laps'].append(lap_entry)

            # Calculate summary
            if lap_times:
                driver_data['summary']['best_lap_time'] = round(min(lap_times), 3)
                driver_data['summary']['average_lap_time'] = round(sum(lap_times) / len(lap_times), 3)

            if speeds:
                driver_data['summary']['avg_max_speed'] = round(sum(speeds) / len(speeds), 1)

            driver_data['summary']['total_pbs'] = sum(1 for lap in driver_data['laps'] if lap.get('is_pb', False))

            return driver_data

        except Exception as e:
            print(f"Error extracting laps for {driver_id}: {e}")
            return None

    def fetch_all_drivers_session(self, year=2024, gp='Austin', session_type='Q'):
        """Fetch data for all drivers in a session"""
        session = self.fetch_session(year, gp, session_type)
        if not session:
            return None

        all_drivers = {}

        # Get all drivers in the session
        drivers = session.results['Abbreviation'].tolist()

        print(f"\nProcessing {len(drivers)} drivers...")
        for idx, driver in enumerate(drivers, 1):
            print(f"  [{idx}/{len(drivers)}] Processing {driver}...", end=' ')
            driver_data = self.extract_driver_laps(session, driver)
            if driver_data:
                all_drivers[driver] = driver_data
                print(f"✅ ({len(driver_data['laps'])} laps)")
            else:
                print("❌")

        return {
            'session': session.name,
            'date': str(session.date),
            'circuit': gp,
            'year': year,
            'drivers': all_drivers
        }

    def fetch_all_sessions(self, year=2024, gp='Austin'):
        """Fetch all available sessions (Q, SQ, S)"""
        all_data = {}

        sessions = {
            'Q': 'Qualifying',
            'SQ': 'Sprint Qualifying',
            'S': 'Sprint'
        }

        for session_code, session_name in sessions.items():
            print(f"\n{'='*60}")
            print(f"Fetching {session_name}")
            print('='*60)

            session_data = self.fetch_all_drivers_session(year, gp, session_code)
            if session_data:
                all_data[session_name] = session_data

        return all_data

    def save_to_json(self, data, filename='f1_data.json'):
        """Save data to JSON file"""
        output_path = os.path.join(self.cache_dir, filename)
        os.makedirs(self.cache_dir, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Data saved to {output_path}")
        return output_path


def main():
    """Main execution"""
    print("🏁 F1 Data Fetcher - Austin US Grand Prix")
    print("=" * 60)

    fetcher = F1DataFetcher(cache_dir='./f1_cache')

    # Fetch all sessions
    all_data = fetcher.fetch_all_sessions(year=2024, gp='Austin')

    # Save to JSON
    if all_data:
        output_file = fetcher.save_to_json(all_data, 'austin_2024_complete.json')
        print(f"\n✅ Complete! Data available at: {output_file}")

    return all_data


if __name__ == '__main__':
    main()
