# CodingAgents

**CodingAgents** is a LangGraph-based multi-agent coding system that helps transform software requirements into a working application.

The system uses specialized agents for planning, design, implementation, visual QA, and code review. Each agent can use its own model and API configuration, allowing different LLM providers or models to be used for different stages of the development workflow.

## Overview

The development workflow is divided into several specialized agents:

```text
Requirements
     │
     ▼
┌─────────────┐
│ Planner     │
│ Agent       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Design      │
│ Agent       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Coding      │
│ Agent       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Visual QA   │
│ Agent       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Reviewer    │
│ Agent       │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Frontier Review  │
│ Agent            │
└──────────────────┘
       │
       ▼
   Application
```

## Agents

### Planner Agent

The **Planner Agent** converts high-level requirements into a structured development plan.

It is responsible for:

* Understanding the requirements
* Breaking requirements into actionable tasks
* Identifying technical considerations
* Creating an implementation plan for downstream agents

### Design Agent

The **Design Agent** focuses on application and UI/UX design.

It is responsible for:

* Translating requirements into a design
* Defining application structure and user flows
* Providing design guidance to the Coding Agent
* Helping ensure the implementation matches the intended experience

### Coding Agent

The **Coding Agent** implements the application based on the requirements, plan, and design.

It is responsible for:

* Writing application code
* Creating and modifying project files
* Implementing features
* Fixing implementation issues
* Iterating based on QA and review feedback

### Visual QA Agent

The **Visual QA Agent** validates the application's visual output and user interface.

It is responsible for:

* Checking UI implementation against the expected design
* Identifying visual inconsistencies
* Detecting layout and styling issues
* Providing feedback for further implementation changes

### Reviewer Agent

The **Reviewer Agent** performs code and implementation reviews.

It is responsible for:

* Reviewing generated code
* Identifying bugs and potential issues
* Checking code quality and maintainability
* Validating that requirements have been implemented correctly
* Providing actionable feedback to the Coding Agent

A fallback model can be configured for the Reviewer Agent.

### Frontier Review Agent

The **Frontier Review Agent** provides an additional high-capability review stage for the generated application.

It can be used for:

* Final implementation review
* Deeper reasoning about potential issues
* Identifying architectural or implementation problems
* Providing an additional quality gate before completion

---

# Environment Variables

Each agent can be configured independently using environment variables.

Create a `.env` file in the project root and configure the required values.

> **Important:** Never commit API keys or other secrets to source control. Add `.env` to `.gitignore`.

## Planner Agent

| Variable                 | Description                                            |
| ------------------------ | ------------------------------------------------------ |
| `PLANNER_MODEL`          | Model/provider configuration used by the Planner Agent |
| `PLANNER_MODEL_NAME`     | Name of the model used for planning                    |
| `PLANNER_MODEL_BASE_URL` | Base URL of the model API                              |
| `PLANNER_MODEL_API_KEY`  | API key for the model provider                         |

```env
PLANNER_MODEL=""
PLANNER_MODEL_NAME=""
PLANNER_MODEL_BASE_URL=""
PLANNER_MODEL_API_KEY=""
```

## Design Agent

| Variable                | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| `DESIGN_MODEL`          | Model/provider configuration used by the Design Agent |
| `DESIGN_MODEL_BASE_URL` | Base URL of the model API                             |
| `DESIGN_MODEL_API_KEY`  | API key for the model provider                        |

```env
DESIGN_MODEL=""
DESIGN_MODEL_BASE_URL=""
DESIGN_MODEL_API_KEY=""
```

## Coding Agent

| Variable               | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| `CODER_MODEL`          | Model/provider configuration used by the Coding Agent |
| `CODER_MODEL_BASE_URL` | Base URL of the model API                             |
| `CODER_MODEL_API_KEY`  | API key for the model provider                        |

```env
CODER_MODEL=""
CODER_MODEL_BASE_URL=""
CODER_MODEL_API_KEY=""
```

## QA Agent

| Variable                   | Description                                              |
| -------------------------- | -------------------------------------------------------- |
| `VISUAL_QA_MODEL`          | Model/provider configuration used by the Visual QA Agent |
| `VISUAL_QA_MODEL_BASE_URL` | Base URL of the model API                                |
| `VISUAL_QA_MODEL_API_KEY`  | API key for the model provider                           |

