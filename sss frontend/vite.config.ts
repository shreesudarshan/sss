import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

function parsePort(rawPort: string | undefined, fallback: number): number {
  const value = Number.parseInt(rawPort ?? "", 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const devPort = parsePort(env.VITE_DEV_PORT, 5173);

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: devPort,
      strictPort: true,
    },
    preview: {
      host: "0.0.0.0",
      port: devPort,
      strictPort: true,
    },
  };
})
