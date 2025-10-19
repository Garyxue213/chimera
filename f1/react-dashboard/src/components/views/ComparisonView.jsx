import React, { useMemo, useState } from 'react';
import ComparisonChart from '../charts/ComparisonChart';
import '../../styles/comparison-view.css';

export default function ComparisonView({
  drivers,
  selectedDriver,
  selectedSession,
}) {
  const [compareWith, setCompareWith] = useState(null);

  const currentDriver = drivers[selectedDriver];

  const availableDrivers = useMemo(() => {
    return Object.keys(drivers).filter(id => id !== selectedDriver);
  }, [drivers, selectedDriver]);

  const selectedCompareDriver = compareWith ? drivers[compareWith] : null;

  const comparisonStats = useMemo(() => {
    if (!currentDriver || !selectedCompareDriver) return null;

    const current = currentDriver.executive_summary;
    const compare = selectedCompareDriver.executive_summary;

    return {
      rating: {
        current: current.avg_performance_rating,
        compare: compare.avg_performance_rating,
        diff: current.avg_performance_rating - compare.avg_performance_rating,
      },
      pbs: {
        current: current.personal_bests,
        compare: compare.personal_bests,
        diff: current.personal_bests - compare.personal_bests,
      },
      bestLap: {
        current: current.best_lap_time,
        compare: compare.best_lap_time,
        diff: compare.best_lap_time - current.best_lap_time, // Lower is better
      },
      maxSpeed: {
        current: currentDriver.telemetry_highlights?.max_speed_recorded,
        compare: selectedCompareDriver.telemetry_highlights?.max_speed_recorded,
        diff:
          currentDriver.telemetry_highlights?.max_speed_recorded -
          selectedCompareDriver.telemetry_highlights?.max_speed_recorded,
      },
    };
  }, [currentDriver, selectedCompareDriver]);

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>⚔️ Driver Comparison</h1>
        <p className="view-subtitle">
          Head-to-head performance analysis
        </p>
      </header>

      <div className="comparison-controls">
        <div className="driver-selector">
          <label>Compare {selectedDriver} with:</label>
          <select
            value={compareWith || ''}
            onChange={(e) => setCompareWith(e.target.value || null)}
            className="comparison-select"
          >
            <option value="">Select a driver...</option>
            {availableDrivers.map((id) => (
              <option key={id} value={id}>
                {id} - {drivers[id].executive_summary?.avg_performance_rating.toFixed(1)}/10
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedCompareDriver && comparisonStats && (
        <>
          <section className="comparison-stats">
            <div className="comparison-row">
              <div className="stat-column">
                <span className="driver-name">{selectedDriver}</span>
                <span className="stat-value">
                  {comparisonStats.rating.current.toFixed(1)}
                </span>
              </div>
              <div className="stat-column center">
                <span className="stat-label">Performance Rating</span>
                <span className="diff-badge" style={{
                  color: comparisonStats.rating.diff > 0 ? '#4ade80' : '#f87171'
                }}>
                  {comparisonStats.rating.diff > 0 ? '+' : ''}
                  {comparisonStats.rating.diff.toFixed(1)}
                </span>
              </div>
              <div className="stat-column right">
                <span className="driver-name">{compareWith}</span>
                <span className="stat-value">
                  {comparisonStats.rating.compare.toFixed(1)}
                </span>
              </div>
            </div>

            <div className="comparison-row">
              <div className="stat-column">
                <span className="driver-name">{selectedDriver}</span>
                <span className="stat-value">
                  {comparisonStats.pbs.current}
                </span>
              </div>
              <div className="stat-column center">
                <span className="stat-label">Personal Bests</span>
                <span className="diff-badge" style={{
                  color: comparisonStats.pbs.diff > 0 ? '#4ade80' : '#f87171'
                }}>
                  {comparisonStats.pbs.diff > 0 ? '+' : ''}
                  {comparisonStats.pbs.diff}
                </span>
              </div>
              <div className="stat-column right">
                <span className="driver-name">{compareWith}</span>
                <span className="stat-value">
                  {comparisonStats.pbs.compare}
                </span>
              </div>
            </div>

            <div className="comparison-row">
              <div className="stat-column">
                <span className="driver-name">{selectedDriver}</span>
                <span className="stat-value">
                  {comparisonStats.bestLap.current.toFixed(3)}s
                </span>
              </div>
              <div className="stat-column center">
                <span className="stat-label">Best Lap Time</span>
                <span className="diff-badge" style={{
                  color: comparisonStats.bestLap.diff > 0 ? '#4ade80' : '#f87171'
                }}>
                  {comparisonStats.bestLap.diff > 0 ? '+' : ''}
                  {comparisonStats.bestLap.diff.toFixed(3)}s
                </span>
              </div>
              <div className="stat-column right">
                <span className="driver-name">{compareWith}</span>
                <span className="stat-value">
                  {comparisonStats.bestLap.compare.toFixed(3)}s
                </span>
              </div>
            </div>

            <div className="comparison-row">
              <div className="stat-column">
                <span className="driver-name">{selectedDriver}</span>
                <span className="stat-value">
                  {comparisonStats.maxSpeed.current.toFixed(0)} km/h
                </span>
              </div>
              <div className="stat-column center">
                <span className="stat-label">Max Speed</span>
                <span className="diff-badge" style={{
                  color: comparisonStats.maxSpeed.diff > 0 ? '#4ade80' : '#f87171'
                }}>
                  {comparisonStats.maxSpeed.diff > 0 ? '+' : ''}
                  {comparisonStats.maxSpeed.diff.toFixed(1)} km/h
                </span>
              </div>
              <div className="stat-column right">
                <span className="driver-name">{compareWith}</span>
                <span className="stat-value">
                  {comparisonStats.maxSpeed.compare.toFixed(0)} km/h
                </span>
              </div>
            </div>
          </section>

          <section className="chart-section">
            <h2 className="section-title">Detailed Comparison Chart</h2>
            <div className="chart-container">
              <ComparisonChart
                driver1={currentDriver}
                driver1Id={selectedDriver}
                driver2={selectedCompareDriver}
                driver2Id={compareWith}
              />
            </div>
          </section>
        </>
      )}

      {!selectedCompareDriver && (
        <div className="no-comparison">
          <p>👇 Select a driver to compare with {selectedDriver}</p>
        </div>
      )}
    </div>
  );
}
