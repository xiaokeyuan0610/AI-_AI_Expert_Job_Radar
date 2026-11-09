# 独立云端定时入口（尚未部署）

当前只有代码，没有创建云账号、函数或定时触发器，不能把它视为已经自动运行。

独立云定时器 → 本函数调用GitHub手动启动接口 → 现有采集、AI分析和飞书推送。
绕开的是GitHub定时调度，仍使用GitHub执行程序，不能承诺准点到达。

## 部署所需

1. 用户注册并登录云平台，完成平台要求的验证，确认实际计费后再创建资源。
2. 腾讯云SCF事件函数可使用Python运行时，入口设为 `index.main_handler`，上传本目录的 `index.py`。
3. 云端私密环境配置 `GITHUB_REPOSITORY=xiaokeyuan0610/AI-_AI_Expert_Job_Radar`。
4. 私密配置 `GITHUB_DISPATCH_TOKEN`。使用仅限该仓库、Actions写权限的细粒度GitHub令牌，设置有效期。不放代码、聊天或公开变量。
5. 仅添加定时触发器，不开放HTTP入口。在控制台选择每天北京时间09:00，核实时区后再启用，可加09:17和09:37恢复触发。
6. 本函数不需要平台Cookie、飞书Webhook、模型密钥或个人画像。这些继续保存在GitHub Secrets。

## 验收

先用 `{"Type":"Timer"}` 测试事件核对调度，再检查GitHub运行及飞书投递。
返回 `dispatch_accepted` 只说明GitHub接收了启动请求，不等于日报已发送。
必须观察一次真实定时启动并核实飞书投递后，才能标记为已验证的自动发送。

官方参考：
- https://cloud.tencent.cn/document/product/583/9708
- https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
