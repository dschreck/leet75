import { findDifference } from './solution';

describe('2215. Find the Difference of Two Arrays', () => {
  it('exports findDifference', () => {
    expect(findDifference).toBeInstanceOf(Function);
  });

  it('example 1: each array has two exclusive values', () => {
    expect(findDifference([1, 2, 3], [2, 4, 6])).toEqual([
      [1, 3],
      [4, 6],
    ]);
  });

  it('example 2: duplicates are reported once', () => {
    expect(findDifference([1, 2, 3, 3], [1, 1, 2, 2])).toEqual([[3], []]);
  });
});
