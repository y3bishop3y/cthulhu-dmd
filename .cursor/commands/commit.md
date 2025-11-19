# Commit Workflow

**Purpose:** Ensure all code is tested, linted, and verified before committing.

---

## Pre-Commit Checklist

### Step 1: Stage Changes
```bash
git add <specific-files>
```
- Stage only the files you want to commit
- Review what's being committed with `git status`
- **NEVER use `git add .` or `git add -A` without explicit permission**

### Step 2: Run Linting
```bash
uv run ruff check scripts/
```

**Requirements:**
- ✅ **Fix all Ruff (linting) errors**
- ❌ **DO NOT skip errors**
- If errors are too complex → **STOP and ask user** before proceeding

### Step 3: Run Type Checking
```bash
uv run mypy scripts/
```

**Requirements:**
- ✅ **Fix all MyPy (type checking) errors**
- ❌ **DO NOT skip errors**
- If errors are too complex → **STOP and ask user** before proceeding

### Step 4: Format Code
```bash
uv run ruff format scripts/
```

**Requirements:**
- ✅ **Format all changed files**
- ✅ **Re-stage formatted files if needed**

---

## Commit Creation

### Step 5: Create Commit Message

Craft a clear commit message that describes:
- **What was fixed/added/changed**
- **Why the change was made** (if fixing a bug/problem)
- **Key changes made**

**Message Format:**
```
feat/fix/refactor: Brief description

- Detailed change 1
- Detailed change 2
- Fixed issue X (if applicable)
```

### Step 6: Commit

```bash
git commit -m "Your commit message here"
```

**CRITICAL RULES:**
- ✅ **ONLY commit when user explicitly requests it**
- ❌ **NEVER commit without explicit permission**
- ❌ **NEVER use `--no-verify`** (bypasses hooks)

---

## Error Handling

### If Linting/Type Errors:
1. **Fix Ruff/MyPy errors**
2. **Re-run checks**
3. **If errors are too complex:** Inform user and ask for guidance
4. **DO NOT skip errors** unless user explicitly requests it

---

## Summary: Commit Workflow

```
1. git add <specific-files>    → Stage only what you need
2. uv run ruff check           → Fix errors or STOP
3. uv run mypy                 → Fix errors or STOP
4. uv run ruff format          → Format code
5. Write commit message
6. git commit -m "..."         → ONLY if user explicitly requests
```

---

## Principles

- ✅ **Lint and type-check everything** before committing
- ✅ **Fix all errors** before committing
- ✅ **Only commit when explicitly requested**
- ❌ **Never skip** error fixes without user approval
- ❌ **Never commit** without explicit user permission
- 🛑 **Stop and ask** if unable to fix something

---

**End of Commit Workflow**
