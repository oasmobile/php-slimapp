# Module 配置

仓库布局与 manifest 见 [仓库契约](repository-contract.md)。

## Modules

`.mdf/modules.yaml` 声明每个 module 的 sourceset、ignore 与分套件入口：

```yaml
# verification:          # 可选；覆写的入口不再按 module 展开
#   lint: "make -j1 lint"
modules:
  default:
    sourceset: ["src/**"]
    ignore: []
    lint: "true"
    build: "true"
    quick:
      command: "python3 -m pytest -m quick"
      tests: ["tests/unit/**"]
    smoke:
      command: "python3 -m pytest -m smoke"
      tests: ["tests/unit/**", "tests/smoke/**"]
    release:
      command: "python3 -m pytest -m release"
      tests: ["tests/**"]
    named: []
budgets:
  quick: 45
```

- 每个 module 必须声明 `sourceset`、`lint`、`build`、以及
  `quick`/`smoke`/`release`（含 `command` 与非空 `tests` glob）。
  - 可选 `ignore`、`named`、`size_limits` 与 `coverage`。
- **ignore**：`pattern` + `reason`，路径与 pattern 均相对 repo 根；可排除源代码、测试源代码与文档。
  - `modules.<name>.ignore` 仅在自身 `sourceset` 内生效，不能排除其他 module 或未归属文件。
  - 重叠 `sourceset` 中仍有 module 未忽略该文件时，保留该 module 的验证与检查。
  - verify、lint、prose-check 与审阅共用 module ignore 的归属判断。
  - fact audit 与 code-review 的实现范围先与 `sourceset` 并集求交，再应用 module ignore。
  - 未归属实现不进入审阅；事实页、文档入口及交付材料仍按各自契约检查。
  - 命中路径不触发 verify，也不产生 uncovered / `agents.project_content` 类提示。
  - lint 跳过命中文件的代码规模检查，package 计数排除命中文件；fact audit 与 prose-check 跳过其文档规模与结构检查。
  - 命中文件不受长度与 70% 拆分要求约束；审阅不得再按这些规则要求拆分，报告匹配路径与理由。
  - `fact-audit` 的 `ignored` 保留命中路径、pattern 与 reason；未匹配的已跟踪文件仍正常检查。
  - fact audit 各 scope 均排除有效 ignore 命中的语义审阅路径；项目事实页独立判定。
  - against 审阅与普通 audit 使用当前工作区的 ignore 与 sourceset；交付 CI context 使用固定 source 配置。
    具体范围与报告约束见 [独立事实审阅](fact-audit-against.md)。
- **quick ⊆ smoke ⊆ release**：以 `tests` glob 匹配到的已跟踪文件集校验。
- repo 级同名入口默认按 module 名排序**串行展开**执行（plan id 为
  `<entry>:<module>`）；可选顶层 `verification` 覆写子集为单命令（id 为
  `<entry>`）。`budgets` 仍为顶层可选。
- `named` 中每个名字必须有独立文档 `docs/system/testing/<name>.md`：
  - frontmatter 必填 `commands`（非空字符串列表）或简写 `command`；
    可选 `parallel: true`（并行时命令数须 ≤5，否则 Core 报错）。
  - 正文写明目的与 testcase 构成；testcase 本身靠代码 frontmatter/stringdoc。
- `quick`/`smoke`/`release` mapping 可选 `parallel: true`（按 module 展开的多命令）。
- 初始化仍可通过 CLI 传入 `--lint` 等，写入默认 module。
- 占位命令必然失败：不得用恒成功的空命令冒充真实 lint/build/suite。

例外写在 module `ignore`。

- 未被 `evidence` 引用且未被 ignore 的实现文件会产生 warning，不阻断 audit，但必须在语义审阅中由用户确认。
  - 锁文件、`.gitignore` 与版本钉等不承载行为的文件不产生该 warning。

### Module 规模 override

每个 module 可选 `size_limits`，仅覆盖源代码和 package；匹配范围由该 module 的 `sourceset` 决定。

```yaml
size_limits:
  max_file_lines: 1200
  max_package_files: 60
  split_percent: 70
```

| 字段 | 默认值 | 要求 |
| --- | --- | --- |
| `max_file_lines` | 1000 | 正整数，源代码及测试源代码的单文件行数硬上限 |
| `max_package_files` | 50 | 正整数，package 直属实现/测试文件数分别使用的硬上限 |
| `split_percent` | 70 | 整数 1–100，两个拆分目标向下取整后均须至少为 1 |

- 缺省或空 mapping 按字段继承默认值；null、未知键、布尔值、字符串、浮点数与非法数值均拒绝。
- 拆分目标为 `floor(对应硬上限 × split_percent / 100)`；上例为 840 行、42 文件。
- 同一文件命中多个 module 时，各配置分别检查；不按配置顺序覆盖，不把不同 module 的值拼成一套策略。
  - 只有某配置超限才产生该配置的 finding，报告标明 module、硬上限及其拆分目标。
  - 超限拆分须满足所有触发配置的目标；迁移后的文件和 package 还须满足新位置的适用硬限制。
- package 仍按完整目录的同类成员总数检查，使用这些成员命中的全部 module 配置。
  - 未归属任何 module 的文件使用默认策略；package 有未归属成员时默认策略也参与该组检查。
  - 已匹配 module 未写某字段时仍使用其默认值；实现与测试各自确定适用配置，不相加。
  - 测试目录需要 override 时也须纳入 `sourceset`，不从 suite 的 `tests` glob 推断归属。
- module `ignore` 优先；文档上限、文档拆分比例与 `prose.*` 不受 `size_limits` 影响。

## 可选 coverage 入口

本节定义与 lint/build 同级的 coverage 配置和项目报告接口。

```yaml
modules:
  app:
    coverage:
      command: scripts/coverage.sh
      targets:
        lines: 85
        branches: 75
```

- coverage 可省略；配置后必须完整提供 command 与非空 targets，metric 名由项目声明。
- 每个 target 是 0–100 的有限数，不接受布尔值；MDF 按原始比例比较，不四舍五入抬过阈值。
- 顶层 verification.coverage 可用同一完整定义覆写全部 module；整项替换，只执行一次。
- command 在本次 `$MDF_REPORT_DIR/coverage.json` 写入统一报告，不读取旧运行目录。

```json
{"metrics":{"lines":{"covered":85,"total":100},"branches":{"covered":3,"total":4}}}
```

- 每个配置 metric 都须有整数 covered/total，满足 0 <= covered <= total 且 total > 0。
- 命令失败、缺报告、缺 metric、非法计数、零 total 或任一 target 未达标均失败。
- MDF 写入 summary.json，包含实际比例、target、各 metric 结果或报告错误；完整 stdout/stderr 同目录保存。
- coverage 不套用 JUnit 解析，不加入 quick/smoke/release 的成员集合，也不计入 quick 的预算。
- `$mdf verify coverage` 可显式执行；未配置时返回 configured: false，不生成虚假的测量结果。
- 自动执行仅属于 feature/release 的实际 converge：smart 通过后执行，未达标不勾 converge。
- release 的 has_dev: no 仍跳过 converge 与 coverage；其他流程可显式调用。
- coverage 是保留入口名，不得用作 module 名或普通 named suite 名。
