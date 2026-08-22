import { isSubsequence } from './solution';

describe('392. Is Subsequence', () => {
  it('exports isSubsequence', () => {
    expect(isSubsequence).toBeInstanceOf(Function);
  });

  it('example 1: "abc" is a subsequence of "ahbgdc"', () => {
    expect(isSubsequence('abc', 'ahbgdc')).toBe(true);
  });

  it('example 2: "axc" is not a subsequence of "ahbgdc"', () => {
    expect(isSubsequence('axc', 'ahbgdc')).toBe(false);
  });
});
