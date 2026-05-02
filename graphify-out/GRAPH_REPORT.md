# Graph Report - .  (2026-05-02)

## Corpus Check
- Corpus is ~12,596 words - fits in a single context window. You may not need a graph.

## Summary
- 218 nodes · 244 edges · 34 communities detected
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_SlimApp Core & Cache|SlimApp Core & Cache]]
- [[_COMMUNITY_Architecture Documentation|Architecture Documentation]]
- [[_COMMUNITY_Project Initialization|Project Initialization]]
- [[_COMMUNITY_CLI & HTTP Subsystems|CLI & HTTP Subsystems]]
- [[_COMMUNITY_Documentation Governance|Documentation Governance]]
- [[_COMMUNITY_Console Application|Console Application]]
- [[_COMMUNITY_Daemon Sentinel Runtime|Daemon Sentinel Runtime]]
- [[_COMMUNITY_Daemon Sentinel Docs|Daemon Sentinel Docs]]
- [[_COMMUNITY_Compiler Pass & Config|Compiler Pass & Config]]
- [[_COMMUNITY_Parallel Command Execution|Parallel Command Execution]]
- [[_COMMUNITY_Alertable Command Base|Alertable Command Base]]
- [[_COMMUNITY_Dummy Test Command|Dummy Test Command]]
- [[_COMMUNITY_Test Controller|Test Controller]]
- [[_COMMUNITY_Test Sentinel Command|Test Sentinel Command]]
- [[_COMMUNITY_Test App Config|Test App Config]]
- [[_COMMUNITY_Service Description Phases|Service Description Phases]]
- [[_COMMUNITY_Logging Standards|Logging Standards]]
- [[_COMMUNITY_Issue Lifecycle|Issue Lifecycle]]
- [[_COMMUNITY_DaemonSentinelCommand|DaemonSentinelCommand]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]
- [[_COMMUNITY_Singleton|Singleton]]

## God Nodes (most connected - your core abstractions)
1. `InitializeProjectCommand` - 22 edges
2. `SlimApp` - 19 edges
3. `ConsoleApplication` - 14 edges
4. `SlimApp Framework` - 13 edges
5. `AbstractParallelCommand` - 8 edges
6. `CommandRunner` - 7 edges
7. `Documentation Layers` - 7 edges
8. `DI Container Architecture` - 5 edges
9. `AbstractDaemonSentinelCommand` - 4 edges
10. `CommandConfiguration` - 4 edges

## Surprising Connections (you probably didn't know these)
- `SlimApp Singleton Pattern` --semantically_similar_to--> `Bootstrap Process`  [INFERRED] [semantically similar]
  docs/state/architecture.md → README.md
- `services.yml` --semantically_similar_to--> `Service Container (README)`  [INFERRED] [semantically similar]
  docs/state/configuration.md → README.md
- `Issue Archive Process` --semantically_similar_to--> `Spec Archive Process`  [INFERRED] [semantically similar]
  issues/README.md → docs/changes/README.md
- `SlimApp Singleton Pattern` --describes--> `SlimApp Framework`  [EXTRACTED]
  docs/state/architecture.md → PROJECT.md
- `Proposal Lifecycle` --triggers--> `Spec Directory`  [INFERRED]
  docs/proposals/README.md → AGENTS.md

## Hyperedges (group relationships)
- **SlimApp Dual Runtime Mode** — project_slimapp, project_http_kernel_mode, project_cli_console_mode [EXTRACTED 1.00]
- **Service Definition Lifecycle** — readme_service_description, readme_service_container, readme_app_service [EXTRACTED 1.00]
- **SlimApp Initialization Pipeline** — arch_init_flow, arch_config_system, arch_di_container, arch_logging_system [EXTRACTED 1.00]
- **Built-in CLI Commands** — cli_project_init, cli_cache_clear, cli_services_validate [EXTRACTED 1.00]
- **Documentation Governance System** — agents_doc_layers, agents_ssot, proposals_lifecycle, issues_lifecycle, changes_readme [INFERRED 0.80]
- **Daemon Sentinel Full Picture** — arch_daemon_sentinel, cli_daemon_sentinel_cmd, config_sentinel_yml, manual_ds_scheduling [INFERRED 0.85]

## Communities

### Community 0 - "SlimApp Core & Cache"
Cohesion: 0.08
Nodes (3): ClearCacheCommand, SlimApp, ValidateServicesCommand

### Community 1 - "Architecture Documentation"
Cohesion: 0.08
Nodes (24): SlimAppCompilerPass, Configuration Cache, Configuration System, ConsoleHandler, Container Cache, Default Namespace Resolution, DI Container Architecture, Initialization Flow (+16 more)

### Community 2 - "Project Initialization"
Cohesion: 0.21
Nodes (1): InitializeProjectCommand

### Community 3 - "CLI & HTTP Subsystems"
Cohesion: 0.1
Nodes (21): Console Application Architecture, HTTP Kernel Architecture, slimapp:cache:clear Command, slimapp:project:init Command, slimapp:services:validate Command, Project Init Guide, Installation Guide, CLI Console Mode (+13 more)

