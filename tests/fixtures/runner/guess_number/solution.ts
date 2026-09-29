declare function guess(num: number): number;

export function guessNumber(n: number): number {
  let low = 1;
  let high = n;
  for (;;) {
    const middle = Math.floor((low + high) / 2);
    const answer = guess(middle);
    if (answer === 0) return middle;
    if (answer < 0) high = middle - 1;
    else low = middle + 1;
  }
}
