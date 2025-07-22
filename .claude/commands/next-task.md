You are a development assistant for the RS Personal Agent project. Your task is to implement the next sequential task from the TASKS.md file following this workflow:

## Workflow Steps:

1. **Read TASKS.md**: Load and analyze the current task file to understand the project progress
2. **Identify Next Task**: Find the next incomplete task in sequential order (e.g., if 1.1 and 1.2 are done, implement 1.3)
3. **Implement Task Group**: Complete all work required for that task group, following the project's UI-first iterative development approach
4. **Quality Verification**: Run the `/verify-quality` command to ensure code quality standards
5. **Mark Complete in TASKS.md**: Update TASKS.md to mark all completed acceptance criteria
   - Identify which task was just implemented (e.g., Task 1.3)
   - Find the "Acceptance Criteria:" section for that task in TASKS.md
   - Replace all `- [ ]` with `- [x]` for criteria that were actually implemented
   - Verify all acceptance criteria in that task section are marked complete
   - Confirm the task section shows all items as `[x]` completed
6. **Final Verification**: Confirm TASKS.md accurately reflects completion
   - Re-read the updated task section in TASKS.md
   - Verify all acceptance criteria show `[x]` 
   - Ensure no `[ ]` items remain for the implemented task
7. **Completion Report**: Provide clear summary of what was accomplished
   - State which task was completed (e.g., "Task 1.3: Basic Database Models and Mock Data")
   - List the specific acceptance criteria that were implemented
   - Confirm TASKS.md has been updated with completion markers

## Important Guidelines:

- Follow the project's iterative UI-first development methodology from CLAUDE.md
- Use proper Python coding standards with type hints and docstrings
- If any task requirements are unclear, ASK the user for clarification - do NOT assume
- Implement complete, working functionality that demonstrates the feature
- Ensure all code follows the PySide6/Qt6 desktop application architecture
- Use the TodoWrite tool to track implementation progress

## TASKS.md Update Requirements:

- **MANDATORY**: Always update TASKS.md after completing implementation
- **Only mark as complete** acceptance criteria that were actually implemented
- **Double-check updates** by re-reading the modified section in TASKS.md
- **Handle edge cases**: If some criteria cannot be completed, document why in the completion report
- **Error recovery**: If TASKS.md update fails, attempt manual correction before finishing

## Implementation Approach:

For each task group, follow this pattern:
1. **UI First**: Create the visible interface elements with mock data
2. **Framework Second**: Add underlying framework code to support the UI
3. **Integration Last**: Connect to real services when the foundation is solid

Start by reading TASKS.md and identifying what needs to be implemented next.