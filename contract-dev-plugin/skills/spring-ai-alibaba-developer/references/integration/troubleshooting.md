# Spring AI Alibaba Integration 故障排查

## 1. A2A 相关问题

### 1.1 Agent 注册失败

**症状:**
```
ERROR: Failed to register agent to Nacos
com.alibaba.nacos.api.exception.NacosException: failed to req API
```

**原因分析:**
1. Nacos 服务未启动或不可达
2. 命名空间配置错误
3. 认证信息不正确
4. 网络连接超时

**解决方案:**

```yaml
# 检查 Nacos 连接配置
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          server-addr: ${NACOS_SERVER_ADDR:127.0.0.1:8848}
          username: ${NACOS_USERNAME:nacos}
          password: ${NACOS_PASSWORD:nacos}
          namespace: public  # 确保命名空间正确
```

```bash
# 验证 Nacos 服务状态
curl http://localhost:8848/nacos/v1/console/health

# 检查服务注册列表
curl http://localhost:8848/nacos/v1/ns/instance/list?serviceName=your-agent-name
```

**调试技巧:**

```java
// 添加日志级别
logging:
  level:
    com.alibaba.nacos: DEBUG
    com.alibaba.cloud.ai.a2a: DEBUG
```

---

### 1.2 服务发现失败

**症状:**
```
ERROR: Agent not found: data_analysis_agent
java.util.NoSuchElementException: Agent not found
```

**原因分析:**
1. 目标 Agent 未注册到 Nacos
2. 命名空间或分组不匹配
3. 服务发现未启用

**解决方案:**

```yaml
# 确保服务发现配置正确
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          discovery:
            enabled: true
            group-name: DEFAULT_GROUP  # 与注册端一致
```

```java
// 调试代码：列出所有可发现的 Agent
@Autowired
private AgentCardProvider agentCardProvider;

public void listAvailableAgents() {
    // 使用 Nacos A2A Service 列出服务
    // 检查 Agent 是否注册成功
}
```

---

### 1.3 A2A 调用超时

**症状:**
```
ERROR: Read timed out
java.net.SocketTimeoutException: Read timed out
```

**原因分析:**
1. 目标 Agent 响应时间过长
2. 网络延迟高
3. 超时配置过短

**解决方案:**

```java
// 配置 WebClient 超时
@Bean
public WebClient a2aWebClient() {
    return WebClient.builder()
        .clientConnector(new ReactorClientHttpConnector(
            HttpClient.create()
                .responseTimeout(Duration.ofSeconds(60))  // 增加超时时间
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 10000)
        ))
        .build();
}
```

---

## 2. 内置节点问题

### 2.1 LlmNode 执行失败

**症状:**
```
ERROR: ChatClient is null
java.lang.NullPointerException: chatClient
```

**原因分析:**
1. ChatClient 未正确注入
2. 模型配置错误

**解决方案:**

```java
// 确保 ChatClient 正确构建
@Service
public class WorkflowService {

    private final ChatClient chatClient;
    
    public WorkflowService(ChatClient.Builder chatClientBuilder) {
        // 使用 Builder 构建而不是直接注入
        this.chatClient = chatClientBuilder.build();
    }
    
    public LlmNode createLlmNode() {
        return LlmNode.builder()
            .chatClient(chatClient)  // 确保 chatClient 不为 null
            .systemPromptTemplate("...")
            .build();
    }
}
```

---

### 2.2 流式响应处理问题

**症状:**
```
ERROR: Cannot serialize Flux
org.springframework.core.codec.CodecException
```

**原因分析:**
1. 流式响应未正确处理
2. 序列化配置缺失

**解决方案:**

```java
// 正确处理流式响应
@GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ChatResponse> streamChat(@RequestParam String input) {
    LlmNode node = LlmNode.builder()
        .chatClient(chatClient)
        .stream(true)
        .build();
    
    OverAllState state = OverAllState.builder()
        .withUserInput(input)
        .build();
    
    // 返回 Flux 而不是阻塞
    return node.stream(state);
}
```

---

### 2.3 代码执行节点安全错误

**症状:**
```
ERROR: Code execution blocked
SecurityException: Permission denied
```

**原因分析:**
1. 安全策略限制
2. 执行环境权限不足

**解决方案:**

