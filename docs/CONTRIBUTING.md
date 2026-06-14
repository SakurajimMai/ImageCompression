# 贡献指南

感谢你帮助改进 ImageCompression。本文档涵盖工作流、规范与评审期待,
让项目持续可维护。

## 快速检查清单

提交 PR 之前:

- [ ] 测试覆盖了新增行为(`cargo test --all` 全绿)。
- [ ] 代码在 stable 上干净编译(`cargo check --all-targets`)。
- [ ] `cargo fmt -- --check` 通过。
- [ ] `cargo clippy --all-targets -- -D warnings` 通过(无新增 warning)。
- [ ] Commit 信息符合下面的格式。
- [ ] 文档已更新(本 `docs/` 目录、`README.md`、`SKILL.md`,或行内注释)。
- [ ] 未提交任何密钥、凭据或用户专属路径。

## 开发工作流

项目遵循小型、测试驱动的循环:

1. **理解**现有模式。在 `src/core/`、`src/cmd/` 或 `src/tui/` 中找两到
   三个类似特性,模仿其风格。
2. **先写一个失败测试**用于新增行为。仓库已有三个测试文件
   (`src/config_test.rs`、`src/core/compress_tests.rs`、
   `src/core/upload_tests.rs`);把你的测试放在它们旁边。
3. **实现最小**代码让测试通过。
4. **重构**,让测试保持绿色。
5. **提交**,信息要描述清楚。

如果你撞墙,项目规则(根 `CLAUDE.md`)把单问题尝试次数限制为 **3 次**。
三次失败之后,记录已尝试的方法,在代码库或上游项目里找类似实现,并思考
抽象层次是否合适。

## 编码规范

这些是现有代码强制实行的规范。请遵循。

### 风格

- **`cargo fmt`** 使用 rustfmt 默认配置。
- **`cargo clippy --all-targets -- -D warnings`** 作为 lint 关卡。
- 测试和模块级常量初始化之外,任何可能失败的调用都优先用 `?` 而非
  `unwrap()` / `expect()`。
- 错误必须带上下文:用 `anyhow::Context` 或 `anyhow!("...")` 带上文件路径
  / 出错操作。

### 命名

- 模块名使用 snake_case,简短,描述模块做什么(`compress`、`prepare`、
  `scanner`、`upload`、`workflow`)。
- 函数名使用动词 / 动词短语(`plan_operations`、`execute_operations`、
  `effective_config`)。
- 结构体名使用名词(`ScanResult`、`BatchOptions`、`ProxyConfig`)。
- 子命令文件以命令本身命名(`scan.rs`、`prepare.rs`)。

### 模块边界

- `src/main.rs` 应保持小。只做参数解析与分发。
- `src/core/*` 模块除 `std`、`walkdir`、`tempfile`、`image`、`reqwest`、
  `suppaftp`、`ssh2` 等外,**不能依赖 UI / I/O 框架**。没有 `ratatui`,
  没有 `crossterm`。
- `src/tui/*` 是唯一接触 `ratatui` 与 `crossterm` 的地方。
- `src/cmd/*` 是唯一直接打印人类可读输出的人;`src/core/*` 通过返回值与
  进度回调报告结果。

### 回调 vs 全局

进度上报使用传入的闭包(`ProgressFunc`、`Runner`),而不是全局通道或
共享状态。新增长时操作时,遵循同样的模式。

### CLI 参数解析

手写 `match args[i].as_str()` 循环。结构与现有子命令保持一致
(`src/cmd/compress.rs:7` 是规范示例)。

### 错误上报

`src/cmd/*` 子命令:有文件失败时退出码 `1`,参数错误时 `2`(经由 `anyhow`
默认行为,即让错误从 `main` 逃逸)。未经讨论不要引入其他退出码。

## Commit 信息

遵循现有节奏:

```text
<type>: <祈使句摘要>

<可选正文,说明为什么>
```

