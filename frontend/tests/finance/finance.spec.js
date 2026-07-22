import { test, expect } from '../fixtures/testFixtures';
import { generateEmail, generateName, generateAmount } from '../utils/testData';

test.describe('ExpenseFlow Core Finance Module E2E Suite', () => {
  const commonPassword = 'Password123!';

  // Helper to register a new user and log in to a clean dashboard workspace
  const setupCleanSession = async (registerPage, loginPage, page) => {
    const email = generateEmail('finance_sdet');
    const name = generateName('FinanceUser');
    
    // Register
    await registerPage.register({
      name,
      email,
      password: commonPassword,
      confirmPassword: commonPassword,
      acceptTerms: true
    });
    
    // Set localStorage before login to bypass onboarding wizard completely
    await page.evaluate(() => {
      localStorage.setItem('ef_onboarding_skipped', 'true');
    });

    // Login
    await loginPage.login(email, commonPassword);
    await expect(page).toHaveURL(/\/dashboard/);
    
    return { email, name };
  };

  // --- 1. DASHBOARD ---
  test.describe('Dashboard Page E2E', () => {
    test('Verify dashboard components load correctly', async ({ registerPage, loginPage, dashboardPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);
      await dashboardPage.navigate();

      // Check key sections are visible
      await expect(dashboardPage.totalMoneyCard).toBeVisible();
      await expect(dashboardPage.moneySpentCard).toBeVisible();
      await expect(dashboardPage.moneyEarnedCard).toBeVisible();
    });
  });

  // --- 2. ACCOUNTS ---
  test.describe('Accounts Management E2E', () => {
    test('Create Checking and Savings accounts and verify balances', async ({ registerPage, loginPage, accountsPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);
      await accountsPage.navigate();

      // Create primary checking account
      const checkingName = 'Primary Checking ' + generateAmount(100, 999);
      await accountsPage.createAccount({
        name: checkingName,
        type: 'checking',
        balance: 1500.50,
        currency: 'USD'
      });
      await expect(accountsPage.accountCard(checkingName)).toBeVisible();

      // Create backup savings account
      const savingsName = 'High Yield Savings ' + generateAmount(100, 999);
      await accountsPage.createAccount({
        name: savingsName,
        type: 'savings',
        balance: 10000.75,
        currency: 'USD'
      });
      await expect(accountsPage.accountCard(savingsName)).toBeVisible();
    });
  });

  // --- 3. CATEGORIES ---
  test.describe('Categories Management E2E', () => {
    test('Seed default categories templates', async ({ registerPage, loginPage, categoriesPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);
      await categoriesPage.navigate();

      // Trigger seed defaults
      await categoriesPage.seedDefaults();
      
      // Verify a common default category is visible on grid (e.g. food utensils glyph Utensils🍴 or Utensils)
      const foodCategoryCard = page.locator('div:has-text("Food")').first();
      await expect(foodCategoryCard).toBeVisible();
    });

    test('Create custom tags category', async ({ registerPage, loginPage, categoriesPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);
      await categoriesPage.navigate();

      const customCatName = 'Hobbies ' + generateAmount(100, 999);
      await categoriesPage.createCategory({
        name: customCatName,
        type: 'expense'
      });

      // Verify tag is present on grid
      await expect(categoriesPage.categoryCard(customCatName)).toBeVisible();
    });
  });

  // --- 4. INCOME ---
  test.describe('Income Transaction Logging E2E', () => {
    test('Log income record and verify dashboard totals updates', async ({ registerPage, loginPage, accountsPage, categoriesPage, incomePage, dashboardPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);

      // 1. Create a Checking Account
      await accountsPage.navigate();
      const checkingName = 'Salary Account';
      await accountsPage.createAccount({ name: checkingName, type: 'checking', balance: 0 });

      // 2. Seed categories
      await categoriesPage.navigate();
      await categoriesPage.seedDefaults();

      // 3. Add Income transaction
      await incomePage.navigate();
      const incomeDesc = 'Monthly Salary Payroll';
      await incomePage.createIncome({
        amount: 3500.00,
        description: incomeDesc,
        account: checkingName,
        category: 'Salary'
      });

      // 4. Verify transaction row exists
      await expect(incomePage.transactionRow(incomeDesc)).toBeVisible();

      // 5. Navigate to Dashboard and verify total money earned is correct
      await dashboardPage.navigate();
      await expect(dashboardPage.moneyEarnedCard.locator('h3').first()).toContainText('3,500');
    });
  });

  // --- 5. EXPENSES ---
  test.describe('Expense Logging and Account Balance Impact E2E', () => {
    test('Record category expense and assert account deduction', async ({ registerPage, loginPage, accountsPage, categoriesPage, expensePage, dashboardPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);

      // 1. Create checking account with $1000 starting balance
      await accountsPage.navigate();
      const checkAcc = 'Expense Check Account';
      await accountsPage.createAccount({ name: checkAcc, type: 'checking', balance: 1000.00 });

      // 2. Seed categories
      await categoriesPage.navigate();
      await categoriesPage.seedDefaults();

      // 3. Record $250.00 expense
      await expensePage.navigate();
      const expenseDesc = 'Groceries Food Market';
      await expensePage.createExpense({
        amount: 250.00,
        description: expenseDesc,
        account: checkAcc,
        category: 'Food'
      });

      // 4. Verify expense row logged
      await expect(expensePage.expenseListRow(expenseDesc)).toBeVisible();

      // 5. Verify remaining account balance on accounts tab matches deduction ($750.00)
      await accountsPage.navigate();
      const cardBalance = await accountsPage.accountCard(checkAcc).textContent();
      expect(cardBalance).toContain('750');

      // 6. Verify Outflow KPI on Dashboard
      await dashboardPage.navigate();
      await expect(dashboardPage.moneySpentCard.locator('h3').first()).toContainText('250');
    });
  });

  // --- 6. TRANSFERS ---
  test.describe('Inter-Account Funds Transfers E2E', () => {
    test('Move cash check and verify target balance balances updates', async ({ registerPage, loginPage, accountsPage, transfersPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);

      // 1. Setup checking ($1000) and savings ($500)
      await accountsPage.navigate();
      const fromAcc = 'Checking Origin';
      const toAcc = 'Savings Target';
      await accountsPage.createAccount({ name: fromAcc, type: 'checking', balance: 1000.00 });
      await accountsPage.createAccount({ name: toAcc, type: 'savings', balance: 500.00 });

      // 2. Perform Transfer of $300.00
      await transfersPage.navigate();
      await transfersPage.makeTransfer({
        fromAccount: fromAcc,
        toAccount: toAcc,
        amount: 300.00,
        description: 'Monthly savings auto allocation'
      });
      await expect(page.locator('div.max-w-md')).toBeHidden();

      // 3. Verify accounts updated (Origin = $700, Target = $800)
      await accountsPage.navigate();
      const originBal = await accountsPage.accountCard(fromAcc).textContent();
      const targetBal = await accountsPage.accountCard(toAcc).textContent();
      expect(originBal).toContain('700');
      expect(targetBal).toContain('800');
    });

    test('Same account target selector warnings', async ({ registerPage, loginPage, accountsPage, transfersPage, page }) => {
      await setupCleanSession(registerPage, loginPage, page);

      // 1. Create two accounts (so the Transfer button is enabled)
      await accountsPage.navigate();
      const singleAcc = 'Standalone Checking';
      const dummyAcc = 'Dummy Account';
      await accountsPage.createAccount({ name: singleAcc, type: 'checking', balance: 500.00 });
      await accountsPage.createAccount({ name: dummyAcc, type: 'savings', balance: 100.00 });

      // 2. Try to transfer to same checking
      await transfersPage.navigate();
      await transfersPage.makeTransfer({
        fromAccount: singleAcc,
        toAccount: singleAcc,
        amount: 100.00,
        description: 'Self loops transfer'
      });

      // 3. Check for same account prevention alert error toast or element block
      const errorMsg = page.locator('.p-3.bg-red-500\\/10, .toast-error, [role="alert"]');
      await expect(errorMsg.first()).toBeVisible();
      await expect(errorMsg.first()).toHaveText(/same|source and destination/i);
    });
  });
});
