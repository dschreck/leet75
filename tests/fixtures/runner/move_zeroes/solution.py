class Solution:
    def moveZeroes(self, nums: list[int]) -> None:
        write = 0
        for value in nums:
            if value != 0:
                nums[write] = value
                write += 1
        nums[write:] = [0] * (len(nums) - write)
