# 交付目标

## 流程

- needs_design: {{MDF_NEEDS_DESIGN}}

## 步骤

依赖链由上到下；完成一项由对应 intent **自勾** `[x]`。
进度只认本清单，不以 `gates/*.json` 或 verify/fact 报告当通行证。

- [ ] 确认目标与约束（start）
- [ ] design（仅 needs_design: yes；由 `$mdf design` 自勾）
- [ ] write-tests（needs_design: yes 且有 qa；否则并入 owner 开发）
- [ ] implement（needs_design: yes 且有 dev；否则并入 owner 开发）
- [ ] owner 开发（仅 needs_design: no，或 roster `0,0` 的串行开发）
- [ ] converge（objectives 前置已勾 + smart；由 `$mdf converge` 自勾）
- [ ] lint（由 `$mdf lint` 自勾）
- [ ] code-review（由 `$mdf code-review` 自勾；报告见 code-review.md）
- [ ] verify branch（由 `$mdf verify` branch 自勾；报告见 verification-report.json）
- [ ] fact audit（由 `$mdf fact audit` 自勾；必要时先 fact update）
- [ ] close-out（由 `$mdf close-out` 自勾）

## 需求来源

{{MDF_PROPOSAL_REFERENCE}}

## 目标与非目标

{{MDF_GOALS_AND_NON_GOALS}}

## 约束

{{MDF_DELIVERY_CONSTRAINTS}}

## 可验证验收

{{MDF_ACCEPTANCE_CRITERIA}}
