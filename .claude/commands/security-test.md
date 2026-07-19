---
description: Run a comprehensive security audit across the entire codebase
---

Perform a full security audit of the project covering:

1. **Secrets & Credentials** - API keys, passwords, tokens, JWT secrets in source code and config files
2. **Code Vulnerabilities** - SQL injection, command injection, path traversal, XSS, missing auth
3. **Configuration Weaknesses** - Docker, CORS, JWT, Nginx, exposed ports

Report all findings ranked by severity (CRITICAL/HIGH/MEDIUM/LOW) with exact file paths, line numbers, and specific fix recommendations.
