# SREmate 测试运行规范

## 概述

SREmate 集成测试依赖外部 MySQL + AI API，耗时较长、消耗 token。按变更范围精确选择测试，避免不必要开销。

## 按变更范围选择测试

| 变更范围 | 运行命令 |
|---------|---------|
| 仅修改单元测试对应的类（引擎、基础设施工具类） | 单元测试命令（见下） |
| 修改 Gateway / Domain / Trigger / 提示词 | `./run-integration-tests.sh` |
| 仅修改文档、YAML 配置、注释 | 无需运行测试 |

## 命令速查

**全量测试（单元 + 集成）**：
```bash
cd /path/to/05-SREmate && ./run-integration-tests.sh
```

**仅单元测试**（无需外部环境，秒级完成）：
```bash
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home \
mvn test -f ../pom.xml -pl 05-SREmate \
  -Dtest="ObservabilityAspectAnnotationTest,ToolExecutionTemplateTest,ToolResultTest,QueryScopeTest,EntityRegistryTest,OntologyQueryEngineTest,PersonalQuoteGatewayTest" \
  -Dsurefire.failIfNoSpecifiedTests=false
```

**仅集成测试**：
```bash
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home \
mvn test -f ../pom.xml -pl 05-SREmate -Dtest="ContractOntologyIT" \
  -Dsurefire.failIfNoSpecifiedTests=false
```

## Git Pre-Commit Hook

已在主仓库配置 pre-commit hook（`.git/hooks/pre-commit`），自动检测 `05-SREmate/src/` 下的 staged 变更：
- 有 src 变更 → 自动运行 `./run-integration-tests.sh`
- 无 src 变更（仅文档/配置）→ 跳过测试，直接提交

**注意**：该 hook 在 `.git/hooks/` 中，git worktree 共享同一套 hooks。

## 测试文件职责（勿创建重复测试）

| 文件 | 职责 |
|------|------|
| `ContractOntologyIT` | 核心集成测试，覆盖所有查询场景，必须全部通过 |
| `OntologyQueryEngineTest` | 单元测试：引擎多跳/多目标逻辑，Mock |
| `PersonalQuoteGatewayTest` | 单元测试：bindType 参数映射规则，Mock |
| `EntityRegistryTest` | 单元测试：YAML 解析和路径查找 |
