import { minEatingSpeed } from './solution';

describe('875. Koko Eating Bananas', () => {
  it('exports minEatingSpeed', () => {
    expect(minEatingSpeed).toBeInstanceOf(Function);
  });

  it('example 1: h = 8 leaves slack', () => {
    expect(minEatingSpeed([3, 6, 7, 11], 8)).toBe(4);
  });

  it('example 2: h equals the pile count', () => {
    expect(minEatingSpeed([30, 11, 23, 4, 20], 5)).toBe(30);
  });

  it('example 3: one extra hour lowers the speed', () => {
    expect(minEatingSpeed([30, 11, 23, 4, 20], 6)).toBe(23);
  });
});
