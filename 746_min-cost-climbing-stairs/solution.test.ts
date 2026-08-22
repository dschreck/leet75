import { minCostClimbingStairs } from './solution';

describe('746. Min Cost Climbing Stairs', () => {
  it('exports minCostClimbingStairs', () => {
    expect(minCostClimbingStairs).toBeInstanceOf(Function);
  });

  it('example 1: start at index 1', () => {
    expect(minCostClimbingStairs([10, 15, 20])).toBe(15);
  });

  it('example 2: skip every expensive step', () => {
    expect(minCostClimbingStairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1])).toBe(6);
  });
});
