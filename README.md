# AI 专家任务雷达（AI Expert Job Radar）

项目目录：`D:\AI专家任务雷达_AI_Expert_Job_Radar`。

面向多模态模型评测、影视视觉美学、视频生成、图像编辑、视频理解标注、数据质量、Rubric、Benchmark 和未来 RL Environment 的每日任务雷达。

## 当前状态
当前版本 v0.2.0。BencherAI、TalentsAI公共机会、MeetChances、Appen访客招募已接通匿名采集。飞书已验证推送。新增腾讯 TLabel 招募入口已登记，接口要求登录。Siriser与CoreXpert待接入，另外3个平台待提供链接。GitHub Actions使用北京时间每天09:00的计划配置，部署结果以Actions运行记录为准。详见 LIVE_STATUS.md。

已登记：Siriser、BencherAI、CoreXpertData、Talents AI、MeetChances Fellow、Appen EliteAI。准确任务页见 config/platforms.json。
2026-11-06 初查：BencherAI 和 EliteAI 返回网页但没有可读正文，其余4个链接在网页工具中无法访问。
这不能证明网站不可用或一定需要登录；公开网页、官方 API、邮件和登录接入方式均待进一步确认。
Siriser 同时保留用户给出的 home 首页和 market 任务页链接。
Python 3.12，仅使用标准库，无第三方安装步骤。在项目根目录运行：

```powershell
python -m unittest discover -s tests -v
python -m radar --demo
python -m radar
```

默认只预览；演示数据明确标识，禁止演示推送，预览不写去重状态。
接入完成后设置当前进程环境变量 FEISHU_WEBHOOK_URL 和可选 FEISHU_SIGNING_SECRET，再运行 python -m radar --send。
.env.example 仅说明变量，不自动加载 .env。不要把凭据粘贴进代码、仓库或日志。

## 结构与扩展
- config/platforms.json：10 个平台接入审核登记。
- config/matching.json：可解释关键词评分，每类仅计一次，总分上限100，默认20分入选。
- radar/collectors.py：Collector 接口与已实现的本地 JSON 导入器。
- radar/core.py：评分、URL去重、飞书文本消息模板。
- radar/feishu.py：HTTPS推送、可选签名、业务响应校验。
- radar/__main__.py：状态、批次、错误隔离。
- tests：去重、评分、失败不提交状态、成功后不重复推荐等测试。

任务格式见 examples/jobs.json，title / description / url 必填，链接必须 HTTPS。
本地导入可配置 method=local_json、path=用户授权导出文件路径、enabled=true。
其他接入方式需要逐个平台实现适配器，不能仅改 method 就宣称已支持。

## 平台接入审核流程
收到每个平台的准确首页及任务页链接后登记：
平台名、官方文档、任务页、接入方式、条款/授权依据、限流、分页、时区、最后审核日期。
优先官方 API；其次允许自动访问的公开网页（审核条款和 robots）；其次用户授权的邮件通知或本地导出。
需登录的平台使用官方授权接口或人工导出。遇验证码、访问控制或禁止自动化，停止并登记原因。
不保存密码或 Cookie，不模拟绕过登录。不凭平台名字猜接口。
已实现四个平台公共列表适配器，包括分页、业务错误检查、关闭状态过滤和岗位ID去重；邮件及其他网站待接入。

## 评分与去重边界
命中类别和分数展示在消息中，关键词匹配用于初筛，不等于资格判断。
地区、语言、报酬、工时等硬性要求待用户补充。首次接入将所有当前匹配条目视为新发现，而非证明当天发布。
按去除跟踪参数的规范 URL 去重；不同平台不同链接的同一职位暂不能可靠识别。
每批推送成功后原子保存 state/sent.json；失败不会确认该批。
推送成功后机器崩溃或响应丢失仍可能重复；Webhook 不提供端到端恰好一次保证。
同一工作目录只运行一个本地进程。

## GitHub 私有仓库 + Actions
在 GitHub 创建空的 Private 仓库，然后在本地人工检查 git status，首次提交并添加远端再推送。
不要上传 .env、state、用户邮件或未经清理的导出数据。当前没有自动提交或发布。
在 Settings → Secrets and variables → Actions 配置：
- Secrets: FEISHU_WEBHOOK_URL；启用签名时再填 FEISHU_SIGNING_SECRET。
- Variables: 完成平台审核和手动验证后，设置 RADAR_ENABLED=true。
工作流通过 RADAR_ENABLED=true 启用。计划为北京时间每天09:00（UTC 01:00），允许手动触发。
定时任务不是精确时钟，可能延迟。只应在受信任私有仓库运行。
Actions cache 保存跨运行去重状态，可能被清理或过期，丢失后可能重复推荐。
正式长期使用建议迁移到持久数据库；本地与云端状态不自动共享。
定时安排、状态保存和Secrets均已预留，但没有真实平台时不可启用。

## 消息模板
AI 专家任务雷达 | AI Expert Job Radar
新增匹配任务：N
分数 | 标题
匹配：类别
任务链接
平台状态：成功读取 / 待审核 / 采集失败
失败不会被解释为没有新任务；没有新增时仍发送每日状态。
机器人若设置关键词，使用 AI Expert Job Radar。

## 待用户提供
剩余4个平台准确链接（最好同时提供任务页）；飞书机器人 Webhook 后续再配置（通过环境变量或 Secrets 设置），
若开启签名则配置签名密钥；后续补充所在地、语言、最低报酬和可投入时间。

参考官方资料：
- https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching

