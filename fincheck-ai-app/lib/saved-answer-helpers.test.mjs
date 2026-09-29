import test from 'node:test';
import assert from 'node:assert/strict';
import { sortSavedAnswers } from './saved-answer-helpers.js';

test('sortSavedAnswers sorts by newest first by default', () => {
  const items = [
    { id: 'oldest', question: 'Older', savedDate: 'Today, 9:00 AM' },
    { id: 'newest', question: 'Newest', savedDate: 'Today, 4:30 PM' },
    { id: 'mid', question: 'Middle', savedDate: 'Yesterday, 11:00 AM' },
  ];

  const sorted = sortSavedAnswers(items, 'newest');
  assert.deepEqual(sorted.map((item) => item.id), ['newest', 'oldest', 'mid']);
});

test('sortSavedAnswers supports oldest-first ordering', () => {
  const items = [
    { id: 'newest', question: 'Newest', savedDate: 'Today, 4:30 PM' },
    { id: 'oldest', question: 'Oldest', savedDate: 'Today, 9:00 AM' },
  ];

  const sorted = sortSavedAnswers(items, 'oldest');
  assert.deepEqual(sorted.map((item) => item.id), ['oldest', 'newest']);
});
