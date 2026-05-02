# Graph Report - .  (2026-05-03)

## Corpus Check
- 68 files · ~0 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 454 nodes · 701 edges · 41 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 221 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_SlimApp Core|SlimApp Core]]
- [[_COMMUNITY_AlertableCommand Tests|AlertableCommand Tests]]
- [[_COMMUNITY_CommandRunner Scheduling|CommandRunner Scheduling]]
- [[_COMMUNITY_CLI Commands & Docs|CLI Commands & Docs]]
- [[_COMMUNITY_Cached DI Container|Cached DI Container]]
- [[_COMMUNITY_BuiltIn Commands & Config|BuiltIn Commands & Config]]
- [[_COMMUNITY_ConfigParser & PBT|ConfigParser & PBT]]
- [[_COMMUNITY_InitializeProject Command|InitializeProject Command]]
- [[_COMMUNITY_ParallelCommand Tests|ParallelCommand Tests]]
- [[_COMMUNITY_Agent & Doc Conventions|Agent & Doc Conventions]]
- [[_COMMUNITY_NamespaceResolver & PBT|NamespaceResolver & PBT]]
- [[_COMMUNITY_DaemonSentinel Tests|DaemonSentinel Tests]]
- [[_COMMUNITY_Fork Process Tests|Fork Process Tests]]
- [[_COMMUNITY_AbstractParallelCommand|AbstractParallelCommand]]
- [[_COMMUNITY_Sentinel Test Fixtures|Sentinel Test Fixtures]]
- [[_COMMUNITY_Parallel Test Fixtures|Parallel Test Fixtures]]
- [[_COMMUNITY_InitProject Tests|InitProject Tests]]
- [[_COMMUNITY_DummyCommand Fixture|DummyCommand Fixture]]
- [[_COMMUNITY_AbstractAlertableCommand|AbstractAlertableCommand]]
- [[_COMMUNITY_TestSentinel Fixture|TestSentinel Fixture]]
- [[_COMMUNITY_TestController Fixture|TestController Fixture]]
- [[_COMMUNITY_TestAppConfig Fixture|TestAppConfig Fixture]]
- [[_COMMUNITY_CommandConfig PBT|CommandConfig PBT]]
- [[_COMMUNITY_Sentinel Scheduling Docs|Sentinel Scheduling Docs]]
- [[_COMMUNITY_Issue Lifecycle|Issue Lifecycle]]
- [[_COMMUNITY_Init Test Environment|Init Test Environment]]
- [[_COMMUNITY_Test Bootstrap|Test Bootstrap]]
- [[_COMMUNITY_Integration HTTP|Integration HTTP]]
- [[_COMMUNITY_Integration Bootstrap|Integration Bootstrap]]
- [[_COMMUNITY_Integration Console|Integration Console]]
- [[_COMMUNITY_Coverage Merge Script|Coverage Merge Script]]
- [[_COMMUNITY_Unreleased Changes|Unreleased Changes]]
- [[_COMMUNITY_Changelog|Changelog]]
- [[_COMMUNITY_DI Construction Phase|DI Construction Phase]]
- [[_COMMUNITY_DI Setting Phase|DI Setting Phase]]
- [[_COMMUNITY_DI Decoration Phase|DI Decoration Phase]]
- [[_COMMUNITY_Default Namespace|Default Namespace]]
- [[_COMMUNITY_Service Access|Service Access]]
- [[_COMMUNITY_Sentinel Creation|Sentinel Creation]]
- [[_COMMUNITY_Parallel Index|Parallel Index]]
- [[_COMMUNITY_Issue Severity|Issue Severity]]

