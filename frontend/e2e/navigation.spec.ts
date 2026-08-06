import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate from landing page to destinations and login', async ({ page }) => {
    // Navigate to root
    await page.goto('/');

    // Check hero exists
    await expect(page.getByText('Plan your next adventure with the power of AI.')).toBeVisible();

    // Click Browse Destinations
    await page.getByRole('link', { name: 'Browse Destinations' }).click();
    
    // Check we are redirected to login page because we are unauthenticated
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.getByText('Authenticating...')).not.toBeVisible();
    await expect(page.getByText('Welcome back')).toBeVisible();
  });
});
