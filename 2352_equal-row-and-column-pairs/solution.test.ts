import { equalPairs } from './solution';

describe('2352. Equal Row and Column Pairs', () => {
  it('exports equalPairs', () => {
    expect(equalPairs).toBeInstanceOf(Function);
  });

  it('example 1: one matching pair', () => {
    expect(
      equalPairs([
        [3, 2, 1],
        [1, 7, 6],
        [2, 7, 7],
      ]),
    ).toBe(1);
  });

  it('example 2: duplicate rows each match the same column', () => {
    expect(
      equalPairs([
        [3, 1, 2, 2],
        [1, 4, 4, 5],
        [2, 4, 2, 2],
        [2, 4, 2, 2],
      ]),
    ).toBe(3);
  });
});
