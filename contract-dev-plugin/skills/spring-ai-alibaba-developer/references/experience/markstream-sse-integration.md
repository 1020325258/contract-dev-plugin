# markstream-vue 前端与 SAA 后端 SSE 对接踩坑记录

## 概述
记录 markstream-vue 前端与 Spring AI Alibaba 后端进行 SSE 流式对接时遇到的问题和解决方案。

## 背景
在 07-ChatUI 前端项目中，需要将 Vue 3 + markstream-vue 搭建的聊天界面与 06-SRE-Agent 后端对接，实现流式 Markdown 渲染。后端使用 SREAgentGraph 的 `streamMessages()` 方法返回 Flux，通过 SSE 协议推送。

## 核心内容

### 1. SSE 响应格式差异导致前端解析失败

**问题现象：**
- 后端返回 `data:内容`（无空格），但前端检查 `data: `（有空格）
- 所有 chunk 被跳过，前端无任何输出
- Console 显示 "Skipping: not starts with data:"

**原因分析：**
后端使用 `ServerSentEvent.builder(text).build()` 时，直接输出 `data:内容`，没有额外空格。前端 useChat.ts 原本写的是：
```typescript
if (!line.startsWith('data: ')) continue  // 期望有空格
const chunk = line.slice(6)  // 去掉 "data: "（6个字符）
```

**解决方案：**
```typescript
// 改用无空格检查
if (!line.startsWith('data:')) continue
// 去掉 "data:"（5个字符）
const chunk = line.slice(5).trim()
```

### 2. 重复订阅导致 Agent 执行两次

**问题现象：**
- 后端日志显示 Agent 执行了两次
- 前端收到重复的 SSE 数据

**原因分析：**
在 Controller 中额外调用了一次 `.subscribe()`：
```java
messageFlux.doOnNext(...).subscribe();  // 第一次订阅（副作用）
return messageFlux...  // 第二次订阅（返回给 Spring）
```
Flux 是惰性的，两次订阅会导致两次执行。

**解决方案：**
移除手动订阅，只使用 Spring 返回的 Flux：
```java
return messageFlux
    .doOnNext(...)  // 只添加副作用，不订阅
    .filter(...)
    .map(...)
```

### 3. CORS 配置导致 403 错误

**问题现象：**
- 前端请求返回 403 Forbidden

**解决方案：**
在 Controller 上添加 `@CrossOrigin` 注解：
```java
@RestController
@CrossOrigin(origins = "http://localhost:5173")
public class ChatController { ... }
```

### 4. SSE 响应 Content-Type 设置

**正确的设置：**
```java
@PostMapping(value = "/stream", produces = "text/event-stream;charset=UTF-8")
public Flux<ServerSentEvent<String>> stream(...) { ... }
```

注意：使用 `Flux<String>` 时 Spring 会自动处理，但 `Flux<ServerSentEvent>` 需要手动设置 Content-Type。

## 注意事项
- Vite 开发服务器的 proxy 配置目标端口必须与后端端口一致（默认 8090）
- SSE 连接是长连接，前端需要正确处理 ReadableStream
- 后端异常时需要在 Flux 中使用 `onErrorResume` 处理，避免整个流中断

## 相关链接
- [SSE 前端处理机制](./studio-admin/sse-frontend-mechanism.md)
- [Studio 系统设计](./studio-admin/system-design.md)