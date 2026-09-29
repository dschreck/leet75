// Child-process harness that runs a TypeScript solution against a job's test cases.
//
// The runner starts it as `node [flags] harness.mjs RUN_DIR`. It imports RUN_DIR/solution.mts
// (so Node strips the types), reads RUN_DIR/job.json and appends one JSON record per line to
// RUN_DIR/results.jsonl, using the same protocol as harness.py:
//
//   {"type": "case", "index": 0, "actual": ..., "error": null, "stdout": "...", "ms": 0.012}
//   {"type": "fatal", "error": "..."}   the solution could not be loaded; nothing follows
//   {"type": "done"}                    every case ran
//
// Each record is written synchronously before the next case starts, so a kill loses at most the
// case in progress. console.* and process.stdout/stderr.write go to a capped buffer per case
// (output printed while the solution loads counts toward the first case); raw writes to fd 1/2
// only reach the runner's capped pipe. Neither can touch the results file.
import { Console } from 'node:console';
import { openSync, readFileSync, writeSync } from 'node:fs';
import { join, sep } from 'node:path';
import { performance } from 'node:perf_hooks';
import { pathToFileURL } from 'node:url';
import { inspect } from 'node:util';

const SOURCE_FILE = 'solution.mts';
const SOURCE_NAME = 'solution.ts';
const JOB_FILE = 'job.json';
const RESULTS_FILE = 'results.jsonl';
const CASE_OUTPUT_CAP = 8 * 1024;
const TOTAL_OUTPUT_CAP = 64 * 1024;
const ERROR_TEXT_CAP = 4 * 1024;
const ACTUAL_JSON_CAP = 256 * 1024;
const OP_NOTE_CAP = 200;
const TRACEBACK_FRAMES = 5;
const TRUNCATED_MARKER = '[truncated]';

// Taken before the solution loads, so a solution that patches globals cannot break reporting.
const stringify = JSON.stringify;
const now = performance.now.bind(performance);
const exitProcess = process.exit.bind(process);

class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

// Keeps CASE_OUTPUT_CAP characters per case and TOTAL_OUTPUT_CAP per run.
class OutputCapture {
  #parts = [];
  #caseSize = 0;
  #totalSize = 0;
  #truncated = false;

  write(text) {
    const room = Math.min(
      CASE_OUTPUT_CAP - this.#caseSize,
      TOTAL_OUTPUT_CAP - this.#totalSize,
    );
    const kept = text.slice(0, Math.max(room, 0));
    this.#parts.push(kept);
    this.#caseSize += kept.length;
    this.#totalSize += kept.length;
    this.#truncated ||= kept.length < text.length;
  }

  // Returns the output captured since the last call and starts a new case.
  take() {
    let text = this.#parts.join('');
    if (this.#truncated) {
      text += (text && !text.endsWith('\n') ? '\n' : '') + TRUNCATED_MARKER;
    }
    this.#parts = [];
    this.#caseSize = 0;
    this.#truncated = false;
    return text;
  }
}

class Clock {
  ms = 0;

  call(fn) {
    const started = now();
    try {
      return fn();
    } finally {
      this.ms += now() - started;
    }
  }
}

// A design op that raised; `message` says which op, `cause` is what the solution threw.
class OpError extends Error {}

const runDir = process.argv[2];
const runDirPrefixes = [`${pathToFileURL(runDir).href}/`, `${runDir}${sep}`];
const solutionPath = join(runDir, SOURCE_FILE);
const solutionUrl = pathToFileURL(solutionPath).href;
const job = JSON.parse(readFileSync(join(runDir, JOB_FILE), 'utf8'));
const resultsFd = openSync(join(runDir, RESULTS_FILE), 'a');
const capture = new OutputCapture();

function installCapture() {
  const toText = chunk =>
    typeof chunk === 'string' ? chunk : Buffer.from(chunk).toString();
  const sink = { write: chunk => (capture.write(toText(chunk)), true) };
  globalThis.console = new Console({
    stdout: sink,
    stderr: sink,
    ignoreErrors: false,
    colorMode: false,
  });
  process.stdout.write = sink.write;
  process.stderr.write = sink.write;
  process.exit = code => {
    throw new Error(`process.exit(${code ?? ''}) is not allowed in a solution`);
  };
}

function writeRecord(record) {
  const data = Buffer.from(`${stringify(record)}\n`);
  for (let offset = 0; offset < data.length;) {
    offset += writeSync(resultsFd, data, offset);
  }
}

