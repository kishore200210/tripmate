import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('login page has correct elements and attempts login', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Check title
    await expect(page.getByText('Welcome back')).toBeVisible();

    // Fill in credentials
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');

    // Mock the API response to avoid needing the real backend running
    await page.route('**/api/v1/auth/login', async route => {
      const json = { access_token: 'fake-jwt-token', token_type: 'bearer' };
      await route.fulfill({ json });
    });

    await page.route('**/api/v1/users/me', async route => {
      const json = { id: '1', email: 'test@example.com', full_name: 'Test User' };
      await route.fulfill({ json });
    });

    // We also need to mock the dashboard API call if we redirect there
    await page.route('**/api/v1/trips/', async route => {
      await route.fulfill({ json: [] });
    });

    // Submit form
    const loginButton = page.getByRole('button', { name: 'Log In' });
    await loginButton.click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('signup page has correct elements', async ({ page }) => {
    await page.goto('/signup');
    await expect(page.getByText('Create an account')).toBeVisible();
    await expect(page.getByLabel('Full Name')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign Up' })).toBeVisible();
  });
});
