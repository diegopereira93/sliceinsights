# 🤖 Guide to Autonomous Development

Welcome to the **Autonomous Development Protocol** for `sliceinsights`. This project interacts with a swarm of specialized AI agents. This guide explains how to operate them effectively to maximize productivity and minimize human friction.

---

## ⚡ Quick Start: The "IssueOps" Workflow

The most efficient way to work is **Asynchronous IssueOps**. Don't wait for the chat.

1.  **Define**: Create an Issue using the `Feature Request` or `Task` template.
2.  **Branch**: ALWAYS create a new branch from `main` (e.g., `feat/`, `fix/`, `chore/`). **Never work directly on `main`.**
3.  **Trigger**: Tag the relevant agent in the issue or PR (mentions like `@project-planner`).
4.  **Review**: The agents will pick up the context, create a plan, code it, and open a PR against `main`.
5.  **Merge**: You review the final PR (guided by the checklist) and merge.

---

## 👥 Agent Roster

Know your team. Calling the right specialist saves tokens and time.

### 🧠 Planning & Management
| Agent | Handle | Role | When to use |
|-------|--------|------|-------------|
| **Project Planner** | `@project-planner` | Architect | New projects, big refactors, roadmap planning. |
| **Product Manager** | `@product-manager` | Vision | Clarifying requirements, defining user stories. |
| **Orchestrator** | `@orchestrator` | Manager | Coordination of multiple agents (default for complex asks). |

### 🛠️ Engineering Specialists
| Agent | Handle | Role | When to use |
|-------|--------|------|-------------|
| **Frontend Specialist** | `@frontend-specialist` | UI/UX | React, Tailwind, Components, Responsiveness. |
| **Backend Specialist** | `@backend-specialist` | API/DB | Python, FastAPI, Postgres, Logic. |
| **Mobile Developer** | `@mobile-developer` | iOS/Android | React Native, Mobile specific logic. |
| **Database Architect** | `@database-architect` | Data | Schema design, SQL optimization, Migrations. |

### 🛡️ Quality & Operations
| Agent | Handle | Role | When to use |
|-------|--------|------|-------------|
| **DevOps Engineer** | `@devops-engineer` | Infra | CI/CD, Docker, Deployment, Scripts. |
| **Test Engineer** | `@test-engineer` | Tests | Writing E2E tests, Unit tests strategies. |
| **Security Auditor** | `@security-auditor` | Security | Vulnerability scans, Auth reviews. |
| **Debugger** | `@debugger` | Fixes | Investigating errors, logs, and weird behaviors. |

---

## 🗣️ Trigger Protocols (Magic Words)

Agents listen for specific intent patterns. Use these keywords in your prompts or issue descriptions to ensure the right agent wakes up.

| Intent | Keywords | Activated Agent |
|--------|----------|-----------------|
| **Plan a Feature** | "plan", "roadmap", "breakdown" | `project-planner` |
| **Design UI** | "design", "mockup", "component", "css" | `frontend-specialist` |
| **Fix a Bug** | "debug", "error", "fail", "log" | `debugger` |
| **Optimize Speed** | "slow", "performance", "latency" | `performance-optimizer` |
| **Test Code** | "test", "coverage", "e2e" | `test-engineer` |
| **Deploy** | "deploy", "release", "prod" | `devops-engineer` |
| **Audit Security** | "scan", "vulnerability", "hack" | `security-auditor` |

---

## 🔄 The Autonomous Cycle

1.  **Initialization**: User runs `/[command]` or states clear intent.
2.  **Branching (MANDATORY)**: Create a feature branch `git checkout -b type/description`.
3.  **Orchestration**: If complex, `orchestrator` breaks it down.
3.  **Execution**: Agents work in parallel where possible.
    *   *Frontend* builds UI.
    *   *Backend* builds API.
    *   *Testers* write verification.
4.  **Verification**:
    *   **MANDATORY**: Agents MUST run `scripts/verify.sh` locally to ensure linting, security, and tests pass.
    *   *CI/CD*: GitHub Actions (`ci.yml`) acts as the final gatekeeper on PRs.
5.  **Completion**: `walkthrough.md` is updated with proof of verification.

---

---

## 🌳 Git Workflow Guidelines

To maintain production stability, all contributors (human and agent) must follow these rules:

*   **Main is Protected**: Direct pushes to `main` are restricted to deployment finalization.
*   **Branch Naming**: 
    *   `feat/feature-name` for new work.
    *   `fix/bug-name` for bug fixes.
    *   `docs/doc-updates` for documentation.
*   **PR Requirement**: All code must enter `main` via a Pull Request with at least one passing CI run.

---

> **Pro Tip**: To force a specific agent, strictly start your prompt with `Act as @[Agent Name]`.
