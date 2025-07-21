Merge a feature branch from a worktree into the current branch.

This command will merge the specified feature branch into the current branch.

Execute the following git command:
```bash
git merge $ARGUMENTS
```

After running the command:
- If the merge is successful, inform the user that the branch `$ARGUMENTS` has been merged
- If there are merge conflicts, inform the user and provide guidance on resolving them
- Remind the user they can use `/worktree-finish $ARGUMENTS` to clean up the worktree after merging