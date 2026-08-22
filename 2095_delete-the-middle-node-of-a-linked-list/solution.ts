/**
 * 2095. Delete the Middle Node of a Linked List
 * https://leetcode.com/problems/delete-the-middle-node-of-a-linked-list/
 * Difficulty: Medium
 * Category: Linked List
 *
 * See README.md in this folder for the full problem statement.
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

export function deleteMiddle(head: ListNode | null): ListNode | null {
  throw new Error('Not implemented: deleteMiddle');
}
