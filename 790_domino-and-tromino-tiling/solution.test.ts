import { numTilings } from './solution';

describe('790. Domino and Tromino Tiling', () => {
  it('exports numTilings', () => {
    expect(numTilings).toBeInstanceOf(Function);
  });

  it('example 1: n = 3', () => {
    expect(numTilings(3)).toBe(5);
  });

  it('example 2: n = 1', () => {
    expect(numTilings(1)).toBe(1);
  });
});
