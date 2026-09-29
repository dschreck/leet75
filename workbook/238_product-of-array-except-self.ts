/**
 * Product of Array Except Self
 * https://leetcode.com/problems/product-of-array-except-self/
 * Topics: Array, Prefix Sum
 * Level: Medium
 *
 * Description:
 * Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].
 *
 * The product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer.
 *
 * You must write an algorithm that runs in O(n) time and without using the division operation.
 */

export function productExceptSelf(nums: number[]): number[] {
  const left: number[] = [];
  const right: number[] = [];
  left[0] = 1;
  right[nums.length - 1] = 1;

  for (let i = 1; i < nums.length; i++) {
    left[i] = nums[i - 1] * left[i - 1];
  }

  for (let i = nums.length - 2; i >= 0; i--) {
    right[i] = nums[i + 1] * right[i + 1];
  }

  const output: number[] = [];
  for (let i = 0; i < nums.length; i++) {
    output[i] = left[i] * right[i] + 0; // +0 fixes IEEE 754 issue where signed int can be -0
  }

  return output;
}