```env
VISUAL_QA_MODEL=""
VISUAL_QA_MODEL_BASE_URL=""
VISUAL_QA_MODEL_API_KEY=""
```

## Reviewer Agent

The Reviewer Agent supports both a primary model and a fallback model.

### Primary Reviewer

```env
REVIEW_MODEL=""
REVIEW_MODEL_BASE_URL=""
REVIEW_MODEL_API_KEY=""
```

### Fallback Reviewer

```env
REVIEW_FALLBACK_MODEL=""
REVIEW_FALLBACK_MODEL_BASE_URL=""
REVIEW_FALLBACK_MODEL_API_KEY=""
```

| Variable                         | Description                           |
| -------------------------------- | ------------------------------------- |
| `REVIEW_MODEL`                   | Primary model/provider configuration  |
| `REVIEW_MODEL_BASE_URL`          | Base URL of the primary model API     |
| `REVIEW_MODEL_API_KEY`           | API key for the primary model         |
| `REVIEW_FALLBACK_MODEL`          | Fallback model/provider configuration |
| `REVIEW_FALLBACK_MODEL_BASE_URL` | Base URL of the fallback model API    |
| `REVIEW_FALLBACK_MODEL_API_KEY`  | API key for the fallback model        |

## Frontier Review Agent

```env
REVIEW_FRONTIER_MODEL=""
REVIEW_FRONTIER_BASE_URL=""
REVIEW_FRONTIER_API_KEY=""
```

| Variable                   | Description                                                    |
| -------------------------- | -------------------------------------------------------------- |
| `REVIEW_FRONTIER_MODEL`    | Model/provider configuration used by the Frontier Review Agent |
| `REVIEW_FRONTIER_BASE_URL` | Base URL of the model API                                      |
| `REVIEW_FRONTIER_API_KEY`  | API key for the model provider                                 |

---

# Complete `.env` Example

The following example shows all supported environment variables:

```env
WORKSPACE_PATH= "{base_path}/GeneratedApps"

# Planner Agent
PLANNER_MODEL=""
PLANNER_MODEL_NAME=""
PLANNER_MODEL_BASE_URL=""
PLANNER_MODEL_API_KEY=""

# Design Agent
DESIGN_MODEL=""
DESIGN_MODEL_BASE_URL=""
DESIGN_MODEL_API_KEY=""

# Coding Agent
CODER_MODEL=""
CODER_MODEL_BASE_URL=""
CODER_MODEL_API_KEY=""

# Visual QA Agent
VISUAL_QA_MODEL=""
VISUAL_QA_MODEL_BASE_URL=""
VISUAL_QA_MODEL_API_KEY=""

# Reviewer Agent
REVIEW_MODEL=""
REVIEW_MODEL_BASE_URL=""
REVIEW_MODEL_API_KEY=""

# Reviewer fallback
REVIEW_FALLBACK_MODEL=""
REVIEW_FALLBACK_MODEL_BASE_URL=""
REVIEW_FALLBACK_MODEL_API_KEY=""

# Frontier Review Agent
REVIEW_FRONTIER_MODEL=""
REVIEW_FRONTIER_BASE_URL=""
REVIEW_FRONTIER_API_KEY=""
```

# Development Workflow

At a high level, CodingAgents follows this workflow:

1. **Requirements** — The user provides the desired application or feature requirements.
2. **Planning** — The Planner Agent analyzes the requirements and creates an implementation plan.
3. **Design** — The Design Agent defines the application and UI/UX design.
4. **Implementation** — The Coding Agent builds the application based on the plan and design.
5. **Visual QA** — The Visual QA Agent evaluates the resulting UI and identifies visual issues.
6. **Review** — The Reviewer Agent reviews the implementation and provides feedback.
7. **Frontier Review** — The Frontier Review Agent performs an additional high-quality review.
8. **Iteration** — Feedback can be passed back to the Coding Agent for further implementation and fixes.
9. **Completion** — The process continues until the application meets the required quality and functionality.


# Project Status

CodingAgents is under active development.

Features, agent capabilities, configuration options, and workflow behavior may change as the project evolves.
