import { pivotIndex } from './solution';

describe('724. Find Pivot Index', () => {
  it('exports pivotIndex', () => {
    expect(pivotIndex).toBeInstanceOf(Function);
  });

  it('example 1: pivot at index 3', () => {
    expect(pivotIndex([1, 7, 3, 6, 5, 6])).toBe(3);
  });

  it('example 2: no pivot exists', () => {
    expect(pivotIndex([1, 2, 3])).toBe(-1);
  });

  it('example 3: pivot at index 0 with an empty left side', () => {
    expect(pivotIndex([2, 1, -1])).toBe(0);
  });
});
