import { twoSum } from "./array_two_sum";

describe("001. Two Sum", () => {
  it("should return the correct indices", () => {
    const nums = [2, 7, 11, 15];
    const target = 9;
    const expected = [0, 1];

    const actual = twoSum(nums, target);

    expect(actual).toEqual(expected);
  });

  it("should return the correct indices", () => {
    const nums = [3, 2, 4];
    const target = 6;
    const expected = [1, 2];

    const actual = twoSum(nums, target);

    expect(actual).toEqual(expected);
  });

  it("should return the correct indices", () => {
    const nums = [3, 3];
    const target = 6;
    const expected = [0, 1];

    const actual = twoSum(nums, target);

    expect(actual).toEqual(expected);
  });
});
