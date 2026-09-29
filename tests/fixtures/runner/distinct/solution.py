class Solution:
    def distinct(self, nums: list[int]) -> list[int]:
        return sorted(set(nums), reverse=True)
