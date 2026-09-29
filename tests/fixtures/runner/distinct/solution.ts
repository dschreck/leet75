export function distinct(nums: number[]): number[] {
  return [...new Set(nums)].sort((a, b) => b - a);
}
