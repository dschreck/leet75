import { countBits } from './solution';

describe('338. Counting Bits', () => {
  it('exports countBits', () => {
    expect(countBits).toBeInstanceOf(Function);
  });

  it('example 1: n = 2', () => {
    expect(countBits(2)).toEqual([0, 1, 1]);
  });

  it('example 2: n = 5', () => {
    expect(countBits(5)).toEqual([0, 1, 1, 2, 1, 2]);
  });
});
