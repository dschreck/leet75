/**
 * 328. Odd Even Linked List
 * https://leetcode.com/problems/odd-even-linked-list/
 * Difficulty: Medium
 * Category: Linked List
 */

/**
 * Definition for singly-linked list.
 */
export class ListNode {
  val: number;
  next: ListNode | null;
  constructor(val?: number, next?: ListNode | null) {
    this.val = val === undefined ? 0 : val;
    this.next = next === undefined ? null : next;
  }
}

export function oddEvenList(head: ListNode | null): ListNode | null {
  throw new Error('Not implemented: oddEvenList');
}
