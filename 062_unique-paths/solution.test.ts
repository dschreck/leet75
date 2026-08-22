import { uniquePaths } from './solution';

describe('62. Unique Paths', () => {
  it('exports uniquePaths', () => {
    expect(uniquePaths).toBeInstanceOf(Function);
  });

  it('example 1: 3 x 7 grid', () => {
    expect(uniquePaths(3, 7)).toBe(28);
  });

  it('example 2: 3 x 2 grid', () => {
    expect(uniquePaths(3, 2)).toBe(3);
  });
});
