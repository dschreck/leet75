/**
 * Maximum Average Subarray I
 * https://leetcode.com/problems/maximum-average-subarray-i
 * Topic: Array, Sliding Window
 * Level: Easy
 *
 * Description:
 *
 * You are given an integer array nums consisting of n elements, and an integer k.
 *
 * Find a contiguous subarray whose length is equal to k that has the maximum average value and return this value. Any answer with a calculation error less than 10-5 will be accepted.
 *
 * Example 1:
 * Input: nums = [1,12,-5,-6,50,3], k = 4
 * Output: 12.75000
 * Explanation: Maximum average is (12 - 5 - 6 + 50) / 4 = 51 / 4 = 12.75
 *
 * Example 2:
 * Input: nums = [5], k = 1
 * Output: 5.00000
 *
 */

export function findMaxAverage(nums: number[], k: number): number {
  // get the first window
  let sum = nums.slice(0, k).reduce((a, b) => a + b, 0);
  let maxSum = sum;

  // slide the window an update the max sum
  for (let i = k; i < nums.length; i++) {
    // this slides the last added number value off of the sum total, and adds the next number in the array
    sum = sum - nums[i - k] + nums[i];
    maxSum = Math.max(maxSum, sum);
  }

  // average the max sum
  return maxSum / k;
}
