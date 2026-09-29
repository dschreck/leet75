class ListNode {
  val: number;
  next: ListNode | null;
  constructor(val?: number, next?: ListNode | null) {
    this.val = val ?? 0;
    this.next = next ?? null;
  }
}

export function reverseList(head: ListNode | null): ListNode | null {
  let previous: ListNode | null = null;
  while (head !== null) {
    const next: ListNode | null = head.next;
    head.next = previous;
    previous = head;
    head = next;
  }
  return previous;
}
