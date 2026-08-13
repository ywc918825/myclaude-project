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
  const [editingProduct, setEditingProduct] = useState(null);
  const bumpRefresh = () => setRefreshKey((k) => k + 1);

  const goToTab = (key) => {
    setEditingProduct(null); // switching tabs via the nav bar always exits edit mode
    setTab(key);
  };

  return (
    <div className="phone-frame">
      <header className="app-header">
        <span className="app-title">🐱 梳妆台管家</span>
      </header>

      <main className="app-content">
        {tab === 'cabinet' && (
          <CabinetOverview
            refreshKey={refreshKey}
            onEdit={(product) => {
              setEditingProduct(product);
              setTab('add');
            }}
          />
        )}
        {tab === 'add' && (
          <AddProduct
            key={editingProduct ? `edit-${editingProduct.id}` : 'add'}
            editingProduct={editingProduct}
            onSaved={() => {
              setEditingProduct(null);
              bumpRefresh();
              setTab('cabinet');
            }}
            onCancel={() => {
              setEditingProduct(null);
              setTab('cabinet');
            }}
            onProductAdded={bumpRefresh}
          />
        )}
        {tab === 'reminder' && <ReminderCenter refreshKey={refreshKey} />}
        {tab === 'report' && <ConsumptionReport refreshKey={refreshKey} />}
      </main>

      <nav className="tab-bar">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab-item ${tab === t.key ? 'active' : ''}`}
            onClick={() => goToTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
