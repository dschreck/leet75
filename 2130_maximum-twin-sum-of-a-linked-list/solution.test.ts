import { ListNode, pairSum } from './solution';

function buildList(values: number[]): ListNode | null {
  let head: ListNode | null = null;
  for (let i = values.length - 1; i >= 0; i--)
    head = new ListNode(values[i], head);
  return head;
}

describe('2130. Maximum Twin Sum of a Linked List', () => {
  it('exports pairSum', () => {
    expect(pairSum).toBeInstanceOf(Function);
  });

  it('example 1: every twin pair sums to 6', () => {
    expect(pairSum(buildList([5, 4, 2, 1]))).toBe(6);
  });

  it('example 2: largest twin sum is 7', () => {
    expect(pairSum(buildList([4, 2, 2, 3]))).toBe(7);
  });

  it('example 3: single twin pair', () => {
    expect(pairSum(buildList([1, 100000]))).toBe(100001);
  });
});
