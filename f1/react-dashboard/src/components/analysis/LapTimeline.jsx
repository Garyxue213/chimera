import React from 'react';
import '../../styles/lap-timeline.css';

export default function LapTimeline({ laps, selectedLap, onSelectLap }) {
  const getPerformanceColor = (assessment) => {
    if (assessment.includes('Best')) return 'best';
    if (assessment.includes('Exceptional')) return 'exceptional';
    if (assessment.includes('Good')) return 'good';
    if (assessment.includes('Decent')) return 'decent';
    return 'poor';
  };

  return (
    <div className="lap-timeline">
      <h2 className="timeline-title">Lap Progression</h2>

      <div className="timeline-scroll">
        {laps.map((lap, idx) => {
          const isSelected = selectedLap?.lap_number === lap.lap_number;
          const color = getPerformanceColor(lap.analysis.performance_assessment);
          const isBest = lap.analysis.is_best_lap;

          return (
            <button
              key={idx}
              className={`timeline-lap ${color} ${isSelected ? 'selected' : ''} ${isBest ? 'best-lap' : ''}`}
              onClick={() => onSelectLap(lap)}
              title={`${lap.lap_time_seconds.toFixed(3)}s`}
            >
              <span className="lap-number">L{lap.lap_number}</span>
              <span className="lap-time">{lap.lap_time_seconds.toFixed(2)}s</span>

              {isBest && <span className="best-badge">⭐</span>}

              {lap.analysis.issues && lap.analysis.issues.length > 0 && (
                <span className="issue-badge">⚠️ {lap.analysis.issues.length}</span>
              )}
            </button>
          );
        })}
      </div>

      <div className="timeline-legend">
        <div className="legend-item best">
          ⭐ Best Lap
        </div>
        <div className="legend-item exceptional">
          🟢 Exceptional
        </div>
        <div className="legend-item good">
          🟡 Good
        </div>
        <div className="legend-item poor">
          🔴 Poor
        </div>
      </div>
    </div>
  );
}
