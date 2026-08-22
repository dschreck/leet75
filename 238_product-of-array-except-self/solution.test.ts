import { productExceptSelf } from './solution';

describe('238_product-of-array-self', () => {
  test('productExceptSelf', () => {
    expect(productExceptSelf([1, 2, 3, 4])).toEqual([24, 12, 8, 6]);
    expect(productExceptSelf([-1, 1, 0, -3, 3])).toEqual([0, 0, 9, 0, 0]);
  });
});
