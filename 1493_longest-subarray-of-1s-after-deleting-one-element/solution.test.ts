import { longestSubarray } from './solution';

describe('1493. Longest Subarray of 1s After Deleting One Element', () => {
  it('exports longestSubarray', () => {
    expect(longestSubarray).toBeInstanceOf(Function);
  });

  it('example 1: delete the single zero', () => {
    expect(longestSubarray([1, 1, 0, 1])).toBe(3);
  });

  it('example 2: delete the zero joining two runs', () => {
    expect(longestSubarray([0, 1, 1, 1, 0, 1, 1, 0, 1])).toBe(5);
  });

  it('example 3: all ones still costs one deletion', () => {
    expect(longestSubarray([1, 1, 1])).toBe(2);
  });
});