function capText(text, limit) {
  return text.length <= limit
    ? text
    : `${text.slice(0, limit)}\n${TRUNCATED_MARKER}`;
}

// Shows paths relative to the run dir, and the solution under the name the user knows.
function withoutRunDir(text) {
  const relative = runDirPrefixes.reduce(
    (result, prefix) => result.replaceAll(prefix, ''),
    text,
  );
  return relative.replaceAll(SOURCE_FILE, SOURCE_NAME);
}

// Error name and message plus the innermost stack frames that belong to the solution.
function describeError(error) {
  if (error instanceof OpError) {
    return capText(
      `${describeError(error.cause)}\n${error.message}`,
      ERROR_TEXT_CAP,
    );
  }
  if (!(error instanceof Error)) {
    return capText(`Uncaught ${inspect(error)}`, ERROR_TEXT_CAP);
  }
  const stack =
    typeof error.stack === 'string' && error.stack
      ? error.stack
      : String(error);
  const kept = [];
  let frames = 0;
  for (const line of stack.split('\n')) {
    const isFrame = /^\s+at /.test(line);
    if (isFrame && (!line.includes(solutionPath) || frames >= TRACEBACK_FRAMES))
      continue;
    frames += isFrame ? 1 : 0;
    kept.push(withoutRunDir(line));
  }
  return capText(kept.join('\n').trimEnd(), ERROR_TEXT_CAP);
}

async function loadSolution() {
  try {
    const target = (await import(solutionUrl))[job.entry];
    if (typeof target === 'function') return { target };
    const what = job.kind === 'design' ? 'class' : 'function';
    return { error: `${SOURCE_NAME} must export ${what} ${job.entry}` };
  } catch (error) {
    return { error: describeError(error) };
  }
}

function buildList(values) {
  let head = null;
  for (let i = values.length - 1; i >= 0; i -= 1)
    head = new ListNode(values[i], head);
  return head;
}

// Builds a tree from LeetCode's level-order array, where null marks a missing child.
function buildTree(values) {
  const nodes = values.map(value =>
    value === null ? null : new TreeNode(value),
  );
  if (nodes.length === 0 || nodes[0] === null) return null;
  const children = nodes.slice(1).values();
  const queue = [nodes[0]];
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    node.left = children.next().value ?? null;
    node.right = children.next().value ?? null;
    for (const child of [node.left, node.right])
      if (child !== null) queue.push(child);
  }
  return nodes[0];
}

function findTreeNode(root, val) {
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node === null) continue;
    if (node.val === val) return node;
    stack.push(node.left, node.right);
  }
  throw new Error(`TreeNodeRef ${stringify(val)} is not a value in the tree`);
}

const NODE_BUILDERS = new Map([
  ['ListNode', buildList],
  ['TreeNode', buildTree],
]);

// Turns JSON arguments into the objects the solution expects (nodes, node references).
function convertArgs(values, types) {
  const args = values.map((value, i) => {
    const build = NODE_BUILDERS.get(types[i]);
    return build === undefined ? value : build(value);
  });
  const root = args[types.indexOf('TreeNode')] ?? null;
  return args.map((arg, i) =>
    types[i] === 'TreeNodeRef' && arg !== null ? findTreeNode(root, arg) : arg,
  );
}

const isListNode = value =>
  typeof value === 'object' &&
  value !== null &&
  'val' in value &&
  'next' in value;
const isTreeNode = value =>
  typeof value === 'object' &&
  value !== null &&
  'val' in value &&
  'left' in value &&
  'right' in value;

function nonFiniteName(value) {
  if (Number.isNaN(value)) return 'NaN';
  return value > 0 ? 'Infinity' : '-Infinity';
}

// Converts a return value to JSON-safe data: typed arrays and Sets become arrays, Maps objects.
function plainJson(value, seen = new Set()) {
  if (value === null || value === undefined) return null;
  switch (typeof value) {
    case 'number':
      return Number.isFinite(value) ? value : nonFiniteName(value);
    case 'bigint':
      return Number(value);
    case 'string':
    case 'boolean':
      return value;
    case 'function':
      return `[Function ${value.name || 'anonymous'}]`;
    case 'symbol':
      return value.toString();
  }
  if (seen.has(value))
    throw new TypeError('cannot serialize a value that contains itself');
  seen.add(value);
  try {
    if (
      Array.isArray(value) ||
      ArrayBuffer.isView(value) ||
      value instanceof Set
    ) {
      return Array.from(value, item => plainJson(item, seen));
    }
    const entries =
      value instanceof Map ? Array.from(value) : Object.entries(value);
    return Object.fromEntries(
      entries.map(([key, item]) => [String(key), plainJson(item, seen)]),
    );
  } finally {
    seen.delete(value);
  }
}

