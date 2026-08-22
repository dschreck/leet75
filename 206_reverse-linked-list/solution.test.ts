import { ListNode, reverseList } from './solution';

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

describe('206. Reverse Linked List', () => {
  it('exports reverseList', () => {
    expect(reverseList).toBeInstanceOf(Function);
  });

  it('example 1: five nodes', () => {
    expect(toArray(reverseList(buildList([1, 2, 3, 4, 5])))).toEqual([
      5, 4, 3, 2, 1,
    ]);
  });

  it('example 2: two nodes', () => {
    expect(toArray(reverseList(buildList([1, 2])))).toEqual([2, 1]);
  });

  it('example 3: empty list', () => {
    expect(reverseList(buildList([]))).toBeNull();
  });
});
