import React, { useState } from 'react';
import AddProduct from './pages/cabinet/AddProduct.jsx';
import CabinetOverview from './pages/cabinet/CabinetOverview.jsx';
import ReminderCenter from './pages/report/ReminderCenter.jsx';
import ConsumptionReport from './pages/report/ConsumptionReport.jsx';

const TABS = [
  { key: 'cabinet', label: '柜子' },
  { key: 'add', label: '添加' },
  { key: 'reminder', label: '提醒' },
  { key: 'report', label: '报表' }
];

export default function App() {
  const [tab, setTab] = useState('cabinet');
  const [refreshKey, setRefreshKey] = useState(0);
  const bumpRefresh = () => setRefreshKey((k) => k + 1);

  return (
    <div className="phone-frame">
      <header className="app-header">
        <span className="app-title">🐱 梳妆台管家</span>
      </header>

      <main className="app-content">
        {tab === 'cabinet' && <CabinetOverview refreshKey={refreshKey} />}
        {tab === 'add' && <AddProduct onCreated={() => { bumpRefresh(); setTab('cabinet'); }} />}
        {tab === 'reminder' && <ReminderCenter refreshKey={refreshKey} />}
        {tab === 'report' && <ConsumptionReport refreshKey={refreshKey} />}
      </main>

      <nav className="tab-bar">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab-item ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
