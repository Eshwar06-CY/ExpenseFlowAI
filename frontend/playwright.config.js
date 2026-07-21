import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',

    timeout: 30000,

    expect: {
        timeout: 5000,
    },

    fullyParallel: true,

    retries: 1,

    reporter: [
        ['html'],
        ['list']
    ],

    use: {
        baseURL: 'http://localhost:5173',

        headless: false,

        trace: 'on-first-retry',

        screenshot: 'only-on-failure',

        video: 'retain-on-failure',
    },

    projects: [
        {
            name: 'chromium',
            use: {
                ...devices['Desktop Chrome'],
            },
        },
    ],
});