import { test, expect } from '@playwright/test';
import { readFileSync } from 'fs';
import { join } from 'path';

const samplePlatformPath = join(__dirname, '../test_data/platform_sample_small.csv');
const sampleBankPath = join(__dirname, '../test_data/bank_settlement_sample_small.csv');

test('Landing page loads correctly', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Start Reconciling')).toBeVisible();
});

test('Navigate to Dashboard and Start Reconciliation', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await expect(page).toHaveURL('/dashboard');
  
  await expect(page.getByText('Total Records')).toBeVisible();
  await expect(page.getByRole('button', { name: /Start Reconciliation/i })).toBeVisible();
});

test('Navigate to Upload Center', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await page.getByText('Upload Center').click();
  await expect(page).toHaveURL('/upload');
  await expect(page.getByText('Drag & Drop')).toBeVisible();
});

test('Navigate to Exception Workbench', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await page.getByText('Exceptions').click();
  await expect(page).toHaveURL('/exceptions');
});

test('Navigate to Transactions', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await page.getByText('Transactions').click();
  await expect(page).toHaveURL('/transactions');
});

test('Navigate to Reports', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await page.getByText('Reports').click();
  await expect(page).toHaveURL('/reports');
});

test('Navigate to Audit Log', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Start Reconciling').click();
  await page.getByText('Audit').click();
  await expect(page).toHaveURL('/audit');
});
