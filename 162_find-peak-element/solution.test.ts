import { findPeakElement } from './solution';

describe('162. Find Peak Element', () => {
  it('exports findPeakElement', () => {
    expect(findPeakElement).toBeInstanceOf(Function);
  });

  it('example 1: single peak at index 2', () => {
    expect(findPeakElement([1, 2, 3, 1])).toBe(2);
  });

  it('example 2: either peak index is accepted', () => {
    expect([1, 5]).toContain(findPeakElement([1, 2, 1, 3, 5, 6, 4]));
  });
});
