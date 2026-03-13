# Spring AI Alibaba Studio & Admin 部署指南

## 1. Studio 部署

### 1.1 嵌入模式部署（推荐用于开发调试）

#### 步骤 1: 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-studio</artifactId>
    <version>1.1.2.0</version>
</dependency>
```

#### 步骤 2: 实现 AgentLoader

```java
@Component
public class MyAgentLoader implements AgentLoader {
    @Override
    public List<String> listAgents() {
        return List.of("my_agent");
    }

    @Override
    public Agent loadAgent(String name) {
        // 返回你的 Agent 实例
    }
}
```

#### 步骤 3: 启动应用

```bash
./mvnw spring-boot:run
```

#### 步骤 4: 访问调试界面

```
http://localhost:8080/chatui/index.html
```

### 1.2 独立模式部署

#### 前端构建

```bash
cd spring-ai-alibaba-studio/agent-chat-ui

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 生产构建
pnpm build

# 静态导出（用于嵌入模式）
pnpm build:static
```

#### 后端部署

```bash
# 构建后端
cd spring-ai-alibaba-studio
./mvnw clean package -DskipTests

# 运行
java -jar target/spring-ai-alibaba-studio-*.jar
```

#### Docker 部署

```dockerfile
# Dockerfile
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

COPY target/spring-ai-alibaba-studio-*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

```bash
# 构建镜像
docker build -t spring-ai-alibaba-studio:latest .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -e DASHSCOPE_API_KEY=your-api-key \
  spring-ai-alibaba-studio:latest
```

---

## 2. Admin 平台部署

### 2.1 前置条件

- Docker 2.0+
- Docker Compose
- Java 17+
- Maven 3.8+

### 2.2 中间件部署

#### 使用 Docker Compose

```bash
cd spring-ai-alibaba-admin/docker/middleware
sh run.sh
```

#### 手动部署各中间件

**MySQL:**
```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=agent_studio \
  -p 3306:3306 \
  mysql:8.0
```

**Elasticsearch:**
```bash
docker run -d \
  --name elasticsearch \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -p 9200:9200 \
  elasticsearch:8.12.0
```

**Nacos:**
```bash
docker run -d \
  --name nacos \
  -e MODE=standalone \
  -p 8848:8848 \
  nacos/nacos-server:v2.3.0
```

**Redis:**
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7.2
```

**RocketMQ:**
```bash
# NameServer
docker run -d \
  --name rmqnamesrv \
  -p 9876:9876 \
  apache/rocketmq:5.1.0 sh mqnamesrv

# Broker
docker run -d \
  --name rmqbroker \
  -p 10911:10911 \
  -e "NAMESRV_ADDR=rmqnamesrv:9876" \
  apache/rocketmq:5.1.0 sh mqbroker -n rmqnamesrv:9876
```

### 2.3 后端部署

#### 配置模型

```yaml
# spring-ai-alibaba-admin-server-start/model-config.yaml
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-max
```

#### 构建并运行

```bash
cd spring-ai-alibaba-admin

# 构建
./mvnw clean package -DskipTests

# 运行
cd spring-ai-alibaba-admin-server-start
java -jar target/spring-ai-alibaba-admin-server-start-*.jar
```

### 2.4 前端部署

```bash
cd spring-ai-alibaba-admin/frontend

# 安装依赖
npm install

# 开发模式
cd packages/main
npm run dev

# 生产构建
npm run build
```

### 2.5 Docker Compose 完整部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 中间件
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: agent_studio
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  nacos:
    image: nacos/nacos-server:v2.3.0
    environment:
      MODE: standalone
    ports:
      - "8848:8848"

  redis:
    image: redis:7.2
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # Admin 后端
  admin-server:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/agent_studio
      - SPRING_DATA_ELASTICSEARCH_CLUSTER-NODES=elasticsearch:9200
      - SPRING_REDIS_HOST=redis
      - NACOS_SERVER-ADDR=nacos:8848
    depends_on:
      - mysql
      - elasticsearch
      - nacos
      - redis
    ports:
      - "8080:8080"

  # Admin 前端
  admin-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "8000:80"
    depends_on:
      - admin-server

volumes:
  mysql_data:
  es_data:
  redis_data:
```

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f admin-server
```

---

## 3. Kubernetes 部署

### 3.1 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: admin-config
data:
  application.yml: |
    spring:
      datasource:
        url: jdbc:mysql://mysql:3306/agent_studio
      elasticsearch:
        cluster-nodes: elasticsearch:9200
      redis:
        host: redis
      cloud:
        nacos:
          config:
            server-addr: nacos:8848
```