```java
// 使用 Docker 执行器隔离环境
CodeExecutionConfig config = CodeExecutionConfig.builder()
    .image("python:3.11-slim")  // 使用安全的 Docker 镜像
    .timeout(Duration.ofSeconds(30))
    .memoryLimit("256m")  // 限制内存
    .build();

CodeExecutorNodeAction codeNode = CodeExecutorNodeAction.builder()
    .codeExecutor(new DockerCodeExecutor(config))
    .language(CodeLanguage.PYTHON3)
    .build();
```

---

## 3. 配置相关问题

### 3.1 Nacos 配置加载失败

**症状:**
```
ERROR: Unable to load config from Nacos
com.alibaba.nacos.api.config.ConfigException
```

**原因分析:**
1. Data ID 配置错误
2. 分组配置不匹配
3. 配置格式不正确

**解决方案:**

```yaml
# 检查配置
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            enabled: true
            server-addr: 127.0.0.1:8848
            data-id: agent-config.yaml  # 确保 Data ID 正确
            group: DEFAULT_GROUP        # 确保分组正确
```

```bash
# 验证配置是否存在
curl "http://localhost:8848/nacos/v1/cs/configs?dataId=agent-config.yaml&group=DEFAULT_GROUP"
```

---

### 3.2 配置热更新不生效

**症状:**
配置在 Nacos 中更新后，Agent 行为未改变

**原因分析:**
1. 监听器未配置
2. 配置刷新机制未触发
3. Bean 未重新创建

**解决方案:**

```java
// 添加配置监听器
@NacosConfigListener(dataId = "agent-config.yaml", groupId = "DEFAULT_GROUP")
public void onConfigChange(String newConfig) {
    log.info("Configuration changed, rebuilding agent...");
    // 手动触发重新构建
    AgentVO agentVO = parseConfig(newConfig);
    rebuildAgent(agentVO);
}

// 或使用 @RefreshScope (需要 spring-cloud-starter-alibaba-nacos-config)
@RefreshScope
@Bean
public ReactAgent dynamicAgent() {
    return agentBuilderFactory.createBuilder().build();
}
```

---

## 4. 可观测性问题

### 4.1 追踪信息丢失

**症状:**
```
WARNING: Trace context not propagated
```

**原因分析:**
1. Reactor 上下文传播未配置
2. ObservationThreadLocalAccessor 未注册

**解决方案:**

```yaml
# 确保可观测性配置正确
spring:
  ai:
    alibaba:
      graph:
        observation:
          enabled: true
```

```java
// 自动配置应该已经处理，如需手动配置：
@Bean
public ObservationThreadLocalAccessorRegistrar registrar(
        ObjectProvider<ObservationRegistry> registry) {
    ObservationRegistry observationRegistry = registry.getIfUnique();
    if (observationRegistry != null) {
        ContextRegistry.getInstance()
            .registerThreadLocalAccessor(
                new ObservationThreadLocalAccessor(observationRegistry));
        Hooks.enableAutomaticContextPropagation();
    }
    return new ObservationThreadLocalAccessorRegistrar();
}
```

---

### 4.2 指标未采集

**症状:**
Prometheus 端点无 Agent 相关指标

**原因分析:**
1. MeterRegistry 未配置
2. 指标端点未暴露

**解决方案:**

```yaml
management:
  observations:
    enabled: true
  endpoints:
    web:
      exposure:
        include: prometheus, metrics
  prometheus:
    metrics:
      export:
        enabled: true
```

---

## 5. MCP 集成问题

### 5.1 MCP 连接失败

**症状:**
```
ERROR: Failed to connect to MCP server
org.springframework.web.client.ResourceAccessException
```

**原因分析:**
1. MCP 服务器不可达
2. SSE 连接配置错误
3. 认证失败

**解决方案:**

```yaml
# 检查 MCP 配置
spring:
  ai:
    mcp:
      client:
        enabled: true
        sse:
          connections:
            mcp-server:
              url: http://mcp-server:8080  # 检查 URL 是否正确
              sse-endpoint: sse            # 检查端点
```

```bash
# 验证 MCP 服务器可用性
curl http://mcp-server:8080/sse
```

---

### 5.2 MCP 工具调用失败

**症状:**
```
ERROR: Tool not found: tool_name
```

**原因分析:**
1. 工具未在 MCP 服务器注册
2. 工具名称不匹配

**解决方案:**

```java
// 调试：列出可用工具
@Autowired
private McpSyncClient mcpClient;

public void listAvailableTools() {
    List<ToolDefinition> tools = mcpClient.listTools();
    tools.forEach(tool -> log.info("Available tool: {}", tool.getName()));
}
```

