import { maxScore } from './solution';

describe('2542. Maximum Subsequence Score', () => {
  it('exports maxScore', () => {
    expect(maxScore).toBeInstanceOf(Function);
  });

  it('example 1: k = 3', () => {
    expect(maxScore([1, 3, 3, 2], [2, 1, 3, 4], 3)).toBe(12);
  });

  it('example 2: k = 1 picks the best single product', () => {
    expect(maxScore([4, 2, 3, 1, 1], [7, 5, 10, 9, 6], 1)).toBe(30);
  });
});
