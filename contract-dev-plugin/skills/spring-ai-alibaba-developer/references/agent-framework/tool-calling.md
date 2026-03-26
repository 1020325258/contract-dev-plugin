# Spring AI Alibaba Tool Calling 实现机制

## 概述

本文档详细分析 Spring AI Alibaba 框架中工具调用 (Tool Calling) 的实现机制，从用户输入到工具被执行的整体流程。

## 核心流程概览

```
用户输入 → ChatClient → LlmNode → ToolNode → ToolCallback → 执行结果
```

## 关键组件

### 1. ToolCallback 接口

Spring AI 定义的工具回调接口，所有工具实现都基于此接口。

```java
public interface ToolCallback {
    ToolDefinition getToolDefinition();  // 工具定义（名称、描述、参数 Schema）
    String call(String arguments, ToolContext context);  // 执行工具
}
```

**实现类型**:
- `MethodToolCallback`: 基于 `@Tool` 注解方法自动生成
- `AsyncToolCallback`: 异步工具接口（Spring AI Alibaba 扩展）
- `CancellableAsyncToolCallback`: 支持取消的异步工具
- `FunctionToolCallback`: 基于函数接口的工具

### 2. LlmNode (LLM 调用节点)

负责调用大语言模型，判断是否需要执行工具。

**关键方法** (`spring-boot-starters/.../node/LlmNode.java`):

```java
// 注册工具
ChatClient.ChatClientRequestSpec chatClientRequestSpec = chatClient.prompt()
    .toolCallbacks(toolCallbacks)  // 注册工具列表
    .messages(messages)
    .advisors(advisors);

// 调用 LLM
ChatResponse response = buildChatClientRequestSpec(state).call().chatResponse();
```

### 3. ToolNode (工具执行节点)

负责执行 LLM 返回的工具调用。

**核心逻辑** (`spring-boot-starters/.../node/ToolNode.java`):

```java
private ToolResponseMessage executeFunction(AssistantMessage assistantMessage, OverAllState state) {
    List<ToolResponseMessage.ToolResponse> toolResponses = new ArrayList<>();

    for (AssistantMessage.ToolCall toolCall : assistantMessage.getToolCalls()) {
        String toolName = toolCall.name();
        String toolArgs = toolCall.arguments();  // JSON 字符串

        // 查找对应的 ToolCallback
        ToolCallback toolCallback = this.resolve(toolName);

        // 执行工具
        String toolResult = toolCallback.call(toolArgs, new ToolContext(Map.of("state", state)));

        // 构建响应
        toolResponses.add(new ToolResponseMessage.ToolResponse(
            toolCall.id(), toolName, toolResult));
    }
    return ToolResponseMessage.builder().responses(toolResponses).build();
}

// 工具解析
private ToolCallback resolve(String toolName) {
    return toolCallbacks.stream()
        .filter(callback -> callback.getToolDefinition().name().equals(toolName))
        .findFirst()
        .orElseGet(() -> toolCallbackResolver.resolve(toolName));
}
```

### 4. AgentLlmNode (Agent 的 LLM 节点)

Spring AI Alibaba Agent 框架中的 LLM 节点，支持更复杂的工具调用场景。

**关键特性** (`spring-ai-alibaba-agent-framework/.../agent/node/AgentLlmNode.java`):

```java
// 禁用 Spring AI 自动执行工具，由框架自行管理
copiedOptions.setInternalToolExecutionEnabled(false);
```

这样框架可以自己管理工具执行循环，而不是让 Spring AI 自动执行。

## 完整调用链路

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           工具调用完整流程                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

1. 用户输入
   │
   ▼
2. ChatClient.prompt()
   - toolCallbacks: 注册的工具列表
   - messages: 用户消息
   - advisors: 拦截器链
   │
   ▼
3. LlmNode.apply()
   - buildChatClientRequestSpec(): 构建请求
   - toolCallbacks → ToolDefinition (JSON Schema)
   │
   ▼
4. ChatModel.call() → LLM
   │
   ▼
5. LLM 返回 AssistantMessage
   │
   ├─ hasToolCalls = true → 需要调用工具
   │   │
   │   ▼
   │6. ToolNode.apply()
   │   - 遍历每个 ToolCall
   │   - resolve(): 查找 ToolCallback
   │   - toolCallback.call(): 执行工具
   │   - 构建 ToolResponseMessage
   │   │
   │   ▼
   │7. 工具结果添加到消息列表
   │   - messages.add(assistantMessage)
   │   - messages.add(toolResponseMessage)
   │   │
   │   ▼
   │8. 重新调用 LlmNode (循环)
   │   │
   └─ hasToolCalls = false → 直接返回结果
```

## Agent 中的工具循环

`AgentLlmNode` + `AgentToolNode` 配合实现 ReAct 模式的工具循环：

1. **AgentLlmNode**: 调用 LLM，如果返回工具调用则暂停
2. **AgentToolNode**: 执行工具调用，返回结果
3. **循环**: 重新调用 LLM，直到 LLM 返回最终答案

## 核心源码位置

| 组件 | 文件路径 |
|------|----------|
| LlmNode | `spring-boot-starters/.../node/LlmNode.java` |
| ToolNode | `spring-boot-starters/.../node/ToolNode.java` |
| AgentLlmNode | `spring-ai-alibaba-agent-framework/.../agent/node/AgentLlmNode.java` |
| AgentToolNode | `spring-ai-alibaba-agent-framework/.../agent/node/AgentToolNode.java` |
| AsyncToolCallback | `spring-ai-alibaba-agent-framework/.../agent/tool/AsyncToolCallback.java` |
| AgentTool | `spring-ai-alibaba-agent-framework/.../agent/AgentTool.java` |

## 自定义工具示例

```java
public class WeatherTool implements ToolCallback {

    @Override
    public ToolDefinition getToolDefinition() {
        return ToolDefinition.builder()
            .name("weather")
            .description("获取指定城市的天气信息")
            .inputSchema("{\"type\":\"object\",\"properties\":{\"city\":{\"type\":\"string\"}}}")
            .build();
    }

    @Override
    public String call(String arguments, ToolContext context) {
        // 解析参数并执行业务逻辑
        Map<String, Object> args = parseJson(arguments);
        String city = (String) args.get("city");
        return weatherService.getWeather(city);
    }
}
```

## 与 Skill 的区别

| 特性 | Tool | Skill |
|------|------|-------|
| 用途 | 执行具体操作 | 扩展领域知识 |
| 实现 | Java 代码 | Markdown 文档 |
| 调用方式 | LLM 主动调用 | 渐进式披露 |
| 灵活性 | 高 | 低 |

## 注意事项

1. **internalToolExecutionEnabled**: Agent 模式下需设为 false，由框架管理工具循环
2. **工具参数**: 工具参数通过 JSON Schema 定义，LLM 根据此生成调用参数
3. **工具结果**: 工具执行结果会自动添加到消息列表，供下一轮 LLM 调用使用
