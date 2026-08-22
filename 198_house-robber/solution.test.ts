import { rob } from './solution';

describe('198. House Robber', () => {
  it('exports rob', () => {
    expect(rob).toBeInstanceOf(Function);
  });

  it('example 1: rob houses 1 and 3', () => {
    expect(rob([1, 2, 3, 1])).toBe(4);
  });

  it('example 2: rob houses 1, 3 and 5', () => {
    expect(rob([2, 7, 9, 3, 1])).toBe(12);
  });
});
