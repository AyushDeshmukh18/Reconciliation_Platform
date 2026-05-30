import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'cd backend && python -m backend.db.seed',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
      timeout: 30 * 1000,
      cwd: '.',
    },
    {
      command: 'cd backend && .\\venv\\Scripts\\uvicorn.exe backend.api.main:create_app --factory --host 127.0.0.1 --port 8000',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
      timeout: 120 * 1000,
      cwd: '.',
    },
    {
      command: 'cd frontend && npm run dev',
      url: 'http://localhost:5174',
      reuseExistingServer: true,
      timeout: 120 * 1000,
      cwd: '.',
    }
  ]
});
