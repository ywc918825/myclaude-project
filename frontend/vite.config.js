import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import basicSsl from '@vitejs/plugin-basic-ssl';

// Camera access (getUserMedia, used for barcode scanning) only works in a
// "secure context" — HTTPS or localhost. A plain http://<lan-ip>:5173 page
// (the normal way to open this app from a phone on the same WiFi) does NOT
// count as secure, so navigator.mediaDevices is simply undefined there and
// the scanner crashes trying to call it. basicSsl gives the dev server a
// self-signed HTTPS cert (the browser will show a "not secure" warning to
// click through once — that's expected for local dev, not a real problem).
//
// Once the page itself is HTTPS, fetch() calls to the plain-HTTP backend
// APIs would get blocked by the browser's mixed-content policy. The proxy
// below avoids that entirely: the browser only ever talks to this single
// HTTPS origin, and Vite's own Node process (not the browser) forwards
// /proxy/core-api/* and /proxy/reminder-api/* to the two backend ports over
// plain HTTP locally — see src/api/coreApi.js and reminderApi.js, which now
// use these relative paths instead of an absolute http://<host>:<port> URL.
export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/proxy/core-api': {
        target: 'http://localhost:4001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy\/core-api/, '')
      },
      '/proxy/reminder-api': {
        target: 'http://localhost:4002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy\/reminder-api/, '')
      }
    }
  }
});
