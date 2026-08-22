import { eraseOverlapIntervals } from './solution';

describe('435. Non-overlapping Intervals', () => {
  it('exports eraseOverlapIntervals', () => {
    expect(eraseOverlapIntervals).toBeInstanceOf(Function);
  });

  it('example 1: remove one interval', () => {
    expect(
      eraseOverlapIntervals([
        [1, 2],
        [2, 3],
        [3, 4],
        [1, 3],
      ]),
    ).toBe(1);
  });

  it('example 2: identical intervals', () => {
    expect(
      eraseOverlapIntervals([
        [1, 2],
        [1, 2],
        [1, 2],
      ]),
    ).toBe(2);
  });

  it('example 3: touching endpoints do not overlap', () => {
    expect(
      eraseOverlapIntervals([
        [1, 2],
        [2, 3],
      ]),
    ).toBe(0);
  });
});
