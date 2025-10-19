"""
Comprehensive F1 Lap Analysis Report Generator
Creates timestamped, detailed reports for each driver and session
"""

import json
import os
from datetime import datetime
from fastf1_fetcher import F1DataFetcher
from gemini_analyzer import GeminiF1Analyzer


class ReportGenerator:
    def __init__(self, output_dir='./reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_lap_by_lap_report(self, session_data, driver_id):
        """Generate detailed lap-by-lap report for a driver"""

        driver_laps = session_data['drivers'][driver_id]

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'driver': driver_id,
                'session': session_data['session'],
                'circuit': session_data['circuit'],
                'year': session_data['year'],
            },
            'summary': driver_laps['summary'],
            'lap_analysis': []
        }

        best_lap_time = driver_laps['summary']['best_lap_time']

        for idx, lap in enumerate(driver_laps['laps']):
            previous_lap = driver_laps['laps'][idx - 1] if idx > 0 else None

            lap_entry = {
                'lap_number': lap['lap_number'],
                'timestamp': f"Lap {lap['lap_number']} - {lap['lap_time_formatted']}",
                'lap_time_seconds': lap['lap_time_seconds'],
                'sectors': {
                    'S1': round(lap['sector_1_seconds'], 3),
                    'S2': round(lap['sector_2_seconds'], 3),
                    'S3': round(lap['sector_3_seconds'], 3),
                },
                'tire': {
                    'compound': lap['compound'],
                    'age': lap['tire_life'],
                },
                'telemetry': {
                    'max_speed': round(lap['telemetry'].get('max_speed', 0), 1),
                    'avg_speed': round(lap['telemetry'].get('avg_speed', 0), 1),
                    'max_rpm': round(lap['telemetry'].get('max_rpm', 0), 0),
                    'drs_activations': lap['telemetry'].get('drs_activations', 0),
                    'brake_events': lap['telemetry'].get('brake_events', 0),
                },
                'analysis': self._generate_lap_analysis(
                    lap, previous_lap, best_lap_time
                )
            }

            report['lap_analysis'].append(lap_entry)

        return report

    def _generate_lap_analysis(self, lap, previous_lap, best_lap_time):
        """Generate analysis for individual lap"""

        time_delta = lap['lap_time_seconds'] - best_lap_time

        analysis = {
            'is_best_lap': lap['lap_time_seconds'] == best_lap_time,
            'time_delta_from_best': f"+{time_delta:.3f}s" if time_delta > 0 else "Best",
            'comparison_to_previous': None,
            'performance_assessment': self._assess_performance(lap, best_lap_time),
            'key_metrics': {
                'speed_trap': f"{lap['speed_trap']:.1f} km/h",
                'peak_speed': f"{lap['telemetry'].get('max_speed', 0):.1f} km/h",
                'tire_age': f"{lap['tire_life']} laps",
            },
            'issues': self._identify_issues(lap, previous_lap, best_lap_time),
            'highlights': self._identify_highlights(lap),
        }

        if previous_lap:
            prev_time_diff = lap['lap_time_seconds'] - previous_lap['lap_time_seconds']
            analysis['comparison_to_previous'] = {
                'previous_lap_time': f"{previous_lap['lap_time_seconds']:.3f}s",
                'time_difference': f"{prev_time_diff:+.3f}s",
                'trend': "Improved 📈" if prev_time_diff < 0 else "Slower 📉",
                'tire_strategy': f"{lap['compound']} vs {previous_lap['compound']}",
            }

        return analysis

    def _assess_performance(self, lap, best_lap_time):
        """Assess lap performance quality"""

        delta = lap['lap_time_seconds'] - best_lap_time

        if delta == 0:
            return "🟢 Best lap - Excellent performance"
        elif delta < 0.1:
            return "🟢 Exceptional - Very close to best"
        elif delta < 0.5:
            return "🟡 Good - Strong lap"
        elif delta < 1.0:
            return "🟡 Decent - Acceptable performance"
        else:
            return "🔴 Poor - Significant time gap"

    def _identify_issues(self, lap, previous_lap, best_lap_time):
        """Identify potential issues with the lap"""

        issues = []
        delta = lap['lap_time_seconds'] - best_lap_time

        # Tire degradation
        if lap['tire_life'] > 5:
            issues.append({
                'category': 'Tire Degradation',
                'description': f"Tire age: {lap['tire_life']} laps - significant wear",
                'severity': 'Medium' if lap['tire_life'] < 10 else 'High',
                'estimated_time_loss': '0.2-0.5s'
            })

        # Speed consistency
        if lap['telemetry'].get('avg_speed', 0) < 180:
            issues.append({
                'category': 'Low Average Speed',
                'description': f"Average speed only {lap['telemetry'].get('avg_speed', 0):.1f} km/h",
                'severity': 'Medium',
                'estimated_time_loss': '0.1-0.3s'
            })

        # DRS issues
        if lap['telemetry'].get('drs_activations', 0) == 0:
            issues.append({
                'category': 'No DRS Activations',
                'description': "Failed to deploy DRS effectively",
                'severity': 'High',
                'estimated_time_loss': '0.3-0.7s'
            })

        # Brake efficiency
        if lap['telemetry'].get('brake_events', 0) > 10:
            issues.append({
                'category': 'Excessive Braking',
                'description': f"{lap['telemetry'].get('brake_events', 0)} brake events - possible overbraking",
                'severity': 'Medium',
                'estimated_time_loss': '0.1-0.2s'
            })

        # High RPM inefficiency
        if lap['telemetry'].get('max_rpm', 0) > 15000:
            issues.append({
                'category': 'RPM Spike',
                'description': f"Peak RPM {lap['telemetry'].get('max_rpm', 0):.0f} - possible throttle mismanagement",
                'severity': 'Low',
                'estimated_time_loss': '0.05-0.1s'
            })

        return issues

    def _identify_highlights(self, lap):
        """Identify positive aspects of the lap"""

        highlights = []

        if lap['telemetry'].get('max_speed', 0) > 210:
            highlights.append({
                'category': 'High Top Speed',
                'description': f"Reached {lap['telemetry'].get('max_speed', 0):.1f} km/h",
                'impact': 'Strong acceleration and DRS execution'
            })

        if lap['telemetry'].get('drs_activations', 0) > 1:
            highlights.append({
                'category': 'Effective DRS Deployment',
                'description': f"{lap['telemetry'].get('drs_activations', 0)} DRS activations",
                'impact': 'Good race craft and positioning'
            })

        if lap['sector_1_seconds'] < 31:
            highlights.append({
                'category': 'Strong Sector 1',
                'description': f"S1: {lap['sector_1_seconds']:.3f}s",
                'impact': 'Excellent corner entry and mid-corner speed'
            })

        if lap['sector_3_seconds'] < 35:
            highlights.append({
                'category': 'Strong Sector 3',
                'description': f"S3: {lap['sector_3_seconds']:.3f}s",
                'impact': 'Good exit speed and acceleration'
            })

        return highlights

    def generate_session_comparison(self, session_data):
        """Generate comparison report across all drivers in session"""

        drivers_summary = []

        for driver_id, driver_data in session_data['drivers'].items():
            drivers_summary.append({
                'driver': driver_id,
                'best_lap': driver_data['summary']['best_lap_time'],
                'avg_lap': driver_data['summary']['average_lap_time'],
                'personal_bests': driver_data['summary']['total_pbs'],
                'total_laps': driver_data['summary']['total_laps'],
                'avg_max_speed': driver_data['summary']['avg_max_speed'],
            })

        drivers_summary.sort(key=lambda x: x['best_lap'])

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'session': session_data['session'],
                'circuit': session_data['circuit'],
                'year': session_data['year'],
            },
            'rankings': drivers_summary,
            'statistics': self._calculate_session_stats(drivers_summary),
            'analysis': self._generate_session_insights(drivers_summary)
        }

        return report

    def _calculate_session_stats(self, drivers_summary):
        """Calculate session-wide statistics"""

        best_laps = [d['best_lap'] for d in drivers_summary]
        avg_laps = [d['avg_lap'] for d in drivers_summary]

        return {
            'total_drivers': len(drivers_summary),
            'fastest_lap': min(best_laps),
            'slowest_lap': max(best_laps),
            'lap_time_range': f"{max(best_laps) - min(best_laps):.3f}s",
            'average_best_lap': sum(best_laps) / len(best_laps),
            'average_of_averages': sum(avg_laps) / len(avg_laps),
        }

    def _generate_session_insights(self, drivers_summary):
        """Generate insights about the session"""

        insights = []

        # Find best performer
        best = drivers_summary[0]
        insights.append({
            'title': 'Session Leader',
            'driver': best['driver'],
            'metric': f"Best Lap: {best['best_lap']}s",
            'description': f"{best['driver']} set the pace with a {best['best_lap']}s lap"
        })

        # Find consistency leader
        consistency_scores = [
            (d['driver'], abs(d['best_lap'] - d['avg_lap']))
            for d in drivers_summary
        ]
        consistency_scores.sort(key=lambda x: x[1])
        consistent = consistency_scores[0]

        insights.append({
            'title': 'Most Consistent',
            'driver': consistent[0],
            'metric': f"Gap: {consistent[1]:.3f}s",
            'description': f"{consistent[0]} showed excellent consistency"
        })

        # Find best improvement trend (most PBs)
        pb_scores = sorted(drivers_summary, key=lambda x: -x['personal_bests'])
        if pb_scores and pb_scores[0]['personal_bests'] > 0:
            pb_leader = pb_scores[0]
            insights.append({
                'title': 'Most Personal Bests',
                'driver': pb_leader['driver'],
                'metric': f"{pb_leader['personal_bests']} PBs",
                'description': f"{pb_leader['driver']} achieved the most personal bests"
            })

        # Competitive gap analysis
        if len(drivers_summary) > 1:
            gap_to_leader = drivers_summary[1]['best_lap'] - drivers_summary[0]['best_lap']
            insights.append({
                'title': 'Top 2 Competitiveness',
                'driver': f"{drivers_summary[0]['driver']} vs {drivers_summary[1]['driver']}",
                'metric': f"Gap: {gap_to_leader:.3f}s",
                'description': f"Close gap of {gap_to_leader:.3f}s shows competitive field"
            })

        return insights

    def save_report(self, report, filename):
        """Save report to JSON file"""

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        return filepath

    def save_markdown_report(self, report, driver_id, session_name):
        """Save report as formatted markdown"""

        md = f"""# F1 Lap Analysis Report

## {driver_id} - {session_name}

**Generated:** {report['metadata']['generated_at']}
**Circuit:** {report['metadata']['circuit']}
**Year:** {report['metadata']['year']}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Laps | {report['summary']['total_laps']} |
| Best Lap | {report['summary']['best_lap_time']}s |
| Average Lap | {report['summary']['average_lap_time']}s |
| Personal Bests | {report['summary']['total_pbs']} |

---

## Lap-by-Lap Analysis

"""

        for lap in report['lap_analysis']:
            md += f"""
### {lap['timestamp']}

**Time:** {lap['lap_time_seconds']:.3f}s {lap['analysis']['time_delta_from_best']}

**Sectors:**
- S1: {lap['sectors']['S1']:.3f}s
- S2: {lap['sectors']['S2']:.3f}s
- S3: {lap['sectors']['S3']:.3f}s

**Telemetry:**
- Max Speed: {lap['telemetry']['max_speed']} km/h
- Avg Speed: {lap['telemetry']['avg_speed']} km/h
- DRS Activations: {lap['telemetry']['drs_activations']}
- Brake Events: {lap['telemetry']['brake_events']}

**Tire:** {lap['tire']['compound']} (Age: {lap['tire']['age']} laps)

**Performance:** {lap['analysis']['performance_assessment']}

"""

            if lap['analysis']['issues']:
                md += "**Issues:**\n"
                for issue in lap['analysis']['issues']:
                    md += f"- **{issue['category']}** [{issue['severity']}]: {issue['description']} (~{issue['estimated_time_loss']} lost)\n"
                md += "\n"

            if lap['analysis']['highlights']:
                md += "**Highlights:**\n"
                for highlight in lap['analysis']['highlights']:
                    md += f"- **{highlight['category']}**: {highlight['description']}\n"
                md += "\n"

        filepath = os.path.join(self.output_dir, f"{driver_id}_{session_name}.md")
        with open(filepath, 'w') as f:
            f.write(md)

        return filepath


def generate_all_reports(f1_data_path, output_dir='./reports'):
    """Generate all reports"""

    print("📄 Generating comprehensive reports...")

    with open(f1_data_path) as f:
        f1_data = json.load(f)

    generator = ReportGenerator(output_dir)

    for session_name, session_data in f1_data.items():
        print(f"\n📊 Generating reports for {session_name}...")

        # Generate session comparison
        comparison = generator.generate_session_comparison(session_data)
        comp_file = generator.save_report(
            comparison,
            f"{session_name.replace(' ', '_')}_comparison.json"
        )
        print(f"  ✅ Session comparison: {comp_file}")

        # Generate per-driver reports
        for driver_id in session_data['drivers'].keys():
            lap_report = generator.generate_lap_by_lap_report(session_data, driver_id)
            json_file = generator.save_report(
                lap_report,
                f"{driver_id}_{session_name.replace(' ', '_')}_laps.json"
            )
            md_file = generator.save_markdown_report(lap_report, driver_id, session_name)

            print(f"  ✅ {driver_id}: {json_file} + {md_file}")

    print(f"\n✅ All reports saved to {output_dir}")


if __name__ == '__main__':
    generate_all_reports('./f1_cache/austin_2024_complete.json')
