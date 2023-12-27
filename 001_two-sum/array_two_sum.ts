/**
 * Two Sum
 * https://leetcode.com/problems/two-sum/
 * Topic: Array, Hash Table
 * Level: Easy
 * 
 * Description:
 * 
 * Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
 * 
 * You may assume that each input would have exactly one solution, and you may not use the same element twice.
 * 
 * You can return the answer in any order.
 */


/**
 * 
 * @param nums 
 * @param target 
 * @returns 
 */
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
