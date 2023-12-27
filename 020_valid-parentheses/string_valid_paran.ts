/**
 * Valid Parentheses
 * https://leetcode.com/problems/valid-parentheses/
 * Topic: String, Stack
 * Level: Easy
 *
 * Description:
 *
 * Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.
 *
 * An input string is valid if:
 *
 * 1. Open brackets must be closed by the same type of brackets.
 * 2. Open brackets must be closed in the correct order.
 * 3. Every close bracket must have an open bracket of the same type.
 */

/**
 *
 * @param s
 */
export function isValid(s: string): boolean {
  // Hint says to use a stack, so let's do that
  const stack = [];

  // Loop through the string
  for (let i = 0; i < s.length; i++) {
    const char = s[i];

    // If the char is an open bracket, push it to the stack
    if (char === '(' || char === '{' || char === '[') {
      stack.push(char);
    } else {
      // If the stack is empty, then we have a close bracket without an open bracket
      if (stack.length === 0) {
        return false;
      }

      // Get the last open bracket from the stack
      const lastOpenBracket = stack.pop();

      // If the last open bracket doesn't match the current close bracket, then return false
      if (
        (lastOpenBracket === '(' && char !== ')') ||
        (lastOpenBracket === '{' && char !== '}') ||
        (lastOpenBracket === '[' && char !== ']')
      ) {
        return false;
      }
    }
  }
  
  return true;
}
