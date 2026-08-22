import { minFlips } from './solution';

describe('1318. Minimum Flips to Make a OR b Equal to c', () => {
  it('exports minFlips', () => {
    expect(minFlips).toBeInstanceOf(Function);
  });

  it('example 1: a = 2, b = 6, c = 5', () => {
    expect(minFlips(2, 6, 5)).toBe(3);
  });

  it('example 2: a = 4, b = 2, c = 7', () => {
    expect(minFlips(4, 2, 7)).toBe(1);
  });

  it('example 3: already satisfied', () => {
    expect(minFlips(1, 2, 3)).toBe(0);
  });
});
