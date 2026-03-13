# Spring AI Alibaba Studio & Admin 故障排查指南

## 1. 常见问题与解决方案

### 1.1 Studio 前端无法连接后端

#### 症状
- 浏览器控制台显示 CORS 错误
- 前端无法获取 Agent 列表
- SSE 连接立即断开

#### 原因分析
1. CORS 配置不正确
2. 后端服务未启动或端口不匹配
3. 网络防火墙阻止

#### 解决方案

**检查 CORS 配置：**

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
            .allowedOrigins(
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            )
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

**通过配置禁用/启用 CORS：**

```yaml
spring:
  ai:
    alibaba:
      agent:
        studio:
          web:
            cors:
              enabled: true  # 或 false 禁用
```

**验证后端服务状态：**

```bash
# 检查服务是否运行
curl http://localhost:8080/list-apps

# 检查端口占用
lsof -i :8080
```

### 1.2 Agent 列表为空

#### 症状
- `/list-apps` 返回空数组
- 前端无法选择 Agent
- 日志显示 "Agent registry is empty"

#### 原因分析
1. 未实现 AgentLoader 接口
2. AgentLoader 未被 Spring 扫描到
3. Agent 创建过程异常

#### 解决方案

**检查 AgentLoader 实现：**

```java
@Component  // 确保有 @Component 注解
public class MyAgentLoader implements AgentLoader {

    @Override
    public List<String> listAgents() {
        return List.of("my_agent");  // 确保返回非空列表
    }

    @Override
    public Agent loadAgent(String name) {
        // 添加日志帮助调试
        log.info("Loading agent: {}", name);
        try {
            return createAgent(name);
        } catch (Exception e) {
            log.error("Failed to load agent: " + name, e);
            throw new IllegalStateException("Agent load failed", e);
        }
    }
}
```

**检查包扫描配置：**

```java
// 确保你的组件在扫描路径下
@SpringBootApplication(scanBasePackages = {
    "com.alibaba.cloud.ai.agent.studio",  // Studio 模块
    "com.example.myapp"                   // 你的应用包
})
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 1.3 SSE 连接中断

#### 症状
- 流式响应中途停止
- 浏览器显示 "Network Error"
- 后端日志无异常

#### 原因分析
1. 请求超时配置过短
2. 网络代理中断长连接
3. Agent 执行异常未正确返回

#### 解决方案

**增加超时配置：**

```yaml
spring:
  mvc:
    async:
      request-timeout: 300000  # 5 分钟
server:
  servlet:
    encoding:
      charset: UTF-8
      force: true
```

**检查代理配置：**

```nginx
# Nginx 配置需要支持 SSE
location /run_sse {
    proxy_pass http://backend:8080;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
}
```

**Agent 异常处理：**

```java
@PostMapping(value = "/run_sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> agentRunSse(@RequestBody AgentRunRequest request) {
    try {
        Agent agent = agentLoader.loadAgent(request.appName());
        return executeAgent(request, agent)
            .onErrorResume(error -> {
                log.error("Agent execution failed", error);
                return Flux.just(ServerSentEvent.<String>builder()
                    .event("error")
                    .data("{\"error\":\"" + error.getMessage() + "\"}")
                    .build());
            });
    } catch (Exception e) {
        return Flux.error(new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage()));
    }
}
```

### 1.4 HitL 审批无响应

#### 症状
- 工具审批界面显示后，点击无反应
- `/resume_sse` 返回错误
- Agent 无法继续执行

#### 原因分析
1. ToolFeedback 格式不正确
2. threadId 不匹配
3. 会话状态丢失

#### 解决方案

**验证请求格式：**

```typescript
// 正确的 resume 请求格式
const resumeRequest = {
  appName: "my_agent",
  threadId: currentThreadId,  // 必须与原会话一致
  userId: "user-001",
  toolFeedbacks: [{
    id: toolCallId,            // 工具调用 ID
    name: toolName,            // 工具名称
    arguments: toolArgs,       // 工具参数
    result: "APPROVED"         // APPROVED 或 REJECTED
  }]
};
```

**检查会话状态：**

```java
// 确保会话持久化正常
@Service
public class ThreadServiceImpl implements ThreadService {
    // 使用数据库或 Redis 替代内存存储
    // private final Map<String, Thread> threads = new ConcurrentHashMap<>();
}
```

---

## 2. Admin 平台问题排查

### 2.1 中间件连接失败

#### 症状
- 启动时报数据库连接错误
- Elasticsearch 连接超时
- Nacos 注册失败

#### 诊断步骤

```bash
# 检查 MySQL
mysql -h localhost -u root -p
SHOW DATABASES;

