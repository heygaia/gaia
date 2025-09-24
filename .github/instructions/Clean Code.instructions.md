---
applyTo: "**"
---

Write clean and minimalistic code. Do not create unnecessary test files, markdown files and unnecsesary files. Prioritize writing clean, modular and production level code. Reuse existing logic, paradigms and abstractions if it's there. Do not do anything unnecessary or anything extra. Do not add unnecessary comments, only add comments that are meaningful and cannot be inferred from the code and the specific code needs to be explained to the developer because its not understandable at a glance.
Make changes file by file and allow for review of mistakes.
Make edits in 1 single shot for the file. Do not make multiple edits to the same file.
Only implement changes explicitly requested; do not invent changes.
Provide all edits in a single chunk per file, not in multiple steps.
Encourage modular design for maintainability and reusability.
Adhere to the existing coding style in the project.
Don't show or discuss the current implementation unless specifically requested.
Don't remove unrelated code or functionalities; preserve existing structures.
Only implement changes explicitly requested; do not invent changes.
Never use apologies or give feedback about understanding in comments or documentation.
DRY Principle
Avoid code duplication; reuse code via functions, classes, modules, or libraries.
Modify code in one place if updates are needed.
Function Length & Responsibility
Write short, focused functions (single responsibility principle).
Break up long or complex functions into smaller ones.
Do not manually run the servers or build unnecessary unless told explicitly.
Try to make use of your own tools instead of running terminal commands.
Do not run git commands at ANY case, unless specified explicitly mentioned by the user.
Do not create new files to replace existing files unless told otherwise. Try to only modify the existing files.
Don't run terminal commands if something can be performed with one of the tools that you have access to.
Don't run critical or breaking changes without user approval.
Don't change things and then keep "backwards compatibility" code. If you change something, make sure that the new code is compatible with the existing code and does not break anything.
Never use 'any' types, try to infer the proper types from the context or use the existing types in the codebase.
Never import inside a function unless ABSOLUTELY necessary or when avoiding circular dependencies when there's no other option.
Stop trying to run the backend or frontend servers, or any other servers. You are not allowed to run servers. You can only make code changes. Also, do not open the browser.
Do not add console logs or debugging statements unless explicitly asked to do so.