---

## 6. 常见错误信息解读

### 6.1 GraphRunnerException

```
com.alibaba.cloud.ai.graph.exception.GraphRunnerException: Node execution failed
```

**含义:** 工作流节点执行过程中发生错误

**排查步骤:**
1. 检查节点日志获取具体错误
2. 验证节点输入参数
3. 检查依赖服务状态

---

### 6.2 AgentNotFoundException

```
com.alibaba.cloud.ai.graph.exception.AgentNotFoundException: Agent not found: agent_name
```

**含义:** 请求的 Agent 不存在

**排查步骤:**
1. 确认 Agent 已注册
2. 检查 Nacos 服务列表
3. 验证 Agent 名称拼写

---

### 6.3 StateKeyNotFoundException

```
com.alibaba.cloud.ai.graph.exception.StateKeyNotFoundException: Key not found: input
```

**含义:** 工作流状态中找不到指定的键

**排查步骤:**
1. 检查上游节点是否正确设置输出
2. 验证 key 名称匹配
3. 检查条件分支是否正确

---

## 7. 已知限制

### 7.1 A2A 限制

| 限制项 | 说明 |
|--------|------|
| 最大请求大小 | JSON-RPC 请求体限制为 10MB |
| 流式超时 | 长时间无数据流会断开连接 (默认 5 分钟) |
| 并发连接 | 单 Agent 默认最大 100 并发连接 |
| 任务取消 | cancel() 未实现，无法主动取消任务 |
| Agent 类型 | 仅支持 ReactAgent 和 A2aRemoteAgent 作为根 Agent |

### 7.2 节点限制

| 限制项 | 说明 |
|--------|------|
| 代码执行超时 | 默认 30 秒，可配置 (CodeExecutionConfig.timeout) |
| Docker 镜像 | 需要预拉取，不支持自动拉取 |
| 内存限制 | Docker 执行默认 256MB |
| 工作目录 | 需要手动清理临时文件 |
| Java 执行 | 需要配置 classPath 才能使用外部依赖 |

### 7.3 配置限制

| 限制项 | 说明 |
|--------|------|
| Nacos 配置大小 | 单配置文件最大 1MB |
| 热更新延迟 | 配置变更后约 1-3 秒生效 |

### 7.4 GraphAgentExecutor 限制

**限制 1: cancel() 未实现**

```java
// 当前实现：空方法
@Override
public void cancel(RequestContext context, EventQueue eventQueue) throws JSONRPCError {
    // 未实现 - 无法主动取消正在执行的任务
}
```

**解决方案:** 使用超时机制控制任务执行时间

```java
CodeExecutionConfig config = new CodeExecutionConfig()
    .setTimeout(60);  // 60秒后自动超时
```

**限制 2: Agent 类型限制**

```java
// 当前实现只支持两种 Agent 类型
// FIXME: currently only support ReactAgent and A2aRemoteAgent as the root agent
String outputText = result.get().data().containsKey(((BaseAgent)executeAgent).getOutputKey())
    ? String.valueOf(result.get().data().get(((BaseAgent)executeAgent).getOutputKey()))
    : "No output key in result.";
```

**解决方案:** 确保 GraphAgentExecutor 包装的是 ReactAgent 或 A2aRemoteAgent

```java
// 正确用法
@Bean
public GraphAgentExecutor graphAgentExecutor(ReactAgent reactAgent) {
    return new GraphAgentExecutor(reactAgent);
}

// 不支持
@Bean
public GraphAgentExecutor graphAgentExecutor(SequentialAgent sequentialAgent) {
    // 这会导致 "No output key in result" 错误
    return new GraphAgentExecutor(sequentialAgent);
}
```

---

## 8. 代码执行问题

### 8.1 Docker 连接失败

**症状:**
```
ERROR: Error executing code in Docker container
java.lang.RuntimeException: Could not connect to Docker daemon
```

**原因分析:**
1. Docker 服务未启动
2. Docker socket 权限不足
3. Docker host 配置错误

**解决方案:**

```bash
# 检查 Docker 服务状态
docker ps

# 检查 socket 权限
ls -la /var/run/docker.sock

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

```java
// 配置正确的 Docker host
CodeExecutionConfig config = new CodeExecutionConfig()
    .setDockerHost("unix:///var/run/docker.sock")  // Linux/Mac
    // .setDockerHost("tcp://localhost:2375")      // Windows
    .setMaxConnections(100)
    .setConnectionTimeout(30);
