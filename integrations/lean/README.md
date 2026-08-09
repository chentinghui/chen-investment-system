# QuantConnect LEAN External Integration（CIS 0.4.5）

`QuantConnect LEAN` 是 CIS 的**外部量化验证引擎**。CIS 不复制、不 fork、不 vendor LEAN 源码；LEAN 继续独立安装和升级，CIS 只维护本目录中的适配层。

```text
CIS Core
  ↓ 仅在规则/策略需要量化验证时
CIS Backtest Validation Policy
  ↓
integrations/lean/cis_lean_adapter.py
  ↓
外部 Lean CLI + Docker + QuantConnect/Lean
  ↓
LEAN 原生 backtest JSON
  ↓
CIS 统一结果契约
  ↓
Evidence / Risk / Backtest Validation Review
```

LEAN **没有 CIS 最终动作权**。回测成功只说明策略在给定数据、参数、费用模型和样本区间内得到某个历史结果，不等于未来有效，也不自动产生 `买入/持有/减仓/清仓`。

## 为什么独立维护

- 不把第三方大仓库塞进 `chen-investment-system`；
- LEAN 可以独立升级，CIS 只维护稳定适配协议；
- LEAN 故障、Docker 故障、账户/数据权限问题不会阻塞 CIS Core；
- 以后更换执行器时，CIS 上层只依赖统一结果契约，而不是依赖 LEAN 内部实现。

## 当前适配能力

`cis_lean_adapter.py` 使用 Python 标准库，不引入新的 CIS Python 依赖，提供三种命令：

```bash
# 1. 检查本机 Lean CLI / Docker 是否可用
python integrations/lean/cis_lean_adapter.py readiness

# 2. 运行本地 LEAN 回测
python integrations/lean/cis_lean_adapter.py backtest \
  --project /path/to/lean-project \
  --output /path/to/lean-results

# 3. 只解析已有 LEAN 结果，不要求本机安装 LEAN
python integrations/lean/cis_lean_adapter.py parse \
  --result /path/to/backtest-id.json
```

运行回测时适配器使用官方命令形态：

```text
lean backtest <project> --output <directory>
```

`--update-image` 可显式要求 Lean CLI 更新其使用的引擎镜像。

## CIS 统一结果契约

成功解析后输出 JSON：

```json
{
  "schema_version": "cis.lean.backtest.v1",
  "engine": "QuantConnect LEAN",
  "engine_role": "external_quant_validation",
  "decision_authority": "none",
  "execution_status": "success",
  "research_quality": "unreviewed",
  "metrics": {
    "cagr": 0.185,
    "max_drawdown": 0.1225,
    "sharpe_ratio": 1.42,
    "win_rate": 0.61
  }
}
```

适配器同时保留 `statistics_raw` 和可用的 `runtime_statistics_raw`，避免因字段归一化丢失 LEAN 原始结果。百分比指标归一化为小数，例如 `18.5% -> 0.185`。

## 失败语义

```text
execution_status = success | invalid_input | unavailable | error
runtime_readiness = ready | lean_cli_missing | docker_missing | unavailable
research_quality = unreviewed
```

- `success`：LEAN 程序返回成功且找到可识别的 backtest JSON；
- `invalid_input`：项目/结果文件等输入无效；
- `unavailable`：本机缺少 Lean CLI 或 Docker；
- `error`：LEAN 非零退出、超时或结果解析失败。

**程序运行成功与研究质量通过必须分开。** `research_quality=unreviewed` 必须经过 `references/backtest-validation.md` 的样本外、前视偏差、幸存者偏差、成本和稳健性检查后才能升级为可采信的量化证据。

## 前置条件与账户边界

截至 2026-08-09，QuantConnect 官方文档说明：

- Lean CLI 通过 Python 包安装；
- 本地 `lean backtest` 使用 Docker 运行 LEAN；
- 官方 Lean CLI 文档当前要求用户属于 QuantConnect 付费组织层级；
- 数据授权、组织 workspace、QuantConnect 登录和数据费用仍由 QuantConnect/用户环境管理，CIS 不保存这些凭据。

这不改变 `QuantConnect/Lean` 作为独立开源项目的维护方式；当前 **CIS adapter v1 只实现官方 Lean CLI 本地 backtest 路径与结果解析**。

官方资料：

- LEAN: https://github.com/QuantConnect/Lean
- Lean CLI: https://www.quantconnect.com/docs/v2/lean-cli
- `lean backtest`: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-backtest
- Local backtest results: https://www.quantconnect.com/docs/v2/local-platform/backtesting/results

## 安全边界

- 不读取、记录或打印 QuantConnect/Broker API Secret；
- 不自动登录 QuantConnect；
- 不自动连接 Broker；
- 不执行 live trading；
- 不把 LEAN 输出直接转换成最终买卖动作；
- 外部引擎不可用时，CIS Core 继续正常运行。

## 与旧 Backtest Extension 的关系

`extensions/research_tooling/backtest_factor_strategy.py` 保留，但定位调整为**轻量横截面 baseline evaluator**：适合快速检查 `date,ticker,score,forward_return` 形式的因子排序逻辑。

需要事件驱动、真实交易规则、订单/费用/持仓路径、ETF/股票/期权策略等更完整验证时，**LEAN 是首选外部回测引擎**。两者不同时跑来制造重复结论。
