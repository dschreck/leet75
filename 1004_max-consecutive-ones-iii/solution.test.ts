import { longestOnes } from './solution';

describe('1004. Max Consecutive Ones III', () => {
  it('exports longestOnes', () => {
    expect(longestOnes).toBeInstanceOf(Function);
  });

  it('example 1: k = 2', () => {
    expect(longestOnes([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2)).toBe(6);
  });

  it('example 2: k = 3', () => {
    expect(
      longestOnes([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3),
    ).toBe(10);
  });
});
