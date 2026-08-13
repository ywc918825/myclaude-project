import React, { useEffect, useRef, useState } from 'react';

// Props: { onDetected: (barcodeText: string) => void, onClose: () => void }
// Full-screen camera overlay that continuously scans for a barcode using
// zxing (pure client-side, works across browsers — the native
// BarcodeDetector API isn't consistently available, e.g. on iOS Safari).
export default function BarcodeScanner({ onDetected, onClose }) {
  const videoRef = useRef(null);
  const controlsRef = useRef(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    import('@zxing/browser')
      .then(({ BrowserMultiFormatReader }) => {
        if (cancelled) return;
        const reader = new BrowserMultiFormatReader();
        return reader.decodeFromVideoDevice(undefined, videoRef.current, (result, err, controls) => {
          controlsRef.current = controls;
          if (cancelled || !result) return;
          controls.stop();
          onDetected(result.getText());
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err.name === 'NotAllowedError'
            ? '没有摄像头权限，请在浏览器设置里允许访问摄像头后重试'
            : `无法启动摄像头：${err.message}`
        );
      });

    return () => {
      cancelled = true;
      controlsRef.current && controlsRef.current.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(20, 10, 15, 0.92)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20
      }}
    >
      {error ? (
        <div style={{ color: 'white', textAlign: 'center', maxWidth: 320 }}>
          <div style={{ marginBottom: 16 }}>{error}</div>
          <button type="button" className="btn-primary" onClick={onClose}>
            关闭
          </button>
        </div>
      ) : (
        <>
          <video
            ref={videoRef}
            muted
            playsInline
            style={{ width: '100%', maxWidth: 420, borderRadius: 14 }}
          />
          <div style={{ color: 'white', marginTop: 16, fontSize: 14 }}>将条码对准取景框，会自动识别</div>
          <button
            type="button"
            onClick={onClose}
            style={{
              marginTop: 20,
              background: 'white',
              border: 'none',
              borderRadius: 999,
              padding: '10px 28px',
              fontSize: 14,
              cursor: 'pointer'
            }}
          >
            取消
          </button>
        </>
      )}
    </div>
  );
}
