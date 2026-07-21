import { test, expect } from '../fixtures/testFixtures';
import { generateEmail, generateName } from '../utils/testData';

test.describe('ExpenseFlow E2E Authentication Suite', () => {
  const commonPassword = 'Password123!';

  // --- REGISTRATION ---
  test.describe('User Registration Flow', () => {
    test('Successful user registration', async ({ registerPage, page }) => {
      const email = generateEmail('reg_success');
      const name = generateName('RegSuccess');

      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: true
      });

      // Verify redirection back to login page
      await expect(page).toHaveURL(/\/login/);
    });

    test('Should reject password mismatches', async ({ registerPage }) => {
      const email = generateEmail('reg_mismatch');
      const name = generateName('RegMismatch');

      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: 'MismatchPassword123',
        acceptTerms: true
      });

      // Expect to see validation message
      await expect(registerPage.errorMessage).toBeVisible();
      await expect(registerPage.errorMessage).toHaveText(/Passwords do not match/i);
    });

    test('Should reject unchecked terms of service', async ({ registerPage }) => {
      const email = generateEmail('reg_terms');
      const name = generateName('RegTerms');

      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: false
      });

      // Expect to see validation message
      await expect(registerPage.errorMessage).toBeVisible();
      await expect(registerPage.errorMessage).toHaveText(/You must accept the terms/i);
    });

    test('Should reject duplicate registrations', async ({ registerPage }) => {
      const email = generateEmail('reg_dup');
      const name = generateName('RegDup');

      // 1. Create first user
      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: true
      });

      // 2. Try duplicate register
      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: true
      });

      // Verify API error message
      await expect(registerPage.errorMessage).toBeVisible();
      await expect(registerPage.errorMessage).toHaveText(/already registered|already exists/i);
    });
  });

  // --- LOGIN ---
  test.describe('User Login Flow', () => {
    // Generate isolated credentials for login tests to avoid cross-test contamination
    const setupLoginUser = async (registerPage) => {
      const email = generateEmail('login_flow');
      const name = generateName('LoginFlow');
      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: true
      });
      return { email, name };
    };

    test('Successful login and redirect to dashboard', async ({ registerPage, loginPage, page }) => {
      const { email } = await setupLoginUser(registerPage);
      await loginPage.login(email, commonPassword);
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('Reject wrong password credentials', async ({ registerPage, loginPage }) => {
      const { email } = await setupLoginUser(registerPage);
      await loginPage.login(email, 'WrongPassword123');
      await expect(loginPage.page.locator('.p-3.bg-red-500\\/10')).toBeVisible();
      await expect(loginPage.page.locator('.p-3.bg-red-500\\/10')).toHaveText(/failed|credentials|unauthorized|incorrect|password/i);
    });

    test('Form validation checks basic formats', async ({ loginPage, page }) => {
      await loginPage.navigate();
      await loginPage.fillEmail('invalid-email-format');
      await loginPage.fillPassword('pass');
      
      // Submit form
      await loginPage.clickSubmit();
      
      // Verify browser level email format validation constraint if supported or no redirect occurred
      await expect(page).not.toHaveURL(/\/dashboard/);
    });

    test('Remember email preference works', async ({ registerPage, loginPage, page }) => {
      const { email } = await setupLoginUser(registerPage);
      await loginPage.navigate();
      await loginPage.fillEmail(email);
      await loginPage.fillPassword(commonPassword);
      
      const rememberCheckbox = loginPage.page.locator('input[type="checkbox"]');
      await rememberCheckbox.check();
      
      await loginPage.clickSubmit();
      await expect(page).toHaveURL(/\/dashboard/);

      // Re-navigate to login page to verify email value is preserved in storage
      await page.goto('/login');
      await expect(loginPage.emailInput).toHaveValue(email);
    });

    test('Session token persistence over page refresh', async ({ registerPage, loginPage, page }) => {
      const { email } = await setupLoginUser(registerPage);
      await loginPage.login(email, commonPassword);
      await expect(page).toHaveURL(/\/dashboard/);

      // Reload page and verify user stays authenticated on the dashboard
      await page.reload();
      await expect(page).toHaveURL(/\/dashboard/);
    });
  });

  // --- FORGOT PASSWORD ---
  test.describe('Forgot Password Flow', () => {
    test('Submit reset request successfully', async ({ forgotPasswordPage }) => {
      await forgotPasswordPage.submitResetRequest('recovery_email@company.com');
      await expect(forgotPasswordPage.successMessageBox).toBeVisible();
      await expect(forgotPasswordPage.successMessageText).toHaveText(/recovery email to/i);
    });
  });

  // --- LOGOUT & PROTECTED ROUTING ---
  test.describe('Protected Routing & Session Control', () => {
    test('Redirect guests attempting direct dashboard access', async ({ page }) => {
      await page.goto('/dashboard');
      // Should redirect back to login page
      await expect(page).toHaveURL(/\/login/);
    });

    test('Logout button cleans session credentials', async ({ registerPage, loginPage, page }) => {
      const email = generateEmail('logout_flow');
      const name = generateName('LogoutFlow');

      // 1. Setup authenticated user
      await registerPage.register({
        name,
        email,
        password: commonPassword,
        confirmPassword: commonPassword,
        acceptTerms: true
      });
      await loginPage.login(email, commonPassword);
      await expect(page).toHaveURL(/\/dashboard/);

      // 2. Perform logout action
      await loginPage.logout();

      // 3. Verify user redirected back to login page
      await expect(page).toHaveURL(/\/login/);

      // 4. Verify dashboard is no longer accessible via direct navigation
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/login/);
    });
  });
});
