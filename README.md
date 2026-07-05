# 🌌 GitHub Companion

[![Version](https://img.shields.io/badge/version-v0.1.1-blue.svg)](https://github.com/revanth-kumar-02/Github-Companion)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/revanth-kumar-02/Github-Companion)

> **An AI-powered GitHub & Developer CLI built for modern software engineers.**

GitHub Companion is an intelligent developer CLI that combines GitHub automation, AI coding agents, repository management, project generation, workspace management, and multiple AI providers into a single, high-performance terminal experience. Inspired by modern agentic coding workflows, it remains lightweight, terminal-first, and completely open source.

---

## ✨ Features

### 🐙 GitHub Integration
*   **Profile Dashboard**: Visual profile rendering displaying bios, social statistics, and user locations inside premium panels.
*   **Repository Management**: Seamless repository creation, deletion, renaming, cloning, and publishing right from the terminal.
*   **Contribution Heatmap**: Branded GitHub Green calendar grid with terminal hover tooltips highlighting exact dates and contribution counts.
*   **Utility Generators**: Interactive README generation and local folder publishing to GitHub.

### 🤖 AI Agentic Coding
*   **AI Coding Agent**: Autonomous loop providing requirement expansion, project planning, code generation, syntax validation, and automated Git staging.
*   **Interactive Assistant**: Multi-turn coding sessions with persistent memory.
*   **AI Model Registry**: Central registry supporting customized OpenAI-compatible models, provider settings, temperatures, and custom headers.

### 📂 Workspace & Projects
*   **GC-Projects Workspace**: Automatic management of project paths, project compilation, and directory operations.
*   **VS Code Integration**: Instantly launch VS Code workspaces directly from CLI parameters.

### 🔌 Multi-Provider Support
*   **Local Execution**: Integration with Ollama for offline-first privacy.
*   **Cloud Scalability**: Powered by OpenRouter and NVIDIA NIM Cloud for state-of-the-art LLMs.

### ⚙️ System
*   **Interactive Theme System**: Hot-swappable CLI visual presets including Dracula, Nord, Synthwave, Monokai, and Default.
*   **Diagnostics Doctor**: Automatic environment configuration tests (Git, Auth tokens, local Ollama endpoints).

---

## 🛠 Implemented Commands

### GitHub & Repository Management
| Command | Category | Description |
| :--- | :--- | :--- |
| `profile` | GitHub | Show your GitHub profile details in a panel |
| `repos` | GitHub | List all your remote repositories |
| `latest` | GitHub | Show the latest created repository details |
| `pushed` | GitHub | Show the most recently pushed repository |
| `heatmap` | GitHub | Display your contribution heatmap with hover tooltips |
| `search` | GitHub | Search your repositories by keyword |
| `create` | Repository | Create a new GitHub repository |
| `publish` | Repository | Publish a local project folder to GitHub |
| `clone` | Repository | Clone a remote GitHub repository locally |
| `rename` | Repository | Rename a GitHub repository |
| `delete` | Repository | Delete an existing GitHub repository |
| `readme` | Repository | Interactively generate a README.md file |

### AI Coding Agents & Models
| Command | Category | Description |
| :--- | :--- | :--- |
| `ai` | AI | Enter interactive multi-turn AI chat mode |
| `ask` | AI | General AI assistant chatbot (no file edits or system commands) |
| `code` | AI | Autonomous AI Coding Agent (planning, execution, and validation) |
| `models` | AI | Register and manage custom AI models |

### Workspace & Projects
| Command | Category | Description |
| :--- | :--- | :--- |
| `workspace` | Workspace | Manage default GC-Projects workspace location |
| `projects` | Workspace | Manage and run generated projects in GC-Projects |

### System & Environment
| Command | Category | Description |
| :--- | :--- | :--- |
| `auth` | System | Manage GitHub and OpenRouter authentication credentials |
| `login` | System | Reconfigure GitHub credentials |
| `logout` | System | Remove GitHub credentials |
| `config` | System | Display or edit current settings |
| `doctor` | System | Run system environment diagnostics |
| `status` | System | Show current local Git status |
| `version` | System | Show installed Git CLI version |
| `help` | System | Show help tables |
| `exit` | System | Exit the interactive shell |

---

## 📐 Project Architecture

GitHub Companion is structured in distinct modular layers:

```
app.py (Entry)
   │
   └──> shell.py (Interactive Repl)
         │
         └──> commands/ (CLI Actions & Arg Parsers)
               │
               └──> services/ (Domain Layer)
                     │
                     ├──> ai/ (Agent Planning & Execution)
                     │     └──> providers/ (Ollama, OpenRouter, NVIDIA)
                     │
                     └──> OS Layer (GitHub API Client, Local Git CLI, Subprocess Services)
```

*   **Entry Points (`app.py` & `shell.py`)**: Handle commands and launch the interactive shell session.
*   **Command Module Layer (`commands/`)**: Parsers that handle arguments, prompt user selections, and construct output layout panels.
*   **Domain Service Layer (`services/`)**: Centralizes subprocess calls and API integrations. *Direct subprocess calls are prohibited in commands.*
*   **AI Service Layer (`ai/`)**: Handles prompts, state memory, and provider connections (Ollama, OpenRouter, NVIDIA).

---

## 🧠 AI Agentic Pipeline

The autonomous coding agent follows a sequential feedback loop to guarantee code correctness:

```
[Requirement Expansion]
         │
         ▼
[Implementation Planning] ──> Saves implementation_plan.md
         │
         ▼
[Code Generation] ──> Writes changes to files
         │
         ▼
[Syntax Validation] ──> Compiles files and runs tests
         │
         ▼
[Git Automation] ──> Automates staging/commit loops
```

1.  **Requirement Expansion**: Clarifies ambiguous goals, generating expanded specifications.
2.  **Implementation Planning**: Formulates a detailed design plan before modifying source files.
3.  **Code Generation**: Modifies file trees using targeted diff modifications.
4.  **Syntax Validation**: Checks python scripts with compiler modules to prevent broken syntax.
5.  **Git Automation**: Automatically packages verified edits into local Git staging.

---

## 🚀 Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/revanth-kumar-02/Github-Companion.git
   cd Github-Companion
   ```

2. Setup virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install production dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

### First-Time Setup
When you first run the CLI, run the doctor command to check requirements and verify credentials:
```bash
gc doctor
```

Setup your credentials:
```bash
gc auth
```

---

## 🗺 Roadmap

*   **Build & Test Runner**: Automated task runners integrated directly inside the agent loop.
*   **AI Code Review & Debugging**: Proactive code smells checks and automated stack trace debuggers.
*   **MCP Server Integration**: Expose CLI automation tools to external LLM clients.
*   **Plugin System**: Allow third-party visual themes and CLI helper command plugins.
*   **Session Restore**: Save and resume active agent workflows.

---

## 🤝 Contributing

We welcome contributions to GitHub Companion! Please check out our guidelines:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/cool-idea`).
3. Commit your changes (`git commit -m "feat: add cool idea"`).
4. Push to the branch (`git push origin feature/cool-idea`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
