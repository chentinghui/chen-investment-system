# CIS 0.3 模块路由

## 总原则

CIS 是唯一用户入口和最终质量控制层。对于股票/上市公司研究，默认先尝试 TradingAgents；专业金融建模再按需调用 Anthropic Financial Services。外部核心不可运行时，才启用 CIS 自写专家作为 fallback adapters。

## 默认路由

| 用户意图 | 默认核心 | 专业增强 | CIS 最终校验 |
|---|---|---|---|
| 一般股票研究、值不值得研究 | TradingAgents 全链路 | Anthropic（如需估值/财报深挖） | 证据门 + 八维评分 |
| 基本面 + 技术 + 新闻 + 情绪综合 | TradingAgents | — | 证据审计 + CIS评分 |
| 多空观点、上涨/下跌逻辑 | TradingAgents Bull/Bear Debate | Anthropic 专业证据（适用时） | 不按多数票；解释冲突 |
| 价值区间、DCF、市场隐含预期 | TradingAgents 作为上下文 | Anthropic `dcf-model` / `comps-analysis` | valuation维度 + 证据门 |
| 财务数据清洗、三表、模型审计 | — | Anthropic `clean-data-xls` / `3-statement-model` / `audit-xls` | 财务口径核验 |
| 业绩前怎么看 | TradingAgents 新闻/市场背景 | Anthropic `earnings-preview` | catalyst/valuation更新 |
| 业绩后论点是否改变 | TradingAgents 通用研究 | Anthropic `earnings-analysis` / `model-update` | 论点证伪 + 评分变化 |
| 买入、卖出、持有、加减仓 | TradingAgents 候选决策 | Anthropic 估值/财报（必要时） | **强制四层交易框架 + 组合门** |
| 宏观事件影响股票 | TradingAgents News Analyst | Anthropic `sector-overview`（适用时） | 宏观→行业→KPI传导 |
| AI/行业主题筛选 | TradingAgents + 可验证数据 | Anthropic `idea-generation` / `sector-overview` | 主题→收入/利润证据 |
| ETF 产品比较 | CIS ETF 模块 | 可用专业资料 | CIS 产品身份/持仓/费用纪律 |
| 跨境 ETF / QDII 溢价 | CIS | — | **CIS 专属溢价纪律** |
| 组合再平衡 | TradingAgents 单标的候选证据 | Anthropic thesis/catalyst（适用时） | **CIS组合数据门** |

## TradingAgents 运行前检查

1. 读取 `tradingagents.md`。
2. 若环境可执行 Python，优先使用 `scripts/run_tradingagents.py --probe-only` 或等价导入检查。
3. 确认模型 provider、API key、数据 provider 和目标市场可用。
4. 历史日期任务检查是否存在前视偏差风险。
5. 记录 `analysis_date`、行情/新闻/情绪来源与 `as_of`。
6. 只有真实执行 `.propagate()` 成功，才可记录 `external_decision_candidate`。
7. 未执行成功时不得把 TradingAgents README、历史输出或聊天记忆包装成本次结果。

## Anthropic 专业 Skill 路由

TradingAgents 的通用分析不能替代以下专业工作：

- DCF / Comps；
- 三表模型 / 模型审计；
- earnings preview / earnings analysis；
- initiating coverage / model update；
- competitive analysis；
- thesis tracker / catalyst calendar。

对应任务按 `anthropic-financial-services.md` 选择最小匹配 Skill，并把结果作为证据回灌 CIS。

## Fallback 路由

若 TradingAgents 为 `upstream_only` / `unavailable` / `blocked`：

1. 不伪造 TradingAgents 决策。
2. 原 CIS 专家 Agent 以 fallback adapter 身份运行。
3. Standard/Deep/Holding Review 仍必须保留证据审计。
4. 专业金融任务仍优先使用可用 Anthropic Skills。
5. 最终输出明确标注 TradingAgents 未实际运行及对置信度的影响。

## 防重叠规则

- TradingAgents Portfolio Manager 只产生候选决策，不拥有 CIS 最终动作权。
- TradingAgents Risk Team 不替代 CIS 的 evidence gate、组合数据门和四层交易纪律。
- TradingAgents Technical Analyst 不替代 CIS 四层交易框架。
- Anthropic 只处理专业金融子问题，不拥有最终动作权。
- CIS 自写专家在 TradingAgents 正常运行时不得重复跑同一职责，除非为验证关键冲突。
- 最终顺序固定为：外部研究证据 → CIS证据审计 → 八维评分 → 四层/组合门（如适用）→ 最终中文研究姿态。
