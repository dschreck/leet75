import { kidsWithCandies } from "./greatest_candies";

describe("1431. Kids With the Greatest Number of Candies", () => {
  test("Example test case 1", () => {
    expect(kidsWithCandies([2, 3, 5, 1, 3], 3)).toEqual([true, true, true, false, true]);
  });

  test("Example test case 2", () => {
    expect(kidsWithCandies([4, 2, 1, 1, 2], 1)).toEqual([true, false, false, false, false]);
  });

  test("Example test case 3", () => {
    expect(kidsWithCandies([12, 1, 12], 10)).toEqual([true, false, true]);
  });
});