## God Nodes (most connected - your core abstractions)
1. `SlimAppTest` - 43 edges
2. `CommandRunnerTest` - 27 edges
3. `ConsoleApplicationTest` - 22 edges
4. `InitializeProjectCommand` - 22 edges
5. `SlimApp` - 21 edges
6. `ConfigParser` - 18 edges
7. `AbstractParallelCommandTest` - 15 edges
8. `SlimAppCachedContainer` - 14 edges
9. `ConsoleApplication` - 14 edges
10. `NamespaceResolver` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Issue Archive Process` --semantically_similar_to--> `Spec Archive Process`  [INFERRED] [semantically similar]
  issues/README.md → docs/changes/README.md
- `Proposal Lifecycle` --triggers--> `Spec Directory`  [INFERRED]
  docs/proposals/README.md → AGENTS.md
- `Issue Archive Process` --archives_to--> `Changes Directory Purpose`  [INFERRED]
  issues/README.md → docs/changes/README.md
- `SlimApp Framework` --references--> `Console Application`  [EXTRACTED]
  PROJECT.md → docs/state/architecture.md
- `SlimApp Framework` --references--> `Logging System`  [EXTRACTED]
  PROJECT.md → docs/state/architecture.md

## Hyperedges (group relationships)
- **Documentation Governance System** — agents_doc_layers, agents_ssot, proposals_lifecycle, issues_lifecycle, changes_readme [INFERRED 0.80]
- **Release 3.0 Core Changes** — release_3_0, microkernel, private_by_default, abstract_daemon_sentinel_removed, pbt_testing [EXTRACTED 0.90]
- **SlimApp Core Subsystems** — slimapp_framework, di_container, config_system, logging_system, microkernel, console_application_concept [EXTRACTED 0.95]
- **Migration Breaking Changes** — migration_guide, microkernel, private_by_default, abstract_daemon_sentinel_removed, phpunit13 [EXTRACTED 0.90]

## Communities

### Community 0 - "SlimApp Core"
Cohesion: 0.07
Nodes (2): SlimApp, SlimAppTest

### Community 1 - "AlertableCommand Tests"
Cohesion: 0.06
Nodes (6): AbstractAlertableCommandTest, ConcreteAlertableCommand, ConsoleApplication, ConsoleApplicationTest, ValidateServicesCommandTest, VerbosityMappingPbtTest

### Community 2 - "CommandRunner Scheduling"
Cohesion: 0.09
Nodes (4): CommandRunner, CommandRunnerSchedulingPbtTest, CommandRunnerTest, DaemonSentinelCommand

### Community 3 - "CLI Commands & Docs"
Cohesion: 0.07
Nodes (32): AbstractAlertableCommand, AbstractDaemonSentinelCommand (Removed), AbstractParallelCommand, ClearCacheCommandTest, ConfigParser, Configuration System, config.yml, Console Application (+24 more)

### Community 4 - "Cached DI Container"
Cohesion: 0.1
Nodes (3): SlimAppCachedContainer, SlimAppCompilerPass, SlimAppCompilerPassTest

### Community 5 - "BuiltIn Commands & Config"
Cohesion: 0.08
Nodes (4): ClearCacheCommand, CommandConfiguration, CommandConfigurationTest, ValidateServicesCommand

### Community 6 - "ConfigParser & PBT"
Cohesion: 0.12
Nodes (4): ConfigParser, ConfigParserPbtTest, PbtTestAppConfig, ConfigParserTest

### Community 7 - "InitializeProject Command"
Cohesion: 0.21
Nodes (1): InitializeProjectCommand

### Community 8 - "ParallelCommand Tests"
Cohesion: 0.1
Nodes (2): AbstractParallelCommandTest, ConcreteParallelCommand

### Community 9 - "Agent & Doc Conventions"
Cohesion: 0.11
Nodes (20): docs/changes/, Documentation Layers, issues/, docs/manual/, docs/notes/, docs/proposals/, Spec Directory, SSOT Principle (+12 more)

### Community 10 - "NamespaceResolver & PBT"
Cohesion: 0.18
Nodes (3): NamespaceResolver, NamespaceResolverPbtTest, NamespaceResolverTest

### Community 11 - "DaemonSentinel Tests"
Cohesion: 0.22
Nodes (1): DaemonSentinelCommandTest

### Community 12 - "Fork Process Tests"
Cohesion: 0.39
Nodes (1): ForkProcessTest

### Community 13 - "AbstractParallelCommand"
Cohesion: 0.46
Nodes (1): AbstractParallelCommand

### Community 14 - "Sentinel Test Fixtures"
Cohesion: 0.33
Nodes (2): SentinelDummyCommand, TestableSentinelCommand

### Community 15 - "Parallel Test Fixtures"
Cohesion: 0.33
Nodes (1): ForkTestCommand

### Community 16 - "InitProject Tests"
Cohesion: 0.5
Nodes (1): InitializeProjectCommandTest

### Community 17 - "DummyCommand Fixture"
Cohesion: 0.5
Nodes (1): DummyCommand

### Community 18 - "AbstractAlertableCommand"
Cohesion: 0.5
Nodes (1): AbstractAlertableCommand

### Community 19 - "TestSentinel Fixture"
Cohesion: 0.67
Nodes (1): TestSentinelCommand

### Community 20 - "TestController Fixture"
Cohesion: 0.67
Nodes (1): TestController

### Community 21 - "TestAppConfig Fixture"
Cohesion: 0.67
Nodes (1): TestAppConfig

### Community 22 - "CommandConfig PBT"
Cohesion: 0.67
Nodes (1): CommandConfigurationPbtTest

### Community 23 - "Sentinel Scheduling Docs"
Cohesion: 0.67
Nodes (3): Frequency Fixed Mode, Interval vs Frequency, Scheduling Strategies

### Community 24 - "Issue Lifecycle"
Cohesion: 0.67
Nodes (3): L Series (Production Bugs), Issue Lifecycle, Release Issue Series

### Community 25 - "Init Test Environment"
Cohesion: 1.0
Nodes (2): init-ut Test Environment, slimapp:project:init

### Community 26 - "Test Bootstrap"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Integration HTTP"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Integration Bootstrap"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Integration Console"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Coverage Merge Script"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Unreleased Changes"
Cohesion: 1.0
Nodes (1): Unreleased Changes

### Community 32 - "Changelog"
Cohesion: 1.0
Nodes (1): CHANGELOG Format

### Community 33 - "DI Construction Phase"
Cohesion: 1.0
Nodes (1): Construction Phase (manual)

### Community 34 - "DI Setting Phase"
Cohesion: 1.0
Nodes (1): Setting Phase (manual)

### Community 35 - "DI Decoration Phase"
Cohesion: 1.0
Nodes (1): Decoration Phase (manual)

### Community 36 - "Default Namespace"
Cohesion: 1.0
Nodes (1): Default Namespace (manual)

### Community 37 - "Service Access"
Cohesion: 1.0
Nodes (1): Service Access API (manual)

### Community 38 - "Sentinel Creation"
Cohesion: 1.0
Nodes (1): Sentinel Command Creation

### Community 39 - "Parallel Index"
Cohesion: 1.0
Nodes (1): PARALLEL_INDEX Variable

### Community 40 - "Issue Severity"
Cohesion: 1.0
Nodes (1): Issue Severity Levels

## Knowledge Gaps
- **35 isolated node(s):** `Unreleased Changes`, `CHANGELOG Format`, `State Directory Purpose`, `Construction Phase (manual)`, `Setting Phase (manual)` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Init Test Environment`** (2 nodes): `init-ut Test Environment`, `slimapp:project:init`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Bootstrap`** (1 nodes): `bootstrap.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Integration HTTP`** (1 nodes): `http.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Integration Bootstrap`** (1 nodes): `bootstrap.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Integration Console`** (1 nodes): `console.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage Merge Script`** (1 nodes): `merge_coverage.php`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Unreleased Changes`** (1 nodes): `Unreleased Changes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Changelog`** (1 nodes): `CHANGELOG Format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DI Construction Phase`** (1 nodes): `Construction Phase (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DI Setting Phase`** (1 nodes): `Setting Phase (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DI Decoration Phase`** (1 nodes): `Decoration Phase (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Default Namespace`** (1 nodes): `Default Namespace (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Service Access`** (1 nodes): `Service Access API (manual)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sentinel Creation`** (1 nodes): `Sentinel Command Creation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Parallel Index`** (1 nodes): `PARALLEL_INDEX Variable`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Issue Severity`** (1 nodes): `Issue Severity Levels`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SlimApp` connect `SlimApp Core` to `CLI Commands & Docs`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `ConfigParser` connect `ConfigParser & PBT` to `SlimApp Core`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `SlimApp` (e.g. with `.testAppReturnsSingleton()` and `.testAppReturnsSlimAppInstance()`) actually correct?**
  _`SlimApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Unreleased Changes`, `CHANGELOG Format`, `State Directory Purpose` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `SlimApp Core` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._
- **Should `AlertableCommand Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `CommandRunner Scheduling` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._