历史中出现的 `type`:

| 类型 | 何时 |
| --- | --- |
| `feat` | 新增面向用户的功能。 |
| `fix` | 修 bug。 |
| `chore` | 工具链、依赖、内部变更。 |
| `docs` | 仅文档。 |
| `refactor` | 无行为变化的代码变更。 |
| `test` | 仅测试。 |

每个 commit:

- 必须能独立编译(`cargo check --all-targets`)。
- 必须保持测试绿色(`cargo test --all`)。
- 应只涉及一个逻辑关注点。

正文(若存在)说明 *为什么* —— 是什么促成这次改动、为何拒绝其他方案、
任何对未来读 diff 的人有帮助的信息。

## 测试

新增行为时:

1. 找到需要测试的最小单元。
2. 先写失败测试。
3. 让它通过。
4. 看看邻近代码是否缺测试,如果加上很简单就一起补。

在用的模式:

- `tempfile::tempdir()` 用于自包含的文件系统 fixture。
- `assert!(err.to_string().contains("…"))` 用于错误形状断言
  (不要钉住整个错误信息;只钉具有区分度的部分)。
- `compress_directory` / `upload_directory` 上的 `Runner` 与 `ProgressFunc`
  回调是 stub I/O 的接缝。请使用。

## 文档

当改动面向用户时,更新以下文件之一或多个:

- `README.md` / `README_EN.md` —— 快速开始、功能列表、要求。
- `docs/API.md` —— 子命令标志、JSON 事件协议。
- `docs/ARCHITECTURE.md` —— 当模块布局或数据流改变时。
- `docs/DEPLOYMENT.md` —— 当发布 / 构建行为改变时。
- `docs/DEVELOPMENT.md` —— 当开发工作流改变时。
- `skills/image-compression/SKILL.md` —— agent 面向的调用模式。
- 行内注释 —— 解释非显而易见的 *为什么*。

如果不确定改哪一个,默认:面向用户的 CLI 行为改 `docs/API.md`,内部架构
改 `docs/ARCHITECTURE.md`。

## PR 流程

1. **开 PR**,从 topic branch 合并到 `main`。
2. **CI 必须绿**:`check`、`test`、`build` 任务覆盖 Ubuntu / macOS /
   Windows。
3. **一位 reviewer** 对大多数 PR 已经足够。对 `src/core/upload.rs`
   (SigV4 / 代理机制)的大重构或改动,建议多一双眼睛。
4. **Squash-merge** 是 PR 通过后的默认做法,除非 commit 历史本身有意义
   (罕见)。

### Reviewer 看什么

- 改动是否与周围模式一致?
- 新的公开类型与函数是否被测试覆盖?
- JSON 事件协议是否保持向后兼容?(见 `docs/API.md`。)新事件必须是
  增量的。
- 是否新增依赖?若有,理由是否充分且最小化?
- 改动是否被文档化?

## 安全

- 永远不要把凭据提交进仓库,即使是测试。用 `tempfile::tempdir()` 与随机
  字符串。
- 代理与 S3 上传代码携带认证令牌;小心不要打日志。避免 `eprintln!` 输出
  `S3Config` 或 `ProxyConfig`。
- 如果发现安全问题,请私下报告,而不是开公开 issue。

## 不在范围内

- 把 `avifenc` / `cwebp` vendored 进源码。发布流水线拉取它们;让它们留在
  仓库外可减小 clone 体积,并允许通过 `LIBAVIF_VERSION` 升级 AVIF。
- 复活旧 Go + Wails + React 栈。README 与历史记录说得很清楚;请不要恢复
  那条代码路径。
- 没有讨论就新增顶层依赖。当前的依赖图是刻意为之的。

## 有疑问?

开 issue,或查看现有 `docs/` 目录 —— 大多数"我该怎么……"的问题在
[DEVELOPMENT.md](./DEVELOPMENT.md) 或 [API.md](./API.md) 中已有答案。