---
name: unit-test
description: Run all unit tests for the RAG project covering auth, chat, RAG modules, and frontend TypeScript.
---

When invoked, run the backend test suite and frontend type check:

## Backend Tests

```bash
cd "D:/longchain rag project/backend"
python -m pytest tests/ -v --tb=short
```

## Frontend Type Check

```bash
cd "D:/longchain rag project/frontend"
npx tsc --noEmit
```

## Report

After running both, report:
- Total passed / failed for backend
- Any TypeScript errors for frontend
- If all pass, confirm the project is healthy
