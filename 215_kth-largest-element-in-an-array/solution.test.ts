import { findKthLargest } from './solution';

describe('215. Kth Largest Element in an Array', () => {
  it('exports findKthLargest', () => {
    expect(findKthLargest).toBeInstanceOf(Function);
  });

  it('example 1: 2nd largest', () => {
    expect(findKthLargest([3, 2, 1, 5, 6, 4], 2)).toBe(5);
  });

  it('example 2: 4th largest counts duplicates', () => {
    expect(findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4)).toBe(4);
  });
});
