# TradingAgents 默认研究核心适配

TradingAgents 是 CIS 0.3.0 的默认通用股票研究/决策核心，但不是 CIS 的最终规则所有者。

- 上游：`https://github.com/TauricResearch/TradingAgents`
- 默认分支：`main`
- 当前核验版本（2026-08-09）：README 标示 v0.3.1（2026-07）。
- 许可证：Apache License 2.0；每次 vendoring、再分发或重大升级前重新核验。
- CIS 默认不复制 TradingAgents 源码；优先使用已安装 Python 包或可访问的当前上游。

## 角色分工

TradingAgents 默认承担：

1. Fundamentals Analyst：通用基本面初筛与红旗识别。
2. Sentiment Analyst：有真实来源支撑的短期市场情绪。
3. News Analyst：新闻与宏观事件影响。
4. Technical Analyst：通用技术指标与市场结构初步判断。
5. Bull / Bear Researchers：多空论证与结构化辩论。
6. Research Manager：汇总研究分歧与关键证据。
7. Trader：形成候选交易方案。
8. Risk Management Team：评估候选方案的风险。
9. Portfolio Manager：输出 TradingAgents 自身的候选决策。

TradingAgents 的 Portfolio Manager 输出只能视为 `external_decision_candidate`，不得直接成为 CIS 最终动作。

## CIS 保留的最终控制权

以下能力不得委托给 TradingAgents 覆盖：

- Runtime Guard 与 GitHub 当前版本校验；
- 证据等级、资料截止时间、来源冲突和 evidence audit；
- CIS 八维评分与 coverage gate；
- 四层交易框架（趋势 → 价格 → 成交 → 风险）；
- 盈利止盈 + 防守止损双路径；
- 跨境 ETF / QDII 产品身份、IOPV、历史溢价和申赎纪律；
- 组合数据门；
- 用户个人投资规则；
- 最终中文研究姿态、证伪条件和复盘计划。

## 与 Anthropic Financial Services 的关系

TradingAgents 是默认“研究团队/决策候选引擎”；Anthropic Financial Services 是专业金融方法库。

当研究需要以下专业工作时，TradingAgents 的通用分析不得替代 Anthropic 对应 Skill：

- DCF；
- Comps；
- 三表模型；
- 模型审计与数据清洗；
- earnings preview / earnings analysis；
- initiating coverage；
- model update；
- competitive analysis；
- thesis tracker / catalyst calendar。

标准路径：

```text
CIS intake
  ↓
TradingAgents 通用研究核心
  ↓
识别专业子问题
  ↓
Anthropic Financial Services（按需）
  ↓
结果回灌 TradingAgents/CIS 证据登记
  ↓
CIS 证据门 + 风险门 + 八维评分
  ↓
四层交易框架 / 组合门
  ↓
CIS 最终结论
```

## 运行状态

每次任务必须明确记录 TradingAgents 的本次状态：

- `installed_ready`：`tradingagents` 包可导入，必要 API/数据源就绪，可运行 `.propagate()`。
- `installed_limited`：包可导入，但部分数据源/模型/API 不可用；只能使用可验证输出。
- `upstream_only`：可读取上游方法/架构，但当前环境未安装可执行包；不得声称已运行 TradingAgents。
- `unavailable`：无法读取上游且无法导入包。
- `blocked`：任务必须依赖 TradingAgents 才能回答，而运行条件不足。

“仓库持续更新”与“市场数据实时”必须分开：代码版本更新不代表行情、新闻或情绪数据实时；数据时效取决于本次实际调用的数据提供商。

## 执行入口

官方包调用路径以当前上游 README 为准。CIS 适配器使用：

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=False, config=DEFAULT_CONFIG.copy())
_, decision = ta.propagate(ticker, analysis_date)
```

CIS 自带 `scripts/run_tradingagents.py` 只负责安全探测、调用和结构化返回，不修改 TradingAgents 本体。

## 数据与防前视纪律

- 历史日期分析必须使用不晚于 `analysis_date` 的信息；不得把后续财报、新闻、价格或情绪泄漏到过去。
- 每个外部数据源必须记录 `as_of`、提供商和可用性。
- TradingAgents 输出若无法追溯关键事实来源，证据审计员应降低置信度或要求补证。
- TradingAgents 的模拟交易/评分不等同于真实成交能力。

## Fallback

若 TradingAgents 不可运行：

1. CIS 不伪造 TradingAgents 输出。
2. 原 CIS 专家 Agent 作为 `fallback_adapters` 按最小团队原则运行。
3. 专业金融任务仍优先使用可用的 Anthropic Financial Services Skills。
4. 最终输出必须明确标注 `TradingAgents: unavailable/limited`。
