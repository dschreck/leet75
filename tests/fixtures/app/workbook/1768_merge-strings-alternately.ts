export function mergeAlternately(word1: string, word2: string): string {
  let merged = "";
  for (let i = 0; i < Math.max(word1.length, word2.length); i++) {
    merged += (word1[i] ?? "") + (word2[i] ?? "");
  }
  return merged;
}
