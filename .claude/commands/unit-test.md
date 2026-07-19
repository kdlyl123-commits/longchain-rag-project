---
description: Run all unit tests for the RAG project (backend pytest + frontend TypeScript check)
---

Run the complete unit test suite for this project:

1. Backend pytest:
```bash
cd "D:/longchain rag project/backend"
python -m pytest tests/ -v --tb=short
```

2. Frontend type check:
```bash
cd "D:/longchain rag project/frontend"
npx tsc --noEmit
```

Report the results clearly: total passed/failed for backend, and any TypeScript errors for frontend.
If all pass, confirm "All tests passed, project is healthy."
If any fail, show the failures and suggest fixes.
