import { combinationSum3 } from './solution';

describe('216. Combination Sum III', () => {
  it('exports combinationSum3', () => {
    expect(combinationSum3).toBeInstanceOf(Function);
  });

  it('example 1: one combination sums to 7', () => {
    expect(combinationSum3(3, 7)).toEqual([[1, 2, 4]]);
  });

  it('example 2: three combinations sum to 9', () => {
    expect(combinationSum3(3, 9)).toEqual([
      [1, 2, 6],
      [1, 3, 5],
      [2, 3, 4],
    ]);
  });

  it('example 3: target below the minimum possible sum', () => {
    expect(combinationSum3(4, 1)).toEqual([]);
  });
});
