/**
 * Can Place Flowers
 * https://leetcode.com/problems/can-place-flowers/
 * Topics: Array
 * Level: Easy
 *
 * Description:
 * You have a long flowerbed in which some of the plots are planted, and some are not. However, flowers cannot be planted in adjacent plots.
 *
 * Given an integer array flowerbed containing 0's and 1's, where 0 means empty and 1 means not empty, and an integer n, return true if n
 * new flowers can be planted in the flowerbed without violating the no-adjacent-flowers rule and false otherwise.
 */

export function canPlaceFlowers(flowerbed: number[], n: number): boolean {
  for (let i = 0; i < flowerbed.length && n > 0; i++) {
    if (flowerbed[i] === 1) {
      continue;
    }
    const behind = flowerbed[i - 1] || 0;
    const ahead = flowerbed[i + 1] || 0;
    if (behind !== 1 && ahead !== 1) {
      flowerbed[i] = 1;
      n--;
    }
  }
  return n === 0;
}
