import React from 'react';
import { Globe, Lightbulb, FileSpreadsheet, ListChecks } from 'lucide-react';

export default function StatsGrid({ sourcesCount, insightsCount, wordCount, stepsCount }) {
  const stats = [
    {
      label: 'Sources',
      value: sourcesCount,
      icon: <Globe size={22} />,
      colorClass: 'stat-sources',
    },
    {
      label: 'Insights',
      value: insightsCount,
      icon: <Lightbulb size={22} />,
      colorClass: 'stat-insights',
    },
    {
      label: 'Words',
      value: wordCount.toLocaleString(),
      icon: <FileSpreadsheet size={22} />,
      colorClass: 'stat-words',
    },
    {
      label: 'Steps',
      value: stepsCount,
      icon: <ListChecks size={22} />,
      colorClass: 'stat-steps',
    },
  ];

  return (
    <div className="stats-grid">
      {stats.map((stat, index) => (
        <div key={index} className={`stat-card ${stat.colorClass}`}>
          <div className="stat-icon-wrapper">
            {stat.icon}
          </div>
          <div className="stat-content">
            <span className="stat-value">{stat.value}</span>
            <span className="stat-label">{stat.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
