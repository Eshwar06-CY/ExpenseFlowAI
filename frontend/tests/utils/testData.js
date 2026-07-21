/**
 * Test Data Generator Utilities for ExpenseFlow E2E Tests
 */

export const generateEmail = (prefix = 'testuser') => {
  const timestamp = Date.now();
  const randomSuffix = Math.floor(Math.random() * 10000);
  return `${prefix}_${timestamp}_${randomSuffix}@example.com`;
};

export const generateName = (prefix = 'Demo') => {
  const randomSuffix = Math.floor(Math.random() * 10000);
  return `${prefix} Name ${randomSuffix}`;
};

export const generateAmount = (min = 10, max = 5000) => {
  const value = Math.random() * (max - min) + min;
  return parseFloat(value.toFixed(2));
};

export const generateDescription = (type = 'transaction') => {
  const descriptions = {
    transaction: ['Coffee with client', 'Office supplies', 'Server hosting invoice', 'Monthly subscription', 'Consulting payout'],
    account: ['Checking Primary', 'Savings High-Yield', 'Business Credit Card', 'Investment Brokerage'],
    budget: ['Q3 Marketing budget', 'Travel & Lodging quota', 'SaaS subscriptions allowance', 'Equipment reserves'],
    goal: ['Emergency backup fund', 'Office redesign goal', 'Tax payment reserves', 'Annual retreat fund']
  };

  const pool = descriptions[type] || descriptions.transaction;
  const item = pool[Math.floor(Math.random() * pool.length)];
  return `${item} - ${Math.floor(Math.random() * 1000)}`;
};

export const generateDate = (offsetDays = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split('T')[0]; // Returns YYYY-MM-DD
};

export const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};
