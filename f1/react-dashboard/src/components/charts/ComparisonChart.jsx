import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function ComparisonChart({
  driver1,
  driver1Id,
  driver2,
  driver2Id,
}) {
  const chartData = useMemo(() => {
    if (!driver1 || !driver2) return null;

    const sessions1 = Object.entries(driver1.session_breakdown || {});
    const sessions2 = Object.entries(driver2.session_breakdown || {});

    // Average ratings across sessions
    const avg1 = sessions1.length > 0
      ? sessions1.reduce((sum, [_, data]) => sum + data.avg_performance_rating, 0) /
        sessions1.length
      : 0;
    const avg2 = sessions2.length > 0
      ? sessions2.reduce((sum, [_, data]) => sum + data.avg_performance_rating, 0) /
        sessions2.length
      : 0;

    return {
      labels: [
        'Overall Rating',
        'Personal Bests',
        'Best Lap Time',
        'Max Speed',
        'Telemetry Avg',
      ],
      datasets: [
        {
          label: driver1Id,
          data: [
            driver1.executive_summary.avg_performance_rating,
            driver1.executive_summary.personal_bests,
            10 - Math.min(driver1.executive_summary.best_lap_time / 10, 2),
            driver1.telemetry_highlights.max_speed_recorded / 30,
            avg1,
          ],
          backgroundColor: 'rgba(96, 165, 250, 0.7)',
          borderColor: 'rgb(96, 165, 250)',
          borderWidth: 2,
          borderRadius: 8,
        },
        {
          label: driver2Id,
          data: [
            driver2.executive_summary.avg_performance_rating,
            driver2.executive_summary.personal_bests,
            10 - Math.min(driver2.executive_summary.best_lap_time / 10, 2),
            driver2.telemetry_highlights.max_speed_recorded / 30,
            avg2,
          ],
          backgroundColor: 'rgba(74, 222, 128, 0.7)',
          borderColor: 'rgb(74, 222, 128)',
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    };
  }, [driver1, driver1Id, driver2, driver2Id]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#ff6b35',
        borderWidth: 1,
        padding: 12,
      },
      legend: {
        labels: {
          color: '#e0e0e0',
          font: {
            size: 12,
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 10,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false,
        },
        ticks: {
          color: '#a0a0a0',
          font: {
            size: 12,
          },
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#e0e0e0',
          font: {
            size: 12,
          },
        },
      },
    },
  };

  if (!chartData) return <div>No comparison data available</div>;

  return (
    <div style={{ height: 300 }}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
