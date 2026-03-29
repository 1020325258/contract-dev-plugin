# Studio 前端独立使用指南

## 概述

介绍如何在不引入 spring-ai-alibaba-studio jar 包的情况下，独立使用 Studio 的前端页面连接自定义后端。

## 背景

spring-ai-alibaba-studio 是一个嵌入到 Spring Boot 应用的库模块，通过 `@ComponentScan` 自动注册 Controller。对于不想引入完整 jar 包但希望使用前端 UI 的场景，只需要实现后端 API 接口即可。

## 核心内容

### 1. 前端需要的 API 端点

Studio 前端 (Next.js) 通过 `SpringAIApiClient` 与后端通信，需要实现以下 5 个接口：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/run_sse` | POST | 流式运行智能体 (SSE) |
| `/resume_sse` | POST | 人机协作审批后恢复执行 (SSE) |
| `/apps/{appName}/users/{userId}/threads` | GET | 获取会话列表 |
| `/apps/{appName}/users/{userId}/threads` | POST | 创建会话 |
| `/apps/{appName}/users/{userId}/threads/{id}` | GET | 获取会话详情 |
| `/apps/{appName}/users/{userId}/threads/{id}` | DELETE | 删除会话 |

### 2. 最小实现示例

```java
@RestController
@RequestMapping
public class StudioApiController {

    @PostMapping(value = "/run_sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> runSse(@RequestBody AgentRunRequest request) {
        // 1. 根据 appName 加载你的 Agent
        Agent agent = agentLoader.load(request.getAppName());

        // 2. 调用 agent.stream() 获取流
        RunnableConfig config = RunnableConfig.builder()
            .threadId(request.getThreadId())
            .build();

        Flux<NodeOutput> stream = agent.stream(
            request.getNewMessage().toUserMessage(),
            config
        );

        // 3. 转换为 SSE 格式
        return stream.map(this::toServerSentEvent);
    }

    @PostMapping(value = "/resume_sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> resumeSse(@RequestBody AgentResumeRequest request) {
        // 类似实现，处理人机协作反馈
    }

    // 其他会话管理接口...
}
```

### 3. 依赖引入

不需要引入完整的 studio jar 包，只需引入核心框架：

```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-agent-framework</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

### 4. 前端配置

修改前端环境变量，指向你的后端地址：

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_APP_NAME=your_agent_name
NEXT_PUBLIC_USER_ID=your_user_id
```

### 5. NodeOutput 到 SSE 转换

```java
private Flux<ServerSentEvent<String>> toServerSentEvent(Flux<NodeOutput> stream) {
    return stream.map(nodeOutput -> {
        String node = nodeOutput.node();
        String agentName = nodeOutput.agent();
        Usage tokenUsage = nodeOutput.tokenUsage();

        if (nodeOutput instanceof StreamingOutput<?> streamingOutput) {
            Message message = streamingOutput.message();
            if (message instanceof AssistantMessage am) {
                AgentRunResponse response = new AgentRunResponse(
                    node, agentName, am, tokenUsage, am.getText()
                );
                return ServerSentEvent.builder(
                    Jackson2JsonEncoder.toString(response)
                ).build();
            }
        }
        return ServerSentEvent.builder("{}").build();
    });
}
```

## 注意事项

- **不需要拷贝所有 studio Java 代码**：只需实现 5-6 个 REST 接口
- **核心逻辑**：`agent.stream()` → 转换为 SSE 格式
- **会话管理**：使用 `RunnableConfig.builder().threadId(sessionId)` 关联会话
- **前端**：使用 `agent-chat-ui` 构建的静态资源或独立 Next.js 服务

## 相关链接

- [studio-admin/development-guide.md](./development-guide.md) - Studio 开发指南
- [agent-framework/api-reference.md](../agent-framework/api-reference.md) - Agent API 参考
- [graph-core/api-reference.md](../graph-core/api-reference.md) - Graph API 参考