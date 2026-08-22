import { maxProfit } from './solution';

describe('714. Best Time to Buy and Sell Stock with Transaction Fee', () => {
  it('exports maxProfit', () => {
    expect(maxProfit).toBeInstanceOf(Function);
  });

  it('example 1: two round trips, fee = 2', () => {
    expect(maxProfit([1, 3, 2, 8, 4, 9], 2)).toBe(8);
  });

  it('example 2: fee = 3', () => {
    expect(maxProfit([1, 3, 7, 5, 10, 3], 3)).toBe(6);
  });
});
