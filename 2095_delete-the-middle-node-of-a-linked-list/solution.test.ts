import { deleteMiddle, ListNode } from './solution';

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

describe('2095. Delete the Middle Node of a Linked List', () => {
  it('exports deleteMiddle', () => {
    expect(deleteMiddle).toBeInstanceOf(Function);
  });

  it('example 1: odd length removes index 3', () => {
    expect(toArray(deleteMiddle(buildList([1, 3, 4, 7, 1, 2, 6])))).toEqual([
      1, 3, 4, 1, 2, 6,
    ]);
  });

  it('example 2: even length removes index 2', () => {
    expect(toArray(deleteMiddle(buildList([1, 2, 3, 4])))).toEqual([1, 2, 4]);
  });

  it('example 3: two nodes leave the head', () => {
    expect(toArray(deleteMiddle(buildList([2, 1])))).toEqual([2]);
  });
});
