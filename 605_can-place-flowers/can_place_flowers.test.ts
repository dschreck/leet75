import { canPlaceFlowers } from './can_place_flowers';

describe('605 Can Place Flowers', () => {
  test('Examples', () => {
    expect(canPlaceFlowers([1, 0, 0, 0, 1], 1)).toBe(true);
    expect(canPlaceFlowers([1, 0, 0, 0, 1], 2)).toBe(false);
    expect(canPlaceFlowers([1, 0, 0, 0, 0, 1], 2)).toBe(false);
    expect(canPlaceFlowers([0, 0, 1, 0, 0], 1)).toBe(true);
  });
});
