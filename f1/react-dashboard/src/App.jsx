import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import './styles/app.css';

export default function App() {
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [selectedSession, setSelectedSession] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [view, setView] = useState('dashboard'); // dashboard, telemetry, comparison
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDrivers();
  }, []);

  const loadDrivers = async () => {
    try {
      const response = await fetch('/data/driver_reports/all_drivers_summary.json');
      const data = await response.json();
      setDrivers(data.driver_reports || []);
      if (Object.keys(data.driver_reports).length > 0) {
        setSelectedDriver(Object.keys(data.driver_reports)[0]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error loading drivers:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Loading F1 Performance Data...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar
        drivers={drivers}
        selectedDriver={selectedDriver}
        onSelectDriver={setSelectedDriver}
        selectedSession={selectedSession}
        onSelectSession={setSelectedSession}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        view={view}
        onViewChange={setView}
      />
      <main className="app-main">
        <Dashboard
          drivers={drivers}
          selectedDriver={selectedDriver}
          selectedSession={selectedSession}
          view={view}
        />
      </main>
    </div>
  );
}
