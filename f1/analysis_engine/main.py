#!/usr/bin/env python3
"""
F1 Comprehensive Analysis Engine
Fetches real F1 data, analyzes with Gemini AI, generates detailed reports
"""

import argparse
import sys
import os
from pathlib import Path

from fastf1_fetcher import F1DataFetcher
from report_generator import generate_all_reports


def setup_environment():
    """Check and setup environment"""
    print("🏁 F1 Analysis Engine - Setup Check")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False

    # Check for API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set")
        print("   Run: export GEMINI_API_KEY='your-api-key'")
        print("   Get key from: https://makersuite.google.com/app/apikey")

    print("✅ Environment check complete\n")
    return True


def fetch_data(year=2024, circuit='Austin', output_dir='./f1_cache'):
    """Fetch F1 data from FastF1"""

    print("🚀 Fetching F1 Data")
    print("=" * 60)

    fetcher = F1DataFetcher(cache_dir=output_dir)

    # Fetch all sessions
    all_data = fetcher.fetch_all_sessions(year=year, gp=circuit)

    if not all_data:
        print("❌ Failed to fetch data")
        return None

    # Save to JSON
    output_file = fetcher.save_to_json(all_data, f'{circuit.lower()}_{year}_complete.json')

    print(f"\n✅ Data fetched and saved to {output_file}\n")
    return output_file


def analyze_data(f1_data_path):
    """Generate analysis reports"""

    print("📄 Generating Analysis Reports")
    print("=" * 60)

    output_dir = './reports'

    generate_all_reports(f1_data_path, output_dir)

    print(f"\n✅ Reports generated in {output_dir}\n")
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description='F1 Comprehensive Analysis Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --fetch                    # Fetch Austin 2024 data
  python main.py --analyze data.json        # Generate reports from data
  python main.py --all                      # Fetch and analyze
  python main.py --year 2025 --circuit "Mexico City"  # Different event
        """
    )

    parser.add_argument('--fetch', action='store_true', help='Fetch F1 data')
    parser.add_argument('--analyze', type=str, help='Generate reports from JSON file')
    parser.add_argument('--all', action='store_true', help='Fetch and analyze')
    parser.add_argument('--year', type=int, default=2024, help='F1 season year')
    parser.add_argument('--circuit', type=str, default='Austin', help='Circuit name')
    parser.add_argument('--cache-dir', type=str, default='./f1_cache', help='Cache directory')
    parser.add_argument('--setup-check', action='store_true', help='Check environment setup')

    args = parser.parse_args()

    # Setup check
    if args.setup_check or not any([args.fetch, args.analyze, args.all]):
        setup_environment()

        if not any([args.fetch, args.analyze, args.all]):
            parser.print_help()
            return

    print()

    data_file = None

    # Fetch data
    if args.fetch or args.all:
        data_file = fetch_data(
            year=args.year,
            circuit=args.circuit,
            output_dir=args.cache_dir
        )

    # Analyze data
    if args.analyze:
        data_file = args.analyze
        if not Path(data_file).exists():
            print(f"❌ File not found: {data_file}")
            return

    if args.all or (args.fetch and not args.analyze):
        if data_file:
            analyze_data(data_file)
    elif args.analyze and data_file:
        analyze_data(data_file)

    print("\n" + "=" * 60)
    print("🎉 Analysis Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Check ./reports/ for generated reports")
    print("2. View JSON reports in your favorite editor")
    print("3. View Markdown reports (.md files) for readable format")
    print("4. Integrate reports into React dashboard")


if __name__ == '__main__':
    main()
