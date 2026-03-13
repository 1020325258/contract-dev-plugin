# Spring AI Alibaba Studio & Admin 功能开发指南

## 1. Studio 配置方式

### 1.1 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-studio</artifactId>
    <version>1.1.2.0</version>
</dependency>
```

### 1.2 实现 AgentLoader 接口

创建自定义的 Agent 加载器，注册你的 Agent：

```java
package com.example.agent;

import com.alibaba.cloud.ai.agent.studio.loader.AgentLoader;
import com.alibaba.cloud.ai.graph.agent.Agent;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class MyAgentLoader implements AgentLoader {

    private final ChatClient chatClient;

    public MyAgentLoader(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    @Override
    public List<String> listAgents() {
        return List.of("my_assistant", "code_helper");
    }

    @Override
    public Agent loadAgent(String name) {
        return switch (name) {
            case "my_assistant" -> createAssistantAgent();
            case "code_helper" -> createCodeHelperAgent();
            default -> throw new NoSuchElementException("Agent not found: " + name);
        };
    }

    private Agent createAssistantAgent() {
        return Agent.builder()
            .name("my_assistant")
            .chatClient(chatClient)
            .systemPrompt("你是一个有用的 AI 助手。")
            .build();
    }

    private Agent createCodeHelperAgent() {
        return Agent.builder()
            .name("code_helper")
            .chatClient(chatClient)
            .systemPrompt("你是一个代码助手，帮助用户编写和调试代码。")
            .tools(List.of(new CodeExecutionTool()))
            .build();
    }
}
```

### 1.3 配置文件

```yaml
# application.yml
server:
  port: 8080

spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-max

# Studio 配置（可选）
saa:
  agents:
    source-dir: ./agents  # Agent 源码目录（动态加载）
```

### 1.4 访问调试界面

启动应用后，访问：
```
http://localhost:8080/chatui/index.html
```

---

## 2. Studio 独立模式开发

### 2.1 克隆并配置前端

```bash
# 克隆仓库
git clone https://github.com/alibaba/spring-ai-alibaba.git
cd spring-ai-alibaba/spring-ai-alibaba-studio/agent-chat-ui

# 安装依赖
pnpm install

# 配置环境变量
cp .env.example .env.development.local
```

### 2.2 环境变量配置

```bash
# .env.development.local
NEXT_PUBLIC_API_URL=http://localhost:8080    # 后端地址
NEXT_PUBLIC_APP_NAME=my_assistant            # 默认 Agent 名称
NEXT_PUBLIC_USER_ID=user-001                 # 用户 ID
```

### 2.3 启动开发服务器

```bash
# 启动前端
pnpm dev

# 另一个终端启动后端
cd ../..
./mvnw -pl spring-ai-alibaba-studio spring-boot:run
```

### 2.4 前端自定义开发

#### 修改 API 客户端

```typescript
// src/lib/spring-ai-api.ts
export class SpringAIApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
  }

  async runAgentStream(request: AgentRunRequest): Promise<Response> {
    return fetch(`${this.baseUrl}/run_sse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });
  }
}
```

#### 添加自定义消息类型

```typescript
// src/types/messages.ts
export interface CustomMessage extends BaseMessage {
  messageType: 'custom';
  customData: {
    // 自定义数据
  };
}
```

#### 自定义消息组件

```typescript
// src/components/thread/messages/CustomMessage.tsx
export function CustomMessage({ message }: { message: CustomMessage }) {
  return (
    <div className="custom-message">
      {/* 自定义渲染逻辑 */}
    </div>
  );
}
```

---

## 3. Admin 平台配置

### 3.1 中间件启动

```bash
cd spring-ai-alibaba-admin/docker/middleware
sh run.sh
```

这会启动以下服务：
- MySQL (3306)
- Elasticsearch (9200)
- Nacos (8848)
- Redis (6379)
- RocketMQ (9876, 10911)

### 3.2 模型配置

```yaml
# spring-ai-alibaba-admin-server-start/model-config.yaml

# DashScope 配置
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-max
          temperature: 0.7

# DeepSeek 配置（备选）
# spring:
#   ai:
#     openai:
#       base-url: https://api.deepseek.com
#       api-key: ${DEEPSEEK_API_KEY}
#       chat:
#         options:
#           model: deepseek-chat
```

### 3.3 启动 Admin 服务

```bash
cd spring-ai-alibaba-admin/spring-ai-alibaba-admin-server-start
mvn spring-boot:run
```

### 3.4 启动前端

```bash
cd spring-ai-alibaba-admin/frontend
npm install
cd packages/main
npm run dev
```

访问：`http://localhost:8000`

---

## 4. Prompt 管理开发

### 4.1 创建 Prompt

```bash
POST /api/prompt
Content-Type: application/json

{
  "promptKey": "my-assistant-prompt",
  "name": "My Assistant Prompt",
  "description": "智能助手 Prompt",
  "workspaceId": "default"
}
```

### 4.2 创建 Prompt 版本

```bash
POST /api/prompt/version
Content-Type: application/json

{
  "promptKey": "my-assistant-prompt",
  "version": "v1.0",
  "content": "你是一个{{role}}，请帮助用户解决{{domain}}问题。",
  "variables": [
    {"name": "role", "defaultValue": "AI 助手"},
    {"name": "domain", "defaultValue": "技术"}
  ]
}
```

### 4.3 Prompt 调试

```bash
POST /api/prompt/run
Content-Type: application/json

{
  "promptKey": "my-assistant-prompt",
  "version": "v1.0",
  "variables": {
    "role": "代码专家",
    "domain": "Java 开发"
  },
  "userMessage": "如何优化 Spring Boot 启动速度？"
}
```

### 4.4 Nacos 集成

配置 Agent 应用从 Nacos 加载 Prompt：

```yaml
# Agent 应用配置
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            serverAddr: 127.0.0.1:8848
            username: nacos
            password: nacos
            promptKey: my-assistant-prompt
```

在 Admin 中更新 Prompt 后，Nacos 会自动推送更新到 Agent 应用。

---

## 5. 数据集管理开发

### 5.1 创建数据集

```bash
POST /api/dataset
Content-Type: application/json

{
  "name": "Customer Service Q&A",
  "description": "客服问答数据集",
  "workspaceId": "default"
}
```

### 5.2 导入数据项

```bash
POST /api/dataset/{datasetId}/items
Content-Type: application/json

{
  "items": [
    {
      "input": "如何退款？",
      "expectedOutput": "您可以在订单详情页点击退款按钮...",
      "metadata": {"category": "refund"}
    }
  ]
}
```

### 5.3 从 Trace 创建数据集

```bash
POST /api/dataset/from-trace
Content-Type: application/json

{
  "traceIds": ["trace-001", "trace-002"],
  "datasetName": "Production Traces"
}
```

---

## 6. 评估器开发

### 6.1 创建评估器

```bash
POST /api/evaluator
Content-Type: application/json

{
  "name": "Accuracy Evaluator",
  "type": "llm-based",
  "config": {
    "model": "qwen-max",
    "promptTemplate": "评估以下回答的准确性..."
  }
}
```

### 6.2 自定义评估器

```java
@Component
public class CustomEvaluator implements Evaluator {

    @Override
    public String getName() {
        return "custom-accuracy";
    }

    @Override
    public EvaluationResult evaluate(EvaluationContext context) {
        String expected = context.getExpectedOutput();
        String actual = context.getActualOutput();

        // 自定义评估逻辑
        double score = calculateSimilarity(expected, actual);

        return EvaluationResult.builder()
            .score(score)
            .passed(score >= 0.8)
            .details("相似度: " + score)
            .build();
    }
}
```

---

## 7. 实验管理开发

### 7.1 创建实验

```bash
POST /api/experiment
Content-Type: application/json

{
  "name": "Prompt Comparison Experiment",
  "datasetId": "dataset-001",
  "evaluatorIds": ["eval-001", "eval-002"],
  "config": {
    "promptVersions": ["v1.0", "v1.1"],
    "sampleSize": 100
  }
}
```

### 7.2 运行实验

```bash
POST /api/experiment/{experimentId}/start
```

### 7.3 查看结果

```bash
GET /api/experiment/{experimentId}/results
```

---

## 8. 可观测性配置

### 8.1 Agent 应用集成

添加依赖：

```xml
<dependencies>
    <!-- 可观测性模块 -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-autoconfigure-arms-observation</artifactId>
        <version>{spring.ai.alibaba.version}</version>
    </dependency>

    <!-- Spring Boot Actuator -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>

    <!-- Micrometer OTel 集成 -->
    <dependency>
        <groupId>io.micrometer</groupId>
        <artifactId>micrometer-registry-otlp</artifactId>
    </dependency>
    <dependency>
        <groupId>io.micrometer</groupId>
        <artifactId>micrometer-tracing-bridge-otel</artifactId>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-exporter-otlp</artifactId>
    </dependency>
</dependencies>
```

### 8.2 配置 OTel

```yaml
management:
  otlp:
    tracing:
      export:
        enabled: true
      endpoint: http://admin-server:4318/v1/traces
    metrics:
      export:
        enabled: false
  tracing:
    sampling:
      probability: 1.0
  opentelemetry:
    resource-attributes:
      service:
        name: my-agent-service
        version: 1.0.0

spring:
  ai:
    chat:
      client:
        observations:
          log-prompt: true
    chat:
      observations:
        log-prompt: true
        log-completion: true
    alibaba:
      arms:
        enabled: true
        tool:
          enabled: true
        model:
          capture-input: true
          capture-output: true
```

---

## 9. HitL（人机协作）开发

### 9.1 配置需要审批的工具

```java
@Bean
public ToolCallback sensitiveTool() {
    return ToolCallback.builder()
        .name("delete_file")
        .description("删除文件")
        .inputSchema("""
            {
              "type": "object",
              "properties": {
                "path": {"type": "string", "description": "文件路径"}
              },
              "required": ["path"]
            }
            """)
        .toolExecutor(this::deleteFile)
        .requiresConfirmation(true)  // 需要人工确认
        .build();
}
```

### 9.2 前端处理 HitL

```typescript
// StreamProvider.tsx
const handleToolConfirm = (event: ToolConfirmEvent) => {
  // 显示审批界面
  setToolConfirmEvent(event);
};

const approveTool = (toolCallId: string, approved: boolean) => {
  const feedback: ToolFeedback = {
    id: toolCallId,
    result: approved ? 'APPROVED' : 'REJECTED',
  };

  resumeFeedback(feedback);
  setToolConfirmEvent(null);
};
```

---

## 10. 自定义工作流节点

### 10.1 创建处理器

```java
@Component
public class CustomExecuteProcessor implements ExecuteProcessor {

    @Override
    public String getNodeType() {
        return "custom";
    }

    @Override
    public NodeOutput execute(NodeExecutionContext context) {
        // 获取节点配置
        Map<String, Object> config = context.getNodeConfig();

        // 执行自定义逻辑
        Object result = doCustomLogic(config);

        // 返回输出
        return NodeOutput.of(context.getNodeName(), result);
    }

    private Object doCustomLogic(Map<String, Object> config) {
        // 实现自定义逻辑
        return null;
    }
}
```

### 10.2 注册处理器

```java
@Configuration
public class WorkflowConfig {

    @Bean
    public ExecuteProcessor customProcessor() {
        return new CustomExecuteProcessor();
    }
}
```
