import { findMaxAverage } from './max_avg_subarray';

describe('643. Maximum Avg Subarray', () => {
  it('should return the maximum average subarray', () => {
    expect(findMaxAverage([1, 12, -5, -6, 50, 3], 4)).toBe(12.75);
    expect(findMaxAverage([0, 1, 1, 3, 3], 4)).toBe(2);
    expect(findMaxAverage([5], 1)).toBe(5);
    expect(findMaxAverage([5], 1)).toBe(5);
  });
});