### Community 4 - "Documentation Governance"
Cohesion: 0.11
Nodes (20): docs/changes/, Documentation Layers, issues/, docs/manual/, docs/notes/, docs/proposals/, Spec Directory, SSOT Principle (+12 more)

### Community 5 - "Console Application"
Cohesion: 0.18
Nodes (1): ConsoleApplication

### Community 6 - "Daemon Sentinel Runtime"
Cohesion: 0.22
Nodes (2): AbstractDaemonSentinelCommand, CommandRunner

### Community 7 - "Daemon Sentinel Docs"
Cohesion: 0.15
Nodes (13): Daemon Sentinel Architecture, AbstractAlertableCommand (doc), AbstractParallelCommand (doc), DaemonSentinelCommand (doc), Exit Codes, pcntl_fork Mechanism, Sentinel YAML Config, Sentinel Command Creation (+5 more)

### Community 8 - "Compiler Pass & Config"
Cohesion: 0.22
Nodes (2): CommandConfiguration, SlimAppCompilerPass

### Community 9 - "Parallel Command Execution"
Cohesion: 0.39
Nodes (1): AbstractParallelCommand

### Community 10 - "Alertable Command Base"
Cohesion: 0.5
Nodes (1): AbstractAlertableCommand

### Community 11 - "Dummy Test Command"
Cohesion: 0.5
Nodes (1): DummyCommand

### Community 12 - "Test Controller"
Cohesion: 0.67
Nodes (1): TestController

### Community 13 - "Test Sentinel Command"
Cohesion: 0.67
Nodes (1): TestSentinelCommand

### Community 14 - "Test App Config"
Cohesion: 0.67
Nodes (1): TestAppConfig

### Community 15 - "Service Description Phases"
Cohesion: 0.67
Nodes (3): Construction Phase (manual), App Service Definition, Service Description Phases

### Community 16 - "Logging Standards"
Cohesion: 0.67
Nodes (3): Logging System, Monolog, PSR-3 Logging Interface

### Community 17 - "Issue Lifecycle"
Cohesion: 0.67
Nodes (3): L Series (Production Bugs), Issue Lifecycle, Release Issue Series

### Community 18 - "DaemonSentinelCommand"
Cohesion: 1.0
Nodes (1): DaemonSentinelCommand

### Community 19 - "Singleton"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Singleton"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Singleton"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Singleton"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Singleton"
Cohesion: 1.0
Nodes (1): Installation & Setup

### Community 24 - "Singleton"
Cohesion: 1.0
Nodes (1): Command Class Hierarchy

### Community 25 - "Singleton"
Cohesion: 1.0
Nodes (1): Parameter Reference Syntax

### Community 26 - "Singleton"
Cohesion: 1.0
Nodes (1): Service Reference Syntax

### Community 27 - "Singleton"
Cohesion: 1.0
Nodes (1): Setting Phase (manual)

### Community 28 - "Singleton"
Cohesion: 1.0
Nodes (1): Decoration Phase (manual)

### Community 29 - "Singleton"
Cohesion: 1.0
Nodes (1): Directory Structure Guide

### Community 30 - "Singleton"
Cohesion: 1.0
Nodes (1): PARALLEL_INDEX Variable

### Community 31 - "Singleton"
Cohesion: 1.0
Nodes (1): Unreleased Changes

### Community 32 - "Singleton"
Cohesion: 1.0
Nodes (1): CHANGELOG Format

### Community 33 - "Singleton"
Cohesion: 1.0
Nodes (1): Issue Severity Levels

## Knowledge Gaps
- **58 isolated node(s):** `DaemonSentinelCommand`, `PHP Microframework`, `HTTP Kernel Mode`, `YAML Configuration`, `Oasis Logging` (+53 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `DaemonSentinelCommand`** (2 nodes): `DaemonSentinelCommand`, `DaemonSentinelCommand.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `test.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `index.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `bootstrap.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `app.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Installation & Setup`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Command Class Hierarchy`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Parameter Reference Syntax`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Service Reference Syntax`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Setting Phase (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Decoration Phase (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Directory Structure Guide`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `PARALLEL_INDEX Variable`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Unreleased Changes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `CHANGELOG Format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Singleton`** (1 nodes): `Issue Severity Levels`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SlimApp Framework` connect `CLI & HTTP Subsystems` to `Architecture Documentation`, `Daemon Sentinel Docs`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `SlimApp Singleton Pattern` connect `Architecture Documentation` to `CLI & HTTP Subsystems`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `SlimApp` connect `SlimApp Core & Cache` to `Compiler Pass & Config`, `Console Application`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **What connects `DaemonSentinelCommand`, `PHP Microframework`, `HTTP Kernel Mode` to the rest of the system?**
  _58 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `SlimApp Core & Cache` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Architecture Documentation` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `CLI & HTTP Subsystems` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._