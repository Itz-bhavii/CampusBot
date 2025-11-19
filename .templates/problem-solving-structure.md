# Problem-Solving Structure Template
## The Ruthless Mentor Approach

**Last Updated:** 2025-11-14  
**Purpose:** Step-by-step problem decomposition for learning by doing

---

## Structure

### 1. **THE PROBLEM (Brutal Diagnosis)**

**The Problem:**
[Clear, direct statement of what's broken/wrong/stupid]

[Detailed technical explanation of WHY it's wrong]

---

### 2. **YOUR TASK (Solve This First)**

**Goal:** [One clear, actionable objective]

**Think through these questions:**

1. **[Core Question 1]**  
   - Hint: [Guiding questions to force thinking]
   - Constraint: [What to consider]

2. **[Core Question 2]**  
   - Hint: [More specific guidance]
   - Alternative: [Different approach to consider]

3. **[Core Question 3]**  
   - Trade-off: [What are the implications?]
   - Context: [Where does this fit in the larger system?]

4. **[Implementation Detail Question]**  
   - Hint: [Technical detail to research]

5. **[Edge Case/Design Question]**  
   - Consideration: [What could go wrong?]

---

### 3. **WHAT TO CODE**

Go to `[file/location]` around lines [X-Y] where you [current behavior]. Redesign/refactor to [expected outcome].

**Don't just copy-paste.** Think about:
- [Design consideration 1]
- [Design consideration 2]
- [Design consideration 3]

---

### 4. **VALIDATION**

When you've thought through these questions and attempted a solution:
1. Show your approach (pseudocode or actual code)
2. Explain your reasoning for key decisions
3. Identify what you're uncertain about

Then get feedback before moving to the next problem.

---

## Example Application

### MISTAKE #1: Garbage Metadata

**The Problem:**
Your metadata is useless. Right now, when ChromaDB retrieves a chunk, you have **no way** to tell the user:
- Which PDF it came from
- What page it was on
- Where in the document it appeared

This makes your RAG system **uncitable** — users can't verify answers, and you can't debug retrieval quality.

---

**Your Task (Solve This First):**

**Goal:** Add complete source tracking to every chunk's metadata before it goes into ChromaDB.

**Think through these questions:**

1. **Where does `unstructured` store page numbers?**  
   - Hint: Look at the `page` object's `.metadata` attribute. What fields does it have?

2. **How do you get the original filename?**  
   - You have `fileNameWithPath` as a parameter. Should you store the full path or just the filename? Why?

3. **What's a good unique document ID?**  
   - Should you use the filename? What if someone uploads two files with the same name?  
   - Should you hash the file content? Generate a UUID when the file is first uploaded?  
   - Where would that ID come from?

4. **How do you track chunk order within a document?**  
   - If you split one page into 3 chunks, how do you number them sequentially?  
   - Should the index reset per-page or be global across the entire document?

5. **What about element type?**  
   - `unstructured` gives you `Title`, `NarrativeText`, `Table`, `ListItem`. Should you store this? Why/why not?

---

**What to Code:**

Go to `parser.py` around lines 48-63 where you build `metadataToAdd`. Redesign that dictionary to include **all the missing fields**.

**Don't just copy-paste.** Think about:
- What data is already available to you?
- What data needs to come from upstream (Spring/RabbitMQ message)?
- How to structure it so retrieval results are **useful**?

---

## Tips for Using This Template

1. **One problem at a time**: Don't try to solve everything at once
2. **Force precision**: If your answer to any question is vague, you haven't thought hard enough
3. **Research first**: Use docs, inspect objects, test assumptions before coding
4. **No shortcuts**: The questions are designed to make you understand the *why*, not just the *how*
5. **Validate reasoning**: Explaining your approach reveals gaps in understanding

---

## Anti-Patterns to Avoid

❌ **Jumping straight to code** without thinking through the questions  
❌ **Asking for the answer** instead of attempting first  
❌ **Implementing without understanding** the underlying problem  
❌ **Skipping edge cases** because "it works for now"  
❌ **Not considering system integration** (where does data come from/go to?)

---

## Progressive Difficulty

As you solve more problems, the structure adapts:
- **Beginner:** More hints, explicit guidance
- **Intermediate:** Broader questions, multiple valid approaches
- **Advanced:** Architectural trade-offs, performance considerations, production readiness

The goal: Make you **think like a senior developer**, not just write code.
