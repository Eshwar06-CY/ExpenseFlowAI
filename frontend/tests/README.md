# ExpenseFlow E2E Playwright Automation Framework Documentation

This directory contains the Playwright E2E automation testing framework for ExpenseFlow. The framework uses the **Page Object Model (POM)** pattern, customized fixtures, and unified random data generation utilities to ensure high scalability and robustness.

---

## Folder Structure

```
tests/
├── auth/                 # TODO: Auth flow specs
├── dashboard/            # TODO: Dashboard widget checks
├── accounts/             # TODO: Account balance specs
├── income/               # TODO: Money earned list specs
├── expenses/             # TODO: Outflows specs
├── transfers/            # TODO: Inter-account routing specs
├── budgets/              # TODO: Limit tracking specs
├── goals/                # TODO: Milestone target specs
├── bills/                # TODO: Due date scheduler specs
├── reports/              # TODO: Document downloads specs
├── analytics/            # TODO: Recharts validation specs
├── settings/             # TODO: Profile config specs
├── navigation/           # TODO: Sidebar routing checks
├── regression/           # TODO: CSS layout specs
├── pages/                # Page Object Model classes
│   ├── BasePage.js       # Shared utility methods and selectors
│   ├── LoginPage.js
│   ├── DashboardPage.js
│   ├── AccountsPage.js
│   ├── IncomePage.js
│   ├── ExpensePage.js
│   ├── BudgetPage.js
│   ├── GoalsPage.js
│   ├── ReportsPage.js
│   ├── SettingsPage.js
│   ├── TransfersPage.js
│   ├── BillsPage.js
│   └── AnalyticsPage.js
├── fixtures/
│   └── testFixtures.js   # custom Page Object and Auth state fixtures
├── utils/
│   └── testData.js       # Random generation utilities
├── smoke.spec.js         # Base sanity verification check
└── README.md             # This documentation
```

---

## How to Run Tests

Ensure you execute all commands from the `frontend/` directory.

### Run in Headless Mode (Default CI)
```bash
npm.cmd run test:e2e
```

### Run in Headed Mode
```bash
npm.cmd run test:e2e:headed
```

### Run in Playwright Interactive UI Mode
```bash
npm.cmd run test:e2e:ui
```

### Open Last HTML Report
```bash
npm.cmd run test:e2e:report
```

---

## Naming Conventions

- **Test Files:** Name files using camelCase with the `.spec.js` extension (e.g. `loginFlow.spec.js`, `createExpense.spec.js`).
- **Page Object Classes:** Name classes using PascalCase with the `Page` suffix (e.g. `LoginPage.js`, `BudgetsPage.js`). Expose single-purpose action methods.
- **Fixture Injectors:** Match class instances in lowercase (e.g. `loginPage`, `accountsPage`).

---

## How to Add New Tests

1. Create a test file in the matching subfolder (e.g. `tests/expenses/addExpense.spec.js`).
2. Import the customized `test` and `expect` utilities from `../fixtures/testFixtures`:
   ```javascript
   import { test, expect } from '../fixtures/testFixtures';
   import { generateAmount, generateDescription } from '../utils/testData';

   test('Can log new expense', async ({ authenticatedPage, expensePage }) => {
     await expensePage.navigate();
     await expensePage.createExpense({
       amount: generateAmount(10, 100),
       description: generateDescription('transaction'),
       account: 'Primary Checking',
       category: 'Food'
     });
     
     // Assertions using Page elements
     await expect(expensePage.expenseListRow(description)).toBeVisible();
   });
   ```

---

## How to Create New Page Objects

1. Create a page file inside the `tests/pages/` folder extending the `BasePage` class:
   ```javascript
   import { BasePage } from './BasePage';

   export class CustomPage extends BasePage {
     constructor(page) {
       super(page);
       this.actionButton = page.locator('button:has-text("Action")');
     }
     
     async triggerAction() {
       await this.actionButton.click();
       await this.waitForLoadingState();
     }
   }
   ```
2. Register the Page Object in `tests/fixtures/testFixtures.js` to enable automatic injection in future tests.
