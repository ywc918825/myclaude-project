import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { coreApi } from '../../api/coreApi';
import { reminderApi } from '../../api/reminderApi';

// Fixed-order categorical colors for the known category set from DESIGN.md
// (护肤 / 彩妆 / 身体护理). Validated for CVD-safe separation with
// scripts/validate_palette.js from the dataviz skill.
const CATEGORY_COLORS = {
  '护肤': '#f4678f',
  '彩妆': '#7c5cd6',
  '身体护理': '#1f9e88'
};
const FALLBACK_CATEGORY_COLOR = '#b9aab3';

export function formatCNY(value) {
  const n = Number(value) || 0;
  return `¥${Math.round(n)}`;
}

// monthlyOpened's exact shape is ambiguous in DESIGN.md (see final report),
// so this accepts the two most plausible encodings:
//   1) an object map:      { "2026-01": { count, costCNY }, ... }
//   2) an array of single-key objects: [{ "2026-01": { count, costCNY } }, ...]
// as well as a flattened array [{ month, count, costCNY }, ...] just in case.
export function normalizeMonthly(monthlyOpened) {
  if (!monthlyOpened) return [];

  if (Array.isArray(monthlyOpened)) {
    return monthlyOpened
      .map((entry) => {
        if (!entry || typeof entry !== 'object') return null;
        if ('month' in entry) {
          return { month: entry.month, count: entry.count || 0, costCNY: entry.costCNY || 0 };
        }
        const [month, val] = Object.entries(entry)[0] || [];
        if (!month) return null;
        return { month, count: val?.count || 0, costCNY: val?.costCNY || 0 };
      })
      .filter(Boolean)
      .sort((a, b) => a.month.localeCompare(b.month));
  }

  return Object.entries(monthlyOpened)
    .map(([month, val]) => ({ month, count: val?.count || 0, costCNY: val?.costCNY || 0 }))
    .sort((a, b) => a.month.localeCompare(b.month));
}

function StatTile({ label, value, color }) {
  return (
    <div style={{ flex: 1, textAlign: 'center' }}>
      <div style={{ fontSize: 20, fontWeight: 700, color: color || 'var(--ink)' }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{label}</div>
    </div>
  );
}

function MonthlyTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const { costCNY, count } = payload[0].payload;
  return (
    <div
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: '8px 10px',
        fontSize: 12,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <div>支出：{formatCNY(costCNY)}</div>
      <div>开封数：{count}</div>
    </div>
  );
}

export default function ConsumptionReport({ refreshKey }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    coreApi.listProducts()
      .then((products) => reminderApi.getReport(products))
      .then((data) => {
        if (cancelled) return;
        setReport(data);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (loading) {
    return <div className="card"><div className="empty-state">加载中…</div></div>;
  }

  if (error || !report) {
    return <div className="card"><div className="empty-state">加载失败，请稍后重试</div></div>;
  }

  if (!report.totalItems) {
    return <div className="card"><div className="empty-state">暂无消费数据</div></div>;
  }

  const categoryBreakdown = report.categoryBreakdown || {};
  const categoryEntries = Object.entries(categoryBreakdown);
  const maxCategoryVal = Math.max(1, ...categoryEntries.map(([, v]) => v));
  const monthlyData = normalizeMonthly(report.monthlyOpened);

  return (
    <div>
      <div className="card">
        <div className="section-title">消费概览</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <StatTile label="总件数" value={String(report.totalItems)} />
          <StatTile label="总价值" value={formatCNY(report.totalValueCNY)} />
          <StatTile label="浪费金额" value={formatCNY(report.wastedValueCNY)} color="var(--expired)" />
        </div>
      </div>

      <div className="card">
        <div className="section-title">分类占比</div>
        {categoryEntries.length === 0 ? (
          <div className="empty-state">暂无分类数据</div>
        ) : (
          categoryEntries.map(([category, value]) => (
            <div key={category} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                <span>{category}</span>
                <span style={{ color: 'var(--muted)' }}>{value}</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${(value / maxCategoryVal) * 100}%`,
                    background: CATEGORY_COLORS[category] || FALLBACK_CATEGORY_COLOR
                  }}
                />
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <div className="section-title">月度开封支出趋势</div>
        {monthlyData.length === 0 ? (
          <div className="empty-state">暂无月度数据</div>
        ) : (
          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#f2dde4" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: '#8a7b83' }}
                  axisLine={{ stroke: '#f2dde4' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#8a7b83' }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                />
                <Tooltip content={<MonthlyTooltip />} cursor={{ fill: '#ffe4ec' }} />
                <Bar dataKey="costCNY" fill="#f4678f" radius={[4, 4, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
