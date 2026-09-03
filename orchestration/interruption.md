# Mid-Generation Interruption Handling

This file defines how to handle new user instructions while generation tasks are running.

---

## 1. Scenario

Omni-IO supports parallel tasks, some of which, such as video and 3D generation, may take tens of seconds. During that time, the user may:

- Change a dispatched task: "That music is too sad; make it more upbeat."
- Add a task: "Also generate a portrait version."
- Cancel a task: "I don't need the video."
- Switch topics completely: "Let's do something else—a cyberpunk style."

These are all **interruptions**. Claude should respond to the new intent as efficiently as possible without affecting completed tasks.

---

## 2. General Principles

1. **Preserve completed results:** Assets already written to the asset registry remain intact.
2. **Prioritize semantic impact over status:** Not every running task must be cancelled; determine which tasks the new instruction actually affects.
3. **Minimize duplicate generation:** Continue any running task compatible with the new instruction, and reuse completed assets whenever possible.
4. **Confirmation is cheaper than incorrect execution:** If the impact of an interruption is unclear, ask the user before acting.

---

## 3. Interruption Types and Rules

### Type 1: Local Change to One Task

The user modifies the requirements of one specific task.

**Condition:** The instruction clearly identifies a task, such as "that music" or "this image," and affects only that task.

**Process:**

```
1. Identify target task T.
2. Check T's status:
   a. Not started → modify T's prompt/params and execute normally.
   b. Running → cancel the current API call and restart T with the new parameters.
   c. Completed → regenerate with the new parameters and update the registry after completion.
3. Check downstream tasks:
   - If T's result feeds a downstream task that has not started, keep it waiting for T's new result.
   - If the downstream task is already complete, explain that it used the old version and ask whether to regenerate it.
```

### Type 2: Global Change to Scene or Style

The user changes a core scene or style that affects every task in the turn.

**Condition:** The instruction changes the overall atmosphere, scene, or style, such as "make it nighttime" or "change everything to cyberpunk."

**Process:**

```
1. Identify a global change.
2. For every running task:
   a. Cancel the current API call.
   b. Rewrite a complete prompt for that task with the new scene/style.
   c. Restart it.
3. For completed tasks, ask whether the user wants to regenerate them.
   Do not regenerate by default, to avoid waste.
```

### Type 3: Add a Task

The user adds another generation task while existing tasks are running.

**Condition:** The instruction requests an additional asset, such as "also make a landscape version" or "add a sound effect."

**Process:**

```
1. Update the internal execution graph with the new task, continuing the ID sequence: img2, sfx2, etc.
2. Insert the task into the existing DAG.
3. If it depends on a running task, wait; if independent, start it immediately in parallel.
4. Completed results remain unaffected.
```

### Type 4: Cancel a Task

The user explicitly cancels one or all tasks.

**Process:**

```
1. Identify target task T, or all tasks.
2. If T is running, send a cancellation signal and stop its API call.
   If the API cannot cancel, ignore the eventual result.
3. If T has not started, remove it from the execution queue.
4. Mark T's downstream tasks cancelled.
5. Do not write cancelled tasks to the registry.
6. Confirm the cancellation to the user.
```

### Type 5: Switch Topics

The user abandons the current task set and switches to an unrelated subject.

**Process:**

```
1. Identify a topic switch: the new instruction is unrelated to every current task.
2. Ask whether to cancel all running tasks.
3. After confirmation:
   a. Cancel every running task.
   b. Clear the current turn's DAG.
   c. Keep completed assets in the registry for possible later use.
4. Start over with the new topic and construct a new execution graph.
```

---

## 4. Semantic Relevance Check

After an interruption, assess every running task for semantic relevance:

```
For each task T, determine:
  Does the new instruction affect T's result?

  → Affected; T's prompt or params must change:
      T running → cancel and restart.
      T not started → modify, then start.

  → Unaffected; T is unrelated to the change:
      Continue without intervention.

  → Uncertain:
      Default conservatively to continuing, or ask the user.
```

Use these signals:

- Does the new instruction explicitly mention the task? "That music" affects only the music task.
- Is it a global style or scene change? This affects every task.
- Does it only add a task? Existing tasks are unaffected.

---

## 5. User-Experience Principles

- **Immediate feedback:** Acknowledge the interruption immediately instead of waiting for all task states to update.
- **Transparency:** Clearly state which tasks were cancelled, restarted, or left running.
- **Minimal disruption:** Do not cancel every task because of one local change.
- **Completed results remain useful:** Even when later tasks are cancelled, completed assets such as images can still be shown.

---

## 6. Relationship to `declare_protocol`

Interruption handling is **dynamic replanning**. Claude incrementally modifies the existing DAG—cancelling, adding, or changing nodes—instead of discarding it wholesale.

It therefore relies on the DAG structure defined in `declare_protocol.md` and follows the same topological scheduling logic. The only difference is that the DAG changes dynamically during execution.
