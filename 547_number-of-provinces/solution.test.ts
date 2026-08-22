import { findCircleNum } from './solution';

describe('547. Number of Provinces', () => {
  it('exports findCircleNum', () => {
    expect(findCircleNum).toBeInstanceOf(Function);
  });

  it('example 1: two provinces', () => {
    expect(
      findCircleNum([
        [1, 1, 0],
        [1, 1, 0],
        [0, 0, 1],
      ]),
    ).toBe(2);
  });

  it('example 2: no city is connected', () => {
    expect(
      findCircleNum([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
      ]),
    ).toBe(3);
  });
});