# 检查 Elasticsearch
curl http://localhost:9200/_cluster/health

# 检查 Nacos
curl http://localhost:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=10

# 检查 Redis
redis-cli ping

# 检查 RocketMQ
curl http://localhost:8080/cluster/list
```

#### 解决方案

**MySQL 连接问题：**

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/agent_studio?useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: root123
    hikari:
      connection-timeout: 30000
      maximum-pool-size: 10
```

**Elasticsearch 连接问题：**

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
    connection-timeout: 5s
    socket-timeout: 30s
```

### 2.2 Prompt 加载失败

#### 症状
- Agent 应用无法从 Nacos 加载 Prompt
- Prompt 内容为空或过期
- 配置推送不生效

#### 诊断步骤

```bash
# 检查 Nacos 配置是否存在
curl "http://localhost:8848/nacos/v1/cs/configs?dataId=my-agent-prompt&group=DEFAULT_GROUP"

# 检查 Nacos 订阅状态
curl "http://localhost:8848/nacos/v1/cs/configs?dataId=my-agent-prompt&group=DEFAULT_GROUP&tenant="
```

#### 解决方案

**验证配置格式：**

```yaml
# Agent 应用配置
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            serverAddr: 127.0.0.1:8848
            username: nacos        # 确保 username 正确
            password: nacos        # 确保 password 正确
            promptKey: my-prompt   # 确保与 Nacos 中的 dataId 一致
```

**检查 Nacos 命名空间：**

```yaml
spring:
  cloud:
    nacos:
      config:
        namespace: ${NACOS_NAMESPACE:}  # 确保命名空间正确
        group: DEFAULT_GROUP
```

### 2.3 评估实验执行失败

#### 症状
- 实验状态卡在 "running"
- 评估器返回错误
- 数据集加载失败

#### 诊断步骤

```bash
# 查看实验日志
curl "http://localhost:8080/api/experiment/{experimentId}/logs"

# 检查评估器状态
curl "http://localhost:8080/api/evaluator/{evaluatorId}"

# 检查数据集
curl "http://localhost:8080/api/dataset/{datasetId}"
```

#### 解决方案

**检查评估器配置：**

```java
@Component
public class MyEvaluator implements Evaluator {

    @Override
    public EvaluationResult evaluate(EvaluationContext context) {
        try {
            // 添加详细日志
            log.info("Evaluating: input={}, expected={}",
                context.getInput(), context.getExpectedOutput());

            // 执行评估
            double score = doEvaluate(context);

            log.info("Evaluation result: score={}", score);
            return EvaluationResult.builder()
                .score(score)
                .build();
        } catch (Exception e) {
            log.error("Evaluation failed", e);
            return EvaluationResult.builder()
                .score(0.0)
                .error(e.getMessage())
                .build();
        }
    }
}
```

---

## 3. 错误信息解读

### 3.1 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `404 NOT_FOUND` | 资源不存在 | 检查 URL 路径和资源 ID |
| `400 BAD_REQUEST` | 请求参数错误 | 检查请求体格式和必填字段 |
| `500 INTERNAL_SERVER_ERROR` | 服务器内部错误 | 查看后端日志获取详细堆栈 |
| `503 SERVICE_UNAVAILABLE` | 服务不可用 | 检查依赖服务状态 |
| `429 TOO_MANY_REQUESTS` | 请求过于频繁 | 检查限流配置 |

### 3.2 典型错误示例

#### Agent 执行错误

```json
{
  "error": true,
  "errorType": "GraphRunnerException",
  "errorMessage": "Agent execution failed: Tool execution error"
}
```

**解读：** Agent 执行过程中工具调用失败，需要检查：
1. 工具实现是否正确
2. 工具参数是否符合预期
3. 外部服务是否可用

#### 连接超时错误

```
java.net.ConnectException: Connection refused
```

**解读：** 无法连接到目标服务，需要检查：
1. 目标服务是否启动
2. 端口是否正确
3. 防火墙是否放行

---

## 4. 调试技巧

### 4.1 启用调试日志

```yaml
logging:
  level:
    root: INFO
    com.alibaba.cloud.ai: DEBUG
    org.springframework.ai: DEBUG
    io.opentelemetry: DEBUG  # OTel 调试
