/**
 * 1768. Merge Strings Alternately
 * https://leetcode.com/problems/merge-strings-alternately/
 * Difficulty: Easy
 * Category: Array / String
 */

export function mergeAlternately(word1: string, word2: string): string {
  let output = [];

  let parts1 = word1.split('').reverse();
  let parts2 = word2.split('').reverse();

  while (parts1.length || parts2.length) {
    if (parts1.length) {
      output.push(parts1.pop());
    }
    if (parts2.length) {
      output.push(parts2.pop());
    }
  }

  return output.join('');
}
