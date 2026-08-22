import { ListNode, oddEvenList } from './solution';

function buildList(values: number[]): ListNode | null {
  let head: ListNode | null = null;
  for (let i = values.length - 1; i >= 0; i--)
    head = new ListNode(values[i], head);
  return head;
}

function toArray(head: ListNode | null): number[] {
  const out: number[] = [];
  for (let node = head; node !== null; node = node.next) out.push(node.val);
  return out;
}

describe('328. Odd Even Linked List', () => {
  it('exports oddEvenList', () => {
    expect(oddEvenList).toBeInstanceOf(Function);
  });

  it('example 1: five nodes', () => {
    expect(toArray(oddEvenList(buildList([1, 2, 3, 4, 5])))).toEqual([
      1, 3, 5, 2, 4,
    ]);
  });

  it('example 2: seven nodes', () => {
    expect(toArray(oddEvenList(buildList([2, 1, 3, 5, 6, 4, 7])))).toEqual([
      2, 3, 6, 7, 1, 5, 4,
    ]);
  });
});
