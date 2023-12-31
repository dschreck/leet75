/**
 * Reverse Vowels of a String
 * https://leetcode.com/problems/reverse-vowels-of-a-string/
 * Topics: Two Pointers, String
 * Level: Easy
 *
 * Description:
 * Given a string s, reverse only all the vowels in the string and return it.
 *
 * The vowels are 'a', 'e', 'i', 'o', and 'u', and they can appear in both lower and upper cases, more than once.
 */

  /**
   *
   * Set left pointer to start at 0
   * Set right pointer to start at length - 1
   *
   * Keep iterating until the left pointer catch up to the right pointer
   *
   * keep incrementing the left pointer start until it's pointing at a vowel
   * keep decrementing the right pointer end until it's pointing to a vowel
   * swap the characters
   * increment start and decremnt end
   */

export function reverseVowels(s: string): string {
  const output = [...s];
  const isVowel = (char: string) =>
    ['a', 'e', 'i', 'o', 'u'].includes(char.toLocaleLowerCase());
  const swap = (leftIdx: number, rightIdx: number) => {
    const tmp = output[leftIdx];
    output[leftIdx] = output[rightIdx];
    output[rightIdx] = tmp;
  };
  
  let left = 0;
  let right = s.length - 1;

  while (left < right) {
    while (left < s.length && !isVowel(output[left])) {
      left++;
    }
    while (right >= 0 && !isVowel(output[right])) {
      right--;
    }

    if (left < right) {
      swap(left++, right--);
    }
  }
  
  return output.join('');
}