function listValues(head) {
  const values = [];
  const seen = new Set();
  for (
    let node = head ?? null;
    node !== null && node !== undefined;
    node = node.next
  ) {
    if (seen.has(node)) throw new Error('the linked list contains a cycle');
    seen.add(node);
    values.push(plainJson(node.val));
  }
  return values;
}

// Serializes a tree to LeetCode's level-order array without trailing nulls.
function treeValues(root) {
  const values = [];
  const seen = new Set();
  const queue = [root ?? null];
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head] ?? null;
    if (node === null) {
      values.push(null);
      continue;
    }
    if (seen.has(node))
      throw new Error('the tree contains a cycle or a shared node');
    seen.add(node);
    values.push(plainJson(node.val));
    queue.push(node.left, node.right);
  }
  while (values.length > 0 && values[values.length - 1] === null) values.pop();
  return values;
}

// Serializes `value` according to its declared meta.toml type.
function toJson(value, type) {
  if (type === 'void') return null;
  if (type === 'ListNode' && (value == null || isListNode(value)))
    return listValues(value);
  if (type === 'TreeNode' && (value == null || isTreeNode(value)))
    return treeValues(value);
  if (type === 'TreeNodeRef' && isTreeNode(value)) return plainJson(value.val);
  return plainJson(value);
}

// LeetCode 374's guess API bound to one case's picked number.
function makeGuess(pick) {
  return num => (num > pick ? -1 : num < pick ? 1 : 0);
}

function serializeOutput(args, result) {
  if (job.output === 'arg0') return toJson(args[0], job.params[0]);
  if (job.output === 'arg0-prefix') {
    if (!Number.isInteger(result)) {
      throw new TypeError(
        `expected the new length (an integer) as the return value, got ${inspect(result)}`,
      );
    }
    return toJson(args[0].slice(0, result), job.params[0]);
  }
  return toJson(result, job.returns);
}

function runFunction(target, testCase, clock) {
  const args = convertArgs(testCase.args, job.params);
  if (job.kind === 'interactive') globalThis.guess = makeGuess(testCase.pick);
  return serializeOutput(
    args,
    clock.call(() => target(...args)),
  );
}

// Constructs the class with ops[0]'s args, then calls each later op on the instance.
function runDesign(Target, testCase, clock) {
  const { ops, args } = testCase;
  const instance = clock.call(() => new Target(...args[0]));
  const outputs = [null];
  for (let position = 1; position < ops.length; position += 1) {
    try {
      const method = instance[ops[position]];
      if (typeof method !== 'function')
        throw new TypeError(`${job.entry}.${ops[position]} is not a function`);
      outputs.push(
        plainJson(clock.call(() => method.apply(instance, args[position]))),
      );
    } catch (error) {
      const call = `${ops[position]}(${stringify(args[position]).slice(1, -1)})`;
      throw new OpError(`in ops[${position}]: ${call.slice(0, OP_NOTE_CAP)}`, {
        cause: error,
      });
    }
  }
  return outputs;
}

function checkedSize(actual) {
  const size = (stringify(actual) ?? '').length;
  if (size > ACTUAL_JSON_CAP)
    throw new RangeError(
      `result too large to report: ${size} characters of JSON`,
    );
  return actual;
}

function runCase(target, index) {
  const runner = job.kind === 'design' ? runDesign : runFunction;
  const clock = new Clock();
  let actual = null;
  let error = null;
  try {
    actual = checkedSize(runner(target, job.cases[index], clock));
  } catch (thrown) {
    error = describeError(thrown);
  }
  const ms = Math.round(clock.ms * 1000) / 1000;
  return { type: 'case', index, actual, error, stdout: capture.take(), ms };
}

installCapture();
const loaded = await loadSolution();
if (loaded.error !== undefined) {
  writeRecord({ type: 'fatal', error: loaded.error });
} else {
  for (let index = 0; index < job.cases.length; index += 1)
    writeRecord(runCase(loaded.target, index));
  writeRecord({ type: 'done' });
}
exitProcess(0); // do not wait for timers the solution may have left pending
