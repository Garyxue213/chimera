import React, { useMemo } from 'react';
import StatCard from '../StatCard';
import PerformanceChart from '../charts/PerformanceChart';
import SessionChart from '../charts/SessionChart';
import DriverProfile from '../DriverProfile';
import '../../styles/views.css';

export default function PerformanceView({
  drivers,
  selectedDriver,
  selectedSession,
}) {
  const currentDriver = drivers[selectedDriver];

  const stats = useMemo(() => {
    if (!currentDriver) return null;

    const summary = currentDriver.executive_summary;
    const sessions = currentDriver.session_breakdown;

    return {
      rating: summary?.avg_performance_rating || 0,
      pbs: summary?.personal_bests || 0,
      bestLapTime: summary?.best_lap_time || 0,
      maxSpeed: currentDriver.telemetry_highlights?.max_speed_recorded || 0,
      avgSpeed: currentDriver.telemetry_highlights?.avg_max_speed || 0,
      drsEvents: currentDriver.telemetry_highlights?.total_drs_events || 0,
    };
  }, [currentDriver]);

  if (!currentDriver || !stats) {
    return <div className="view-container">Select a driver to view details</div>;
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>🏎️ {selectedDriver} Performance Dashboard</h1>
        <p className="view-subtitle">
          Comprehensive performance analysis across sessions
        </p>
      </header>

      <section className="stats-grid">
        <StatCard
          label="Performance Rating"
          value={stats.rating.toFixed(1)}
          unit="/10"
          icon="⭐"
          color={
            stats.rating >= 8 ? 'exceptional' :
            stats.rating >= 7 ? 'strong' :
            stats.rating >= 5 ? 'consistent' :
            'developing'
          }
        />
        <StatCard
          label="Personal Bests"
          value={stats.pbs}
          icon="🎯"
          color="exceptional"
        />
        <StatCard
          label="Best Lap Time"
          value={stats.bestLapTime.toFixed(3)}
          unit="s"
          icon="⏱️"
          color="strong"
        />
        <StatCard
          label="Max Speed"
          value={stats.maxSpeed.toFixed(0)}
          unit="km/h"
          icon="⚡"
          color="exceptional"
        />
      </section>

      <section className="charts-grid">
        <div className="chart-container">
          <h2 className="chart-title">Performance by Session</h2>
          <SessionChart
            sessions={currentDriver.session_breakdown}
          />
        </div>
        <div className="chart-container">
          <h2 className="chart-title">Driver Rankings</h2>
          <PerformanceChart drivers={drivers} />
        </div>
      </section>

      <section className="profile-section">
        <DriverProfile
          driver={currentDriver}
          driverId={selectedDriver}
        />
      </section>
    </div>
  );
}
