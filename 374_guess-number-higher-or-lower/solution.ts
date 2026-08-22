/**
 * 374. Guess Number Higher or Lower
 * https://leetcode.com/problems/guess-number-higher-or-lower/
 * Difficulty: Easy
 * Category: Binary Search
 *
 * See README.md in this folder for the full problem statement.
 */

/**
 * The guess API is provided by LeetCode:
 *   -1 -> the picked number is lower than num
 *    1 -> the picked number is higher than num
 *    0 -> num is the picked number
 * Locally the picked number is supplied by setPick().
 */
let pick: number | null = null;

export function setPick(num: number): void {
  pick = num;
}

export function guess(num: number): number {
  if (pick === null) throw new Error('No number picked: call setPick() first');
  if (num > pick) return -1;
  if (num < pick) return 1;
  return 0;
}

export function guessNumber(n: number): number {
  throw new Error('Not implemented: guessNumber');
}
