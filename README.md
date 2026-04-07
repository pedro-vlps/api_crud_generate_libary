# Versioning Template

A repository created to simplify project versioning and commits generation

*Warning: This script work only on Windows*

## Script usage

You just need to run the script typing its name in PowerShell

> Execute this script in a PowerShell terminal.

```powershell
.\scripts\git_version.ps1
```

## How it works

When you run `.\scripts\git_version.ps1`, the script executes the following steps in order:

1. It sets the console output encoding to UTF-8.
2. It displays commit type options and reads the user selection.
3. It maps the selected option to a commit type label (`initial commit`, `feature`, `bugfix`, `release`, `build`, or `docs`) and exits if the input is invalid.
4. It asks whether to add all files or choose specific files.
5. If the user chooses all files, it runs `git add .`; if the user chooses specific files, it shows the modified files with `git status --short`, reads the file list input, and runs `git add` on the selected files; invalid input causes the script to exit.
6. It prompts for the commit message and creates a commit with `git commit -m "[$tipo] - $mensagem"`.
7. It asks whether to generate a version.
   - If the user answers yes, it asks for a version type: initial version, release (major), feature (minor), or bugfix (patch).
   - It obtains the latest tag from Git using `git describe --tags --abbrev=0`.
   - For an initial version, it sets `0.0.1`; otherwise it parses the latest tag, increments the major, minor, or patch number according to the chosen version type, and constructs a new version string.
   - It creates a tag name prefixed with `v`.
   - It prompts the user to enter changelog notes line by line until an empty line is entered.
   - It updates or creates `CHANGELOG.md` by prepending a new section for the new version and the entered notes.
   - It commits the changelog update, creates the Git tag, and pushes the new tag to the remote origin.
8. Finally, the script pushes the current branch to the remote repository with `git push`.

