import { maxOperations } from './solution';

describe('1679. Max Number of K-Sum Pairs', () => {
  it('exports maxOperations', () => {
    expect(maxOperations).toBeInstanceOf(Function);
  });

  it('example 1: two pairs sum to 5', () => {
    expect(maxOperations([1, 2, 3, 4], 5)).toBe(2);
  });

  it('example 2: one pair sums to 6', () => {
    expect(maxOperations([3, 1, 3, 4, 3], 6)).toBe(1);
  });
});
