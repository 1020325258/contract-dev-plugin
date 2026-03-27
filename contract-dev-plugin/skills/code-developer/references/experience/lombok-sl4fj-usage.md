# Lombok @Slf4j 日志规范

## 概述
项目中日志打印必须使用 Lombok 的 `@Slf4j` 注解配合 `LOGGER` 变量，禁止直接声明 `Logger` 或使用 `log` 变量名。

## 背景
项目使用 Lombok 自动生成日志变量，部分开发者习惯使用 `log` 或自行创建 `Logger`，导致编译失败。

## 正确用法

```java
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class MyService {

    public void doSomething() {
        LOGGER.info("开始处理: {}", param);
        LOGGER.error("处理失败", exception);
    }
}
```

## 错误用法

```java
// ❌ 错误：使用 log 变量名
private static final Logger log = LoggerFactory.getLogger(MyService.class);

// ❌ 错误：自行创建 Logger
private Logger logger = org.slf4j.LoggerFactory.getLogger(MyService.class);
```

## 注意事项
- `@Slf4j` 注解会自动生成 `LOGGER` 变量（不是 `log`）
- 使用 `LOGGER.info/error/warn/debug` 进行日志打印
- 禁止在代码中声明同名的 `log` 或 `Logger` 变量
