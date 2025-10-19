import React, { useMemo } from 'react';
import '../styles/sidebar.css';

export default function Sidebar({
  drivers,
  selectedDriver,
  onSelectDriver,
  selectedSession,
  onSelectSession,
  searchTerm,
  onSearchChange,
  view,
  onViewChange,
}) {
  const filteredDrivers = useMemo(() => {
    return Object.entries(drivers)
      .filter(([id, data]) => {
        const matchesSearch = id.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesSession = selectedSession === 'All' ||
          data.session_breakdown &&
          Object.keys(data.session_breakdown).some(session =>
            session.includes(selectedSession.replace('Sprint ', ''))
          );
        return matchesSearch && matchesSession;
      })
      .sort((a, b) => {
        const ratingA = a[1]?.executive_summary?.avg_performance_rating || 0;
        const ratingB = b[1]?.executive_summary?.avg_performance_rating || 0;
        return ratingB - ratingA;
      });
  }, [drivers, searchTerm, selectedSession]);

  const getPerformanceColor = (rating) => {
    if (rating >= 8) return 'exceptional';
    if (rating >= 7) return 'strong';
    if (rating >= 5) return 'consistent';
    return 'developing';
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">🏁 F1 DASH</h1>
        <p className="sidebar-subtitle">Performance Analysis</p>
      </div>

      <nav className="view-tabs">
        <button
          className={`tab-button ${view === 'dashboard' ? 'active' : ''}`}
          onClick={() => onViewChange('dashboard')}
        >
          📊 Dashboard
        </button>
        <button
          className={`tab-button ${view === 'telemetry' ? 'active' : ''}`}
          onClick={() => onViewChange('telemetry')}
        >
          📈 Telemetry
        </button>
        <button
          className={`tab-button ${view === 'comparison' ? 'active' : ''}`}
          onClick={() => onViewChange('comparison')}
        >
          ⚔️ Compare
        </button>
        <button
          className={`tab-button ${view === 'analysis' ? 'active' : ''}`}
          onClick={() => onViewChange('analysis')}
        >
          ⏱️ Analysis
        </button>
        <button
          className={`tab-button ${view === 'race' ? 'active' : ''}`}
          onClick={() => onViewChange('race')}
        >
          🏁 Race
        </button>
      </nav>

      <div className="filters">
        <input
          type="text"
          placeholder="Search drivers..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="search-input"
        />

        <select
          value={selectedSession}
          onChange={(e) => onSelectSession(e.target.value)}
          className="session-select"
        >
          <option value="All">All Sessions</option>
          <option value="Qualifying">Qualifying</option>
          <option value="Sprint Qualifying">Sprint Qualifying</option>
          <option value="Sprint Race">Sprint Race</option>
        </select>
      </div>

      <div className="drivers-list">
        <h2 className="drivers-title">Drivers</h2>
        <div className="drivers-grid">
          {filteredDrivers.map(([id, data]) => {
            const rating = data?.executive_summary?.avg_performance_rating || 0;
            const color = getPerformanceColor(rating);

            return (
              <button
                key={id}
                className={`driver-card ${id === selectedDriver ? 'selected' : ''} ${color}`}
                onClick={() => onSelectDriver(id)}
                title={`${id} - ${rating.toFixed(1)}/10`}
              >
                <div className="driver-id">{id}</div>
                <div className="driver-rating">{rating.toFixed(1)}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="sidebar-footer">
        <p className="drivers-count">
          {filteredDrivers.length} driver{filteredDrivers.length !== 1 ? 's' : ''}
        </p>
        <p className="total-laps">224 total laps analyzed</p>
      </div>
    </aside>
  );
}
