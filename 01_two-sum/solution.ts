export function twoSum(nums: number[], target: number): number[] {
  // nums = [2, 7, 11, 15]
  // target = 9
  // output = [0,1]

  for (let i = 0; i < nums.length; i++) {
    for (let y = i + 1; y < nums.length; y++) {
      const testValue = nums[i] + nums[y];
      if (testValue === target) {
        return [i, y];
      }
    }
  }

  return [-1, -1];
}
