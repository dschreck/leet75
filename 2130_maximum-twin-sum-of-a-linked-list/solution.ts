/**
 * 2130. Maximum Twin Sum of a Linked List
 * https://leetcode.com/problems/maximum-twin-sum-of-a-linked-list/
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

export function pairSum(head: ListNode | null): number {
  throw new Error('Not implemented: pairSum');
}
