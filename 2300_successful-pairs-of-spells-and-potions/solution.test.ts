import { successfulPairs } from './solution';

describe('2300. Successful Pairs of Spells and Potions', () => {
  it('exports successfulPairs', () => {
    expect(successfulPairs).toBeInstanceOf(Function);
  });

  it('example 1: success = 7', () => {
    expect(successfulPairs([5, 1, 3], [1, 2, 3, 4, 5], 7)).toEqual([4, 0, 3]);
  });

  it('example 2: success = 16 with duplicate potions', () => {
    expect(successfulPairs([3, 1, 2], [8, 5, 8], 16)).toEqual([2, 0, 2]);
  });
});
