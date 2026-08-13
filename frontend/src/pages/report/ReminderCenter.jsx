import React, { useEffect, useState } from 'react';
import { coreApi } from '../../api/coreApi';
import { reminderApi } from '../../api/reminderApi';
import { isNotificationsEnabled, setNotificationsEnabled, maybeNotify } from '../../notifications.js';

export function daysRemainingText(product) {
  if (product.status === 'expired') {
    const overdue = Math.abs(product.daysRemaining);
    return overdue > 0 ? `已过期 ${overdue} 天` : '已过期';
  }
  return `剩余 ${product.daysRemaining} 天`;
}

export default function ReminderCenter({ refreshKey }) {
  const [expiringProducts, setExpiringProducts] = useState([]);
  const [expiringLoading, setExpiringLoading] = useState(true);
  const [expiringError, setExpiringError] = useState(false);

  const [conflicts, setConflicts] = useState([]);
  const [conflictsLoading, setConflictsLoading] = useState(true);
  const [conflictsError, setConflictsError] = useState(false);

  const notificationSupported = typeof window !== 'undefined' && 'Notification' in window;
  const [notifyEnabled, setNotifyEnabled] = useState(() => notificationSupported && isNotificationsEnabled());
  const [notifyPermission, setNotifyPermission] = useState(() =>
    notificationSupported ? Notification.permission : 'unsupported'
  );

  const handleEnableNotifications = async () => {
    if (!notificationSupported) return;
    const permission = await Notification.requestPermission();
    setNotifyPermission(permission);
    if (permission === 'granted') {
      setNotificationsEnabled(true);
      setNotifyEnabled(true);
    }
  };

  const handleDisableNotifications = () => {
    setNotificationsEnabled(false);
    setNotifyEnabled(false);
  };

  // Fire (at most once/day) once we know how many products need attention.
  // This only works while the page is open in a browser tab — it is not a
  // true background push notification (that needs a service worker + push
  // server, out of scope for this prototype).
  useEffect(() => {
    if (!notifyEnabled || notifyPermission !== 'granted' || expiringLoading) return;
    maybeNotify(expiringProducts.length);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifyEnabled, notifyPermission, expiringLoading, expiringProducts.length]);

  useEffect(() => {
    let cancelled = false;

    setExpiringLoading(true);
    setExpiringError(false);
    setConflictsLoading(true);
    setConflictsError(false);

    coreApi.listProducts()
      .then((products) => {
        if (cancelled) return;

        const expiring = products
          .filter((p) => p.status === 'warning' || p.status === 'expired')
          .sort((a, b) => a.daysRemaining - b.daysRemaining);
        setExpiringProducts(expiring);
        setExpiringLoading(false);

        // Conflict check is fetched independently so a failure here never
        // blanks out the already-loaded expiry section above.
        const payload = products.map((p) => ({ id: p.id, name: p.name, ingredientTags: p.ingredientTags }));
        reminderApi.checkConflicts(payload)
          .then((hits) => {
            if (cancelled) return;
            setConflicts(Array.isArray(hits) ? hits : []);
            setConflictsLoading(false);
          })
          .catch(() => {
            if (cancelled) return;
            setConflictsError(true);
            setConflictsLoading(false);
          });
      })
      .catch(() => {
        if (cancelled) return;
        // Product list failed to load, so neither section has data.
        setExpiringError(true);
        setExpiringLoading(false);
        setConflictsError(true);
        setConflictsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <div>
      <div className="card">
        <div className="section-title">到期提醒通知</div>
        {!notificationSupported ? (
          <div className="empty-state">当前浏览器不支持通知</div>
        ) : notifyPermission === 'denied' ? (
          <div style={{ fontSize: 13, color: 'var(--muted)' }}>通知权限被拒绝，请在浏览器设置中为此网站开启通知权限</div>
        ) : notifyEnabled && notifyPermission === 'granted' ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
            <span className="status-ok">提醒通知已开启（每天最多提醒一次，仅在打开本页面时生效）</span>
            <button
              type="button"
              onClick={handleDisableNotifications}
              style={{ border: 'none', background: 'none', color: 'var(--muted)', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
            >
              关闭
            </button>
          </div>
        ) : (
          <button type="button" className="btn-primary" onClick={handleEnableNotifications}>
            🔔 开启到期提醒通知
          </button>
        )}
      </div>

      <div className="card">
        <div className="section-title">即将到期</div>
        {expiringLoading ? (
          <div className="empty-state">加载中…</div>
        ) : expiringError ? (
          <div className="empty-state">加载失败，请稍后重试</div>
        ) : expiringProducts.length === 0 ? (
          <div className="empty-state">暂无即将到期的产品</div>
        ) : (
          expiringProducts.map((p) => (
            <div className="card" key={p.id} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{p.brand}</div>
                </div>
                <span className={`badge status-${p.status}`}>{daysRemainingText(p)}</span>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <div className="section-title">成分冲突提醒</div>
        {conflictsLoading ? (
          <div className="empty-state">加载中…</div>
        ) : conflictsError ? (
          <div className="empty-state">加载失败，请稍后重试</div>
        ) : conflicts.length === 0 ? (
          <div className="empty-state">未检测到成分冲突</div>
        ) : (
          conflicts.map((c, idx) => (
            <div
              className="card"
              key={`${c.productAId}-${c.productBId}-${c.ingredientA}-${c.ingredientB}-${idx}`}
              style={{ marginBottom: 8 }}
            >
              <div style={{ fontSize: 14, lineHeight: 1.5 }}>
                「{c.productAName}」含{c.ingredientA} + 「{c.productBName}」含{c.ingredientB}：{c.reason}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
