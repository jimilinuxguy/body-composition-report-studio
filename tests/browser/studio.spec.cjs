const { test, expect } = require('@playwright/test');

test('home page initializes without JavaScript errors and renders regional preview', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#pdf-live-preview')).toBeVisible();
  await expect(page.locator('#pdf-live-preview')).toHaveAttribute('src', /blob:/, { timeout: 15000 });
  await expect(page.locator('#segmental-preview')).toContainText('SEGMENTAL BODY COMPOSITION');
  await expect(page.locator('#segmental-preview')).toContainText('Right arm');
  await expect(page.locator('#segmental-preview')).toContainText('Left leg');
  await expect(page.locator('#trends')).toHaveClass(/workspace-history/);
  expect(await page.locator('#trends').evaluate(el => el.parentElement.tagName)).toBe('MAIN');
  expect(errors).toEqual([]);
});

test('segmental accordion opens, values appear in preview, and fields survive navigation', async ({ page }) => {
  await page.goto('/');
  const group = page.locator('details.segmental-group');
  await expect(group).toHaveAttribute('open', '');
  const rightFat = page.locator('[name="right_arm_fat_lb"]');
  await rightFat.fill('4.2');
  await expect(page.locator('#segmental-preview')).toContainText('4.2 lb');
  await page.locator('#wizard-next').click();
  await expect(rightFat).toHaveValue('4.2');
  await group.locator('summary').click();
  await expect(group).not.toHaveAttribute('open', '');
  await group.locator('summary').click();
  await expect(rightFat).toBeVisible();
  await expect(rightFat).toHaveValue('4.2');
});

test('show all sections expands advanced fields', async ({ page }) => {
  await page.goto('/');
  await page.locator('#wizard-all').click();
  await expect(page.locator('details.measurement-group[open]')).toHaveCount(4);
  await expect(page.locator('[name="impedance_50khz_right_arm_ohm"]')).toBeVisible();
});

test('PDF export succeeds with blank optional notes and numeric fields', async ({ page }) => {
  await page.goto('/');
  await page.locator('[name="notes"]').fill('');
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#download').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/generated_report\.pdf$/);
  await expect(page.locator('#error')).toBeEmpty();
});

test('dated entry populates history and trend workspace', async ({ page }) => {
  await page.goto('/');
  await page.locator('#save-entry').click();
  await expect(page.locator('#entry-count')).toContainText('15 entries');
  await expect(page.locator('#history-table')).toContainText('192.4');
  await expect(page.locator('#trends')).toBeVisible();
});

test('DEXA mode changes the visible measurements and preview', async ({ page }) => {
  await page.goto('/');
  await page.locator('[name="report_type"][value="dexa"]').check();
  await expect(page.locator('[name="arms_fat_pct"]')).toBeVisible();
  await expect(page.locator('#kind')).toContainText('DEXA-STYLE');
  await expect(page.locator('#segmental-preview')).toBeEmpty();
});

test('offline file hydrates all dates and replaces stale browser history', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('bodycomp.history.v2', JSON.stringify([{
    name:'Stale Client',report_type:'inbody',scan_date:'2025-01-01',
    height_in:71,weight_lb:100,body_fat_pct:10
  }])));
  await page.goto('/');
  await expect(page.locator('#entry-count')).toContainText('15 entries');
  await expect(page.locator('[name="name"]')).toHaveValue('Jimi Sanchez');
  await expect(page.locator('[name="weight_lb"]')).toHaveValue('192.4');
  await expect(page.locator('[name="skeletal_muscle_lb"]')).toHaveValue('85.3');
  await expect(page.locator('#history-table')).toContainText('522.4');
  const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('bodycomp.history.v2')));
  expect(stored).toHaveLength(15);
  expect(stored[0].scan_date).toBe('2024-05-15');
});
