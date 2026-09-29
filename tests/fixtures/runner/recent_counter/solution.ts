export class RecentCounter {
  private calls: number[] = [];

  ping(t: number): number {
    this.calls.push(t);
    while (this.calls[0] < t - 3000) this.calls.shift();
    return this.calls.length;
  }
}
