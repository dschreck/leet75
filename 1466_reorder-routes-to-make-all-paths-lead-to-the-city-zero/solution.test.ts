import { minReorder } from './solution';

describe('1466. Reorder Routes to Make All Paths Lead to the City Zero', () => {
  it('exports minReorder', () => {
    expect(minReorder).toBeInstanceOf(Function);
  });

  it('example 1: three edges must be flipped', () => {
    expect(
      minReorder(6, [
        [0, 1],
        [1, 3],
        [2, 3],
        [4, 0],
        [4, 5],
      ]),
    ).toBe(3);
  });

  it('example 2: two edges must be flipped', () => {
    expect(
      minReorder(5, [
        [1, 0],
        [1, 2],
        [3, 2],
        [3, 4],
      ]),
    ).toBe(2);
  });

  it('example 3: all edges already point at the capital', () => {
    expect(
      minReorder(3, [
        [1, 0],
        [2, 0],
      ]),
    ).toBe(0);
  });
});
