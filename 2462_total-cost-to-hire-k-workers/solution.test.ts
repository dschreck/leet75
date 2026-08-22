import { totalCost } from './solution';

describe('2462. Total Cost to Hire K Workers', () => {
  it('exports totalCost', () => {
    expect(totalCost).toBeInstanceOf(Function);
  });

  it('example 1: k = 3, candidates = 4', () => {
    expect(totalCost([17, 12, 10, 2, 7, 2, 11, 20, 8], 3, 4)).toBe(11);
  });

  it('example 2: candidate windows overlap', () => {
    expect(totalCost([1, 2, 4, 1], 3, 3)).toBe(4);
  });
});
