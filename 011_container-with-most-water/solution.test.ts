import { maxArea } from './solution';

describe('11. Container With Most Water', () => {
  it('exports maxArea', () => {
    expect(maxArea).toBeInstanceOf(Function);
  });

  it('example 1: widest pair is not the tallest pair', () => {
    expect(maxArea([1, 8, 6, 2, 5, 4, 8, 3, 7])).toBe(49);
  });

  it('example 2: two lines only', () => {
    expect(maxArea([1, 1])).toBe(1);
  });
});
