import React from 'react';
import '../../styles/performance-summary.css';

export default function PerformanceSummary({ summary, metadata }) {
  return (
    <div className="performance-summary">
      <h2 className="summary-title">Session Summary</h2>

      <div className="summary-stats">
        <div className="stat-item">
          <span className="stat-label">Best Lap</span>
          <span className="stat-value">{summary.best_lap_time?.toFixed(3)}s</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Average Lap</span>
          <span className="stat-value">
            {summary.average_lap_time?.toFixed(3)}s
          </span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Total Laps</span>
          <span className="stat-value">{summary.total_laps}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Personal Bests</span>
          <span className="stat-value">{summary.total_pbs}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Avg Max Speed</span>
          <span className="stat-value">
            {summary.avg_max_speed?.toFixed(0)} km/h
          </span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Avg Avg Speed</span>
          <span className="stat-value">
            {summary.avg_avg_speed?.toFixed(0)} km/h
          </span>
        </div>
      </div>

      <div className="summary-meta">
        <p className="meta-info">
          📅 {new Date(metadata.date).toLocaleDateString()}
        </p>
        <p className="meta-info">
          🏁 {metadata.circuit} {metadata.year}
        </p>
      </div>
    </div>
  );
}
