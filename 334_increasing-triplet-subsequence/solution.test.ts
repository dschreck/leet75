import { increasingTriplet } from './solution';

describe('334. Increasing Triplet Subsequence', () => {
  it('exports increasingTriplet', () => {
    expect(increasingTriplet).toBeInstanceOf(Function);
  });

  it('example 1: strictly increasing array', () => {
    expect(increasingTriplet([1, 2, 3, 4, 5])).toBe(true);
  });

  it('example 2: strictly decreasing array', () => {
    expect(increasingTriplet([5, 4, 3, 2, 1])).toBe(false);
  });

  it('example 3: non-adjacent triplet', () => {
    expect(increasingTriplet([2, 1, 5, 0, 4, 6])).toBe(true);
  });
});
