# Claude Code Custom Commands

This document describes the custom slash commands available in Claude Code for the RS Personal Agent project.

## Available Commands

### `/execute-prompt`

**Purpose**: Executes instructions from a `prompt.md` file in the project root.

**Description**: This command reads the CLAUDE.md file to understand project context and guidelines, then reads and executes the contents of prompt.md as a direct prompt. This is useful for running predefined tasks or workflows.

**Usage**:
```
/execute-prompt
```

**Example**:
If you have a `prompt.md` file with instructions to update documentation or run specific tasks, simply run:
```
/execute-prompt
```

The command will:
1. Read CLAUDE.md for project context
2. Read prompt.md for instructions
3. Execute all instructions in prompt.md following project guidelines

---

### `/worktree-start <feature-name>`

**Purpose**: Creates a new git worktree for feature development.

**Description**: This command sets up a new git worktree in a separate directory, allowing you to work on multiple features simultaneously without switching branches in your main repository.

**Usage**:
```
/worktree-start feature-name
```

**Example**:
```
/worktree-start add-calendar-agent
```

This will:
- Create a new worktree at `../rs_pa_worktrees/add-calendar-agent`
- Create a new branch called `add-calendar-agent`
- Check out the new branch in the worktree

**Benefits**:
- Work on multiple features simultaneously
- Keep your main repository clean
- No need to stash changes when switching features

---

### `/worktree-merge <feature-name>`

**Purpose**: Merges a feature branch from a worktree into the current branch.

**Description**: Use this command to merge a completed feature from a worktree branch into your current branch (typically main or develop).

**Usage**:
```
/worktree-merge feature-name
```

**Example**:
```
/worktree-merge add-calendar-agent
```

This will:
- Merge the `add-calendar-agent` branch into your current branch
- Notify you of any merge conflicts if they occur
- Provide guidance on resolving conflicts if needed

**Follow-up**: After successful merge, use `/worktree-finish` to clean up.

---

### `/worktree-finish <feature-name>`

**Purpose**: Cleans up a feature worktree after merging.

**Description**: This command removes the worktree directory and deletes the feature branch after you've successfully merged your changes.

**Usage**:
```
/worktree-finish feature-name
```

**Example**:
```
/worktree-finish add-calendar-agent
```

This will:
- Remove the worktree directory at `../rs_pa_worktrees/add-calendar-agent`
- Delete the `add-calendar-agent` branch
- Confirm successful cleanup

**Note**: The branch deletion will fail if it hasn't been merged. Use the `-D` flag to force delete if you're certain you want to remove an unmerged branch.

## Workflow Example

Here's a typical workflow using these commands:

1. **Start a new feature**:
   ```
   /worktree-start implement-task-scheduler
   ```

2. **Work on the feature** in the new worktree directory:
   ```
   cd ../rs_pa_worktrees/implement-task-scheduler
   # Make your changes, commit them
   ```

3. **Merge the feature** when complete:
   ```
   # Return to main repository
   cd ../rs_pa
   /worktree-merge implement-task-scheduler
   ```

4. **Clean up** after successful merge:
   ```
   /worktree-finish implement-task-scheduler
   ```

## Creating Custom Commands

To create your own custom Claude commands:

1. Create a markdown file in `.claude/commands/` with your command name
2. Write the command instructions in natural language
3. Use `$ARGUMENTS` placeholder for parameters
4. Organize in subdirectories for namespacing (e.g., `.claude/commands/test/unit.md` → `/test:unit`)

Example custom command file (`.claude/commands/run-tests.md`):
```markdown
Run the test suite for the RS Personal Agent project.

Execute the following command:
\```bash
pytest tests/ -v --cov=rs_pa --cov-report=html
\```

After running, inform the user:
- How many tests passed/failed
- The code coverage percentage
- That the HTML coverage report is available at htmlcov/index.html
```

This would be available as `/run-tests` in Claude Code.