```

### 4.2 使用 Actuator 端点

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,env,loggers
  endpoint:
    health:
      show-details: always
```

```bash
# 检查健康状态
curl http://localhost:8080/actuator/health

# 查看环境变量
curl http://localhost:8080/actuator/env

# 动态调整日志级别
curl -X POST http://localhost:8080/actuator/loggers/com.alibaba.cloud.ai \
  -H "Content-Type: application/json" \
  -d '{"configuredLevel": "TRACE"}'
```

### 4.3 SSE 流调试

```bash
# 使用 curl 测试 SSE
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8080/run_sse \
  -d '{
    "appName": "my_agent",
    "threadId": "test-thread",
    "userId": "debug-user",
    "newMessage": {"type": "user", "content": "hello"}
  }'
```

### 4.4 前端调试

```typescript
// 在 SpringAIApiClient 中添加日志
class SpringAIApiClient {
  async runAgentStream(request: AgentRunRequest) {
    console.log('[API] Request:', JSON.stringify(request, null, 2));

    const response = await fetch(`${this.baseUrl}/run_sse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });

    console.log('[API] Response status:', response.status);
    console.log('[API] Response headers:', response.headers);

    return response.body;
  }
}
```

---

## 5. 已知限制

### 5.1 Studio 限制

| 限制 | 说明 | 规避方案 |
|------|------|----------|
| 会话存储 | 默认使用内存存储 | 生产环境使用数据库或 Redis |
| 并发限制 | 单实例并发有限 | 水平扩展 + 负载均衡 |
| 文件上传 | 不支持直接文件上传 | 使用外部存储 + URL 传递 |

### 5.2 Admin 限制

| 限制 | 说明 | 规避方案 |
|------|------|----------|
| 数据集大小 | 单个数据集建议 < 10000 条 | 分批处理 |
| 实验并发 | 并行实验数有限 | 增加资源或排队执行 |
| 向量维度 | 依赖 Elasticsearch 限制 | 使用专用向量数据库 |

### 5.3 版本兼容性

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| JDK | 17 | 17+ |
| Spring Boot | 3.2.x | 3.3.x |
| Elasticsearch | 8.0 | 8.12+ |
| Nacos | 2.2 | 2.3+ |
| MySQL | 8.0 | 8.0+ |

---

## 6. 获取帮助

### 6.1 官方资源

- **GitHub Issues**: https://github.com/alibaba/spring-ai-alibaba/issues
- **官方文档**: https://java2ai.com
- **社区论坛**: GitHub Discussions

### 6.2 问题报告模板

```markdown
## 环境信息
- Spring AI Alibaba 版本:
- JDK 版本:
- Spring Boot 版本:
- 操作系统:

## 问题描述
[详细描述问题现象]

## 复现步骤
1. ...
2. ...
3. ...

## 期望行为
[描述期望的正常行为]

## 实际行为
[描述实际的异常行为]

## 日志输出
```
[粘贴相关日志]
```

## 配置文件
```yaml
[粘贴相关配置]
```
```
