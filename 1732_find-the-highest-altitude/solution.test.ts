import { largestAltitude } from './solution';

describe('1732. Find the Highest Altitude', () => {
  it('exports largestAltitude', () => {
    expect(largestAltitude).toBeInstanceOf(Function);
  });

  it('example 1: peak altitude is 1', () => {
    expect(largestAltitude([-5, 1, 5, 0, -7])).toBe(1);
  });

  it('example 2: never climbs above the start', () => {
    expect(largestAltitude([-4, -3, -2, -1, 4, 3, 2])).toBe(0);
  });
});