### 3.2 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: admin-secrets
type: Opaque
stringData:
  dashscope-api-key: your-api-key
  mysql-password: root123
```

### 3.3 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: admin-server
  template:
    metadata:
      labels:
        app: admin-server
    spec:
      containers:
      - name: admin-server
        image: spring-ai-alibaba-admin:latest
        ports:
        - containerPort: 8080
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: admin-secrets
              key: dashscope-api-key
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: admin-config
```

### 3.4 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: admin-server
spec:
  selector:
    app: admin-server
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

---

## 4. 生产环境配置

### 4.1 JVM 参数

```bash
java -Xms2g -Xmx4g \
     -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:+HeapDumpOnOutOfMemoryError \
     -jar spring-ai-alibaba-admin-server-start.jar
```

### 4.2 数据库连接池

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
```

### 4.3 Redis 配置

```yaml
spring:
  redis:
    lettuce:
      pool:
        max-active: 16
        max-idle: 8
        min-idle: 2
```

### 4.4 Elasticsearch 配置

```yaml
spring:
  elasticsearch:
    rest:
      connection-timeout: 5000
      read-timeout: 60000
```

---

## 5. 监控与运维

### 5.1 健康检查

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always
```

```bash
# 健康检查
curl http://localhost:8080/actuator/health
```

### 5.2 日志配置

```yaml
logging:
  level:
    root: INFO
    com.alibaba.cloud.ai: DEBUG
  file:
    name: /var/log/admin/application.log
  logback:
    rollingpolicy:
      max-file-size: 100MB
      max-history: 30
```

### 5.3 性能监控

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
  prometheus:
    metrics:
      export:
        enabled: true
```

---

## 6. Agent 应用集成 Admin

### 6.1 添加依赖

```xml
<dependencies>
    <!-- Nacos Agent 代理 -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-agent-nacos</artifactId>
        <version>{version}</version>
    </dependency>

    <!-- 可观测性 -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-autoconfigure-arms-observation</artifactId>
        <version>{version}</version>
    </dependency>

    <!-- Actuator -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>

    <!-- Micrometer OTel -->
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

### 6.2 配置

```yaml
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            serverAddr: ${NACOS_ADDR:127.0.0.1:8848}
            username: nacos
            password: nacos
            promptKey: ${PROMPT_KEY:my-agent}

management:
  otlp:
    tracing:
      export:
        enabled: true
      endpoint: http://${ADMIN_ADDR:localhost}:4318/v1/traces
  tracing:
    sampling:
      probability: 1.0
  opentelemetry:
    resource-attributes:
      service:
        name: ${SERVICE_NAME:my-agent}
        version: 1.0

spring.ai.chat.client.observations.log-prompt: true
spring.ai.chat.observations.log-prompt: true
spring.ai.chat.observations.log-completion: true
spring.ai.alibaba.arms.enabled: true
```

---

## 7. 常见问题排查

### 7.1 前端无法连接后端

检查 CORS 配置：

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
            .allowedOrigins("http://localhost:3000")
            .allowedMethods("*")
            .allowedHeaders("*");
    }
}
```

### 7.2 SSE 连接断开

检查超时配置：

```yaml
server:
  servlet:
    encoding:
      charset: UTF-8
spring:
  mvc:
    async:
      request-timeout: 300000  # 5 分钟
```

### 7.3 Elasticsearch 连接失败

```bash
# 检查 ES 状态
curl http://localhost:9200/_cluster/health

# 检查索引
curl http://localhost:9200/_cat/indices
```

### 7.4 Nacos 配置不生效

```bash
# 检查 Nacos 配置
curl "http://localhost:8848/nacos/v1/cs/configs?dataId=my-agent&group=DEFAULT_GROUP"
```

---

## 8. 安全配置

### 8.1 API Key 认证

```java
@Component
public class ApiKeyAuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request,
                            HttpServletResponse response,
                            Object handler) {
        String apiKey = request.getHeader("X-API-Key");
        if (!isValidApiKey(apiKey)) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }
        return true;
    }
}
```

### 8.2 OAuth2 配置

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
```

### 8.3 数据加密

```java
@Service
public class CryptoService {
    public String encrypt(String plainText) {
        // 使用 AES 加密
    }

    public String decrypt(String cipherText) {
        // 使用 AES 解密
    }
}
```