```

### 8.2 代码执行超时

**症状:**
```
ERROR: Code execution timeout
java.util.concurrent.TimeoutException
```

**原因分析:**
1. 代码包含无限循环
2. 处理数据量过大
3. 超时设置过短

**解决方案:**

```java
CodeExecutionConfig config = new CodeExecutionConfig()
    .setTimeout(600)  // 增加到 10 分钟
    .setWorkDir("/fast-ssd/workspace");  // 使用更快的存储
```

### 8.3 Java 代码执行失败

**症状:**
```
ERROR: Could not find or load main class
java.lang.ClassNotFoundException
```

**原因分析:**
1. classPath 配置错误
2. 依赖 JAR 未正确挂载
3. 类名与文件名不匹配

**解决方案:**

```java
CodeExecutionConfig config = new CodeExecutionConfig()
    .setDocker("openjdk:17-jdk-slim")
    .setWorkDir("/app/workspace")
    .setClassPath("/app/workspace:/app/libs/*");  // 配置 classPath

// 确保 JAR 文件在工作目录中
FileUtils.copyResourceJarToWorkDir(workDir);
```

### 8.4 工作目录清理

**症状:**
磁盘空间持续增长

**原因分析:**
临时文件未清理

**解决方案:**

```java
// 在 finally 块中清理
try {
    executor.executeCodeBlocks(codeBlocks, config);
} finally {
    // 清理代码文件
    FileUtils.deleteFile(workDir, filename);
    // 清理 JAR 文件 (Java)
    FileUtils.deleteResourceJarFromWorkDir(workDir);
    // 清理整个工作目录
    Files.walk(Path.of(workDir))
        .sorted(Comparator.reverseOrder())
        .forEach(path -> path.toFile().delete());
}
```

---

## 8. 调试技巧

### 8.1 启用详细日志

```yaml
logging:
  level:
    root: INFO
    com.alibaba.cloud.ai: DEBUG
    org.springframework.ai: DEBUG
    com.alibaba.nacos: DEBUG
    io.micrometer: DEBUG
```

### 8.2 使用健康检查

```bash
# 检查应用健康状态
curl http://localhost:8080/actuator/health

# 检查 Nacos 连接状态
curl http://localhost:8080/actuator/nacos-config
```

### 8.3 远程调试

```bash
# 启用远程调试
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 -jar app.jar
```

### 8.4 常用诊断命令

```bash
# 查看 AgentCard
curl http://localhost:8080/.well-known/agent.json | jq

# 测试消息端点
curl -X POST http://localhost:8080/message \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"send_message","params":{"message":{"role":"user","content":"test"}},"id":"1"}'

# 检查 Prometheus 指标
curl http://localhost:8080/actuator/prometheus | grep agent
```

### 8.5 GraphAgentExecutor 调试

```java
// 启用详细日志查看节点输出
logging:
  level:
    com.alibaba.cloud.ai.a2a.core.server.GraphAgentExecutor: DEBUG

// DEBUG 日志会显示被忽略的节点类型输出
// 输出格式: {"data": {...}, "node": "preLlm"}
```

**调试流式输出:**

```java
// 监控流式输出内容
generator.subscribe(
    output -> {
        if (!IGNORE_NODE_TYPE.contains(output.node())) {
            log.info("Node output: {} -> {}", output.node(),
                output instanceof StreamingOutput ?
                ((StreamingOutput) output).chunk() : "non-streaming");
        }
    },
    error -> log.error("Stream error", error),
    () -> log.info("Stream completed")
);
```

**检查 RunnableConfig 传递:**

```java
// 确保 threadId 正确传递
Map<String, Object> metadata = new HashMap<>();
metadata.put("threadId", "session-123");
metadata.put(GraphAgentExecutor.STREAMING_METADATA_KEY, true);

MessageSendParams params = MessageSendParams.builder()
    .message(message)
    .metadata(metadata)
    .build();
```

### 8.6 代码执行调试

```bash
# 检查 Docker 环境
docker info
docker images | grep -E "python|openjdk|node"

# 手动测试容器
docker run --rm -it python:3.11-slim python -c "print('Hello')"

# 检查工作目录权限
ls -la /app/workspace
```

```java
// 调试代码执行过程
logger.info("Executing code in language: {}", language);
logger.info("Work directory: {}", hostWorkDir);
logger.info("Container name: {}", containerName);
logger.info("Timeout: {} seconds", timeout);
```
