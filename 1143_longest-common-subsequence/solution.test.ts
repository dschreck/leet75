import { longestCommonSubsequence } from './solution';

describe('1143. Longest Common Subsequence', () => {
  it('exports longestCommonSubsequence', () => {
    expect(longestCommonSubsequence).toBeInstanceOf(Function);
  });

  it('example 1: subsequence "ace"', () => {
    expect(longestCommonSubsequence('abcde', 'ace')).toBe(3);
  });

  it('example 2: identical strings', () => {
    expect(longestCommonSubsequence('abc', 'abc')).toBe(3);
  });

  it('example 3: no common subsequence', () => {
    expect(longestCommonSubsequence('abc', 'def')).toBe(0);
  });
});
