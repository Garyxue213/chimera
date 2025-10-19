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

export default function SessionChart({ sessions }) {
  const chartData = useMemo(() => {
    if (!sessions) return null;

    const sessionNames = Object.keys(sessions);
    const ratings = sessionNames.map(session => {
      const data = sessions[session];
      return data?.avg_performance_rating || 0;
    });

    return {
      labels: sessionNames.map(s => s.replace(' Qualifying', ' Q').replace('Sprint Race', 'Race')),
      datasets: [
        {
          label: 'Performance Rating',
          data: ratings,
          backgroundColor: ratings.map(rating =>
            rating >= 8 ? 'rgba(74, 222, 128, 0.7)' :
            rating >= 7 ? 'rgba(96, 165, 250, 0.7)' :
            'rgba(251, 191, 36, 0.7)'
          ),
          borderColor: ratings.map(rating =>
            rating >= 8 ? 'rgb(74, 222, 128)' :
            rating >= 7 ? 'rgb(96, 165, 250)' :
            'rgb(251, 191, 36)'
          ),
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    };
  }, [sessions]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#ff6b35',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (context) => `Rating: ${context.parsed.y.toFixed(1)}/10`,
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
            weight: 600,
          },
        },
      },
    },
  };

  if (!chartData) return <div>No session data available</div>;

  return (
    <div style={{ height: 250 }}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
