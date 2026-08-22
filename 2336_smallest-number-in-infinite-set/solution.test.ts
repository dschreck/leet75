import { SmallestInfiniteSet } from './solution';

describe('2336. Smallest Number in Infinite Set', () => {
  it('exports SmallestInfiniteSet', () => {
    expect(SmallestInfiniteSet).toBeInstanceOf(Function);
  });

  it('example 1: the documented call sequence', () => {
    const set = new SmallestInfiniteSet();
    set.addBack(2);
    expect(set.popSmallest()).toBe(1);
    expect(set.popSmallest()).toBe(2);
    expect(set.popSmallest()).toBe(3);
    set.addBack(1);
    expect(set.popSmallest()).toBe(1);
    expect(set.popSmallest()).toBe(4);
    expect(set.popSmallest()).toBe(5);
  });
});
