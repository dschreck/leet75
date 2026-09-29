class Solution:
    def guessNumber(self, n: int) -> int:
        low, high = 1, n
        while True:
            middle = (low + high) // 2
            answer = guess(middle)  # noqa: F821 - the harness provides LeetCode's guess API
            if answer == 0:
                return middle
            if answer < 0:
                high = middle - 1
            else:
                low = middle + 1
