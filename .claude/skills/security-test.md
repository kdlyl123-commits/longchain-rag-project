---
name: security-test
description: Audit the codebase for security vulnerabilities including hardcoded secrets, injection flaws, XSS, missing auth, and configuration weaknesses.
---

When invoked, perform a comprehensive security audit of the entire project:

## 1. Secrets & Credentials
Search for:
- API keys, tokens, passwords in source code (grep for `sk-`, `password`, `secret`, `token`, `api_key`)
- JWT secret strength
- Database credentials in config files
- Default passwords in docker-compose, README, docs
- Real credentials in .env files (verify .gitignore coverage)
- Check if `.env` files are accidentally tracked by git

## 2. Code Vulnerabilities
Check backend Python files for:
- SQL injection (string formatting in queries)
- Command injection (shell commands with user input)
- Path traversal (user input in file paths)
- Missing input validation on API endpoints
- Missing authentication/authorization on routes
- Unsafe deserialization (eval, exec, pickle)
- Error messages leaking internal details

## 3. Frontend & Config
Check frontend and config for:
- XSS vulnerabilities (dangerouslySetInnerHTML, innerHTML)
- CORS misconfiguration
- JWT expiration, algorithm strength
- Docker containers running as root
- Exposed ports to 0.0.0.0
- Nginx security headers
- npm dependency vulnerabilities

## Report
Present findings ranked by severity (CRITICAL > HIGH > MEDIUM > LOW). For each finding, include:
- Exact file path and line
- What the issue is
- Why it's a problem
- Specific fix recommendation
