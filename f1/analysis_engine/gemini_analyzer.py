"""
Gemini AI Lap-by-Lap Analysis Engine
Analyzes F1 telemetry data and generates detailed performance reports
"""

import google.generativeai as genai
import json
import os
from datetime import datetime

class GeminiF1Analyzer:
    def __init__(self, api_key=None):
        """Initialize Gemini API"""
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_lap(self, driver_id, lap_data, previous_lap=None, session_context=None):
        """
        Analyze a single lap using Gemini
        Returns detailed breakdown of performance issues and highlights
        """

        prompt = self._build_lap_analysis_prompt(driver_id, lap_data, previous_lap, session_context)

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error analyzing lap: {e}")
            return None

    def _build_lap_analysis_prompt(self, driver_id, lap_data, previous_lap=None, session_context=None):
        """Build detailed prompt for lap analysis"""

        prompt = f"""
Analyze this F1 lap data for driver {driver_id} with expertise in performance telemetry analysis.

LAP DATA:
- Lap Number: {lap_data['lap_number']}
- Lap Time: {lap_data['lap_time_seconds']:.3f}s
- Sector 1: {lap_data['sector_1_seconds']:.3f}s
- Sector 2: {lap_data['sector_2_seconds']:.3f}s
- Sector 3: {lap_data['sector_3_seconds']:.3f}s
- Tire Compound: {lap_data['compound']}
- Tire Age: {lap_data['tire_life']} laps old
- Speed Trap: {lap_data['speed_trap']:.1f} km/h
- DRS Activations: {lap_data['telemetry'].get('drs_activations', 0)}
- Max Speed: {lap_data['telemetry'].get('max_speed', 0):.1f} km/h
- Average Speed: {lap_data['telemetry'].get('avg_speed', 0):.1f} km/h
- Max RPM: {lap_data['telemetry'].get('max_rpm', 0):.0f}
- Throttle Events: {lap_data['telemetry'].get('max_throttle', 0):.1f}%
- Brake Events: {lap_data['telemetry'].get('brake_events', 0)}
"""

        if previous_lap:
            time_diff = lap_data['lap_time_seconds'] - previous_lap['lap_time_seconds']
            prompt += f"""
PREVIOUS LAP COMPARISON:
- Previous Lap Time: {previous_lap['lap_time_seconds']:.3f}s
- Time Difference: {time_diff:+.3f}s ({'Faster' if time_diff < 0 else 'Slower'})
- Previous Tire Age: {previous_lap['tire_life']} laps
- Tire Strategy Change: {lap_data['compound']} vs {previous_lap['compound']}
"""

        prompt += """

PROVIDE ANALYSIS IN THIS FORMAT:

⏱️ LAP TIME ANALYSIS:
- Overall Performance: [Assessment of lap time quality]
- Comparison to Session Pace: [How does this compare to driver's other laps]

🔴 PERFORMANCE ISSUES (if any):
For each issue found, provide:
- Issue: [What went wrong]
- Sector: [Which sector - S1/S2/S3]
- Time Lost: [Estimate of how many tenths/hundredths were lost]
- Root Cause: [Technical reason - oversteering, understeer, lock-up, cold tires, tire degradation, DRS timing, fuel load, etc.]

🟢 HIGHLIGHTS (what went well):
- Best Sector: [S1/S2/S3 with time]
- Key Strength: [What the driver did well]
- Notable Achievement: [Any specific achievement this lap]

⚙️ TELEMETRY INSIGHTS:
- Speed Management: [How well speed was managed]
- Throttle Control: [Smoothness and application]
- Braking Performance: [Braking efficiency]
- DRS Strategy: [How DRS was deployed]

📊 STRATEGIC NOTES:
- Tire Impact: [How tire age/compound affected performance]
- Comparison to Best: [How this lap compares to driver's best lap]
- Session Trend: [Is the driver improving/degrading?]

🎯 NEXT LAP RECOMMENDATION:
- What to focus on: [Specific areas to improve for next lap]
"""

        return prompt

    def analyze_session(self, session_data, driver_id):
        """Analyze complete session for a driver"""

        driver_laps = session_data['drivers'][driver_id]

        prompt = f"""
Provide a comprehensive session analysis for F1 driver {driver_id}.

SESSION SUMMARY:
- Session: {session_data['session']}
- Circuit: {session_data['circuit']}
- Year: {session_data['year']}
- Total Laps: {driver_laps['summary']['total_laps']}
- Best Lap: {driver_laps['summary']['best_lap_time']}s
- Average Lap: {driver_laps['summary']['average_lap_time']}s
- Personal Bests: {driver_laps['summary']['total_pbs']}
- Average Max Speed: {driver_laps['summary']['avg_max_speed']} km/h

LAP DETAILS:
"""

        for lap in driver_laps['laps']:
            prompt += f"\nLap {lap['lap_number']}: {lap['lap_time_formatted']} (S1:{lap['sector_1_seconds']:.2f} S2:{lap['sector_2_seconds']:.2f} S3:{lap['sector_3_seconds']:.2f}) - {lap['compound']} Tire Age:{lap['tire_life']}"

        prompt += """

PROVIDE COMPREHENSIVE SESSION REPORT:

📋 SESSION PERFORMANCE OVERVIEW:
- Overall Assessment: [Overall performance in this session]
- Key Metrics: [Notable numbers]
- Comparison to Teammates/Competition: [General assessment]

🏆 BEST LAP ANALYSIS:
- Lap Number: [Which lap was best]
- What Made It Special: [Why this lap was fastest]
- Key Techniques: [Techniques used]

⚠️ CONSISTENCY ANALYSIS:
- Lap-to-Lap Variation: [How consistent were the laps]
- Improvement Trend: [Did driver get better/worse through session]
- Issue Areas: [Consistent problems across laps]

🔧 STRATEGIC OBSERVATIONS:
- Tire Strategy Effectiveness: [How well tire management was done]
- Setup Evolution: [Any observable setup changes]
- Adaptation: [How driver adapted through session]

📈 SESSION TREND:
[Timeline showing performance evolution through session with key moments]

🎯 FINAL ASSESSMENT:
- Strengths Demonstrated: [What the driver did well]
- Areas for Improvement: [What needs work]
- Qualifying/Race Readiness: [Assessment for next phase]

💡 RECOMMENDATIONS:
- For Next Session: [Specific recommendations]
- Technical Focus: [Technical areas to work on]
"""

        return self.model.generate_content(prompt).text

    def generate_comparison_report(self, session_data, driver_ids):
        """Generate head-to-head comparison between drivers"""

        drivers_summary = []
        for driver_id in driver_ids:
            if driver_id in session_data['drivers']:
                driver = session_data['drivers'][driver_id]
                drivers_summary.append({
                    'driver': driver_id,
                    'best_lap': driver['summary']['best_lap_time'],
                    'avg_lap': driver['summary']['average_lap_time'],
                    'pbs': driver['summary']['total_pbs'],
                    'total_laps': driver['summary']['total_laps'],
                })

        drivers_summary.sort(key=lambda x: x['best_lap'])

        comparison_data = "\n".join([
            f"{d['driver']}: Best={d['best_lap']}s Avg={d['avg_lap']}s PBs={d['pbs']} Laps={d['total_laps']}"
            for d in drivers_summary
        ])

        prompt = f"""
Analyze this competitive comparison for {session_data['session']} at {session_data['circuit']}:

{comparison_data}

Provide:
1. Ranking and gaps between drivers
2. Who is strongest and why
3. Strategic implications
4. Standout performances
5. Surprising results or patterns
"""

        return self.model.generate_content(prompt).text


def analyze_austin_data(f1_data_path):
    """Complete Austin GP analysis"""

    print("🤖 Initializing Gemini AI Analyzer...")
    analyzer = GeminiF1Analyzer()

    with open(f1_data_path) as f:
        session_data = json.load(f)

    print("📊 Starting comprehensive analysis...")

    all_reports = {}

    for session_name, session in session_data.items():
        print(f"\n{'='*60}")
        print(f"Analyzing {session_name}")
        print('='*60)

        all_reports[session_name] = {}

        for driver_id in list(session['drivers'].keys())[:5]:  # Analyze top 5 for demo
            print(f"\n🏁 Analyzing {driver_id}...")

            report = analyzer.analyze_session(session, driver_id)
            all_reports[session_name][driver_id] = report

            print(f"✅ Report generated for {driver_id}")

    # Save all reports
    output_file = f1_data_path.replace('.json', '_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(all_reports, f, indent=2)

    print(f"\n✅ All analyses saved to {output_file}")
    return all_reports


if __name__ == '__main__':
    # Check for API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your-key-here'")
    else:
        analyze_austin_data('./f1_cache/austin_2024_complete.json')
