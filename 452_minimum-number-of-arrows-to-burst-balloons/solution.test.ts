import { findMinArrowShots } from './solution';

describe('452. Minimum Number of Arrows to Burst Balloons', () => {
  it('exports findMinArrowShots', () => {
    expect(findMinArrowShots).toBeInstanceOf(Function);
  });

  it('example 1: two arrows cover four balloons', () => {
    expect(
      findMinArrowShots([
        [10, 16],
        [2, 8],
        [1, 6],
        [7, 12],
      ]),
    ).toBe(2);
  });

  it('example 2: disjoint balloons need one arrow each', () => {
    expect(
      findMinArrowShots([
        [1, 2],
        [3, 4],
        [5, 6],
        [7, 8],
      ]),
    ).toBe(4);
  });

  it('example 3: touching endpoints count as overlapping', () => {
    expect(
      findMinArrowShots([
        [1, 2],
        [2, 3],
        [3, 4],
        [4, 5],
      ]),
    ).toBe(2);
  });
});
