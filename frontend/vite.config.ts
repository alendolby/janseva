import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],optimizeDeps:{exclude:["maplibre-gl"]},build:{rollupOptions:{output:{manualChunks:{map:['maplibre-gl'],charts:['recharts']}}}},preview:{proxy:{'/api':process.env.API_PROXY || 'http://127.0.0.1:8000'}},server:{proxy:{'/api':process.env.API_PROXY || 'http://127.0.0.1:8000'}}});
