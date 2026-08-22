import { orangesRotting } from './solution';

describe('994. Rotting Oranges', () => {
  it('exports orangesRotting', () => {
    expect(orangesRotting).toBeInstanceOf(Function);
  });

  it('example 1: all oranges rot in 4 minutes', () => {
    expect(
      orangesRotting([
        [2, 1, 1],
        [1, 1, 0],
        [0, 1, 1],
      ]),
    ).toBe(4);
  });

  it('example 2: one orange is unreachable', () => {
    expect(
      orangesRotting([
        [2, 1, 1],
        [0, 1, 1],
        [1, 0, 1],
      ]),
    ).toBe(-1);
  });

  it('example 3: no fresh oranges to begin with', () => {
    expect(orangesRotting([[0, 2]])).toBe(0);
  });
});
