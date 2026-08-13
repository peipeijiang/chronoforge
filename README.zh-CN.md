<div align="center">

[English](README.md) · [简体中文](README.zh-CN.md)

# ChronoForge

**一个因果优先的 Agent Skill：把超过单次生成时长的源视频，复刻为完整长视频。**

[![Validate](https://img.shields.io/github/actions/workflow/status/peipeijiang/chronoforge/validate.yml?branch=main&style=for-the-badge&label=Validate)](https://github.com/peipeijiang/chronoforge/actions/workflows/validate.yml)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-ChronoForge-6D5AE6?style=for-the-badge)](SKILL.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Languages](https://img.shields.io/badge/Docs-English%20%7C%20中文-1F6FEB?style=for-the-badge)](README.md)

</div>

短视频模型只能生成片段，但故事通常更长。ChronoForge 把源视频编译为证据、不可变的故事真值、锁定参考图、固定时长的生成容器、确定性拼接和分层 QA。它的核心原则是：**故事真值不可变，模型片段只是包装。**

ChronoForge 的目标是“参考锁定的结构与语义复刻”，不承诺逐像素克隆、运动完全一致或身份完全一致；使用者必须拥有源视频与参考素材的相应权利。

## 为什么需要 ChronoForge

机械等分可以保住时长，却会破坏故事。角色可能还戴着口罩，但气味这个原因消失了；垃圾被扔掉了，却没有前因；反应被保留下来，触发反应的动作却被替换了。

ChronoForge 会显式记录：

- 原因 → 可见动作 → 反应 → 结果/回收；
- 跨镜头的人物状态与道具生命周期；
- 不可变的编辑镜头，以及与之分离的模型时长容器；
- 付费视频生成之前的人工参考图锁定闸门；
- L1/L2/L3 三层 QA，以及最早责任层返工；
- 串行付费提交与追加式任务账本。

## 工作原理

```mermaid
flowchart LR
  A["源视频"] --> B["证据分析"]
  B --> C["故事真值<br/>节拍 · 状态 · 道具"]
  C --> D["编辑镜头"]
  D --> E["模型容器"]
  C --> F["参考图设计"]
  F --> G{"人工锁定参考图"}
  G -->|通过| H["付费生成"]
  E --> H
  H --> I["L2 容器 QA"]
  I --> J["FFmpeg 确定性拼接"]
  J --> K["L3 母版 QA"]

  classDef evidence fill:#E8F1FF,stroke:#2F6FEB,color:#102A56;
  classDef truth fill:#FFF4CC,stroke:#B58105,color:#513B00;
  classDef paid fill:#FFE5E5,stroke:#C93C3C,color:#5C1616;
  classDef output fill:#E6F6EA,stroke:#27864A,color:#123F24;
  class A,B evidence;
  class C,D,E,F,G truth;
  class H paid;
  class I,J,K output;
```

即使模型每次只能输出固定 10 秒，编辑时间线仍然是唯一真值。一个 33.1 秒源视频可以提交四个 10 秒任务，实际保留 `10 + 7 + 10 + 6.1` 秒，再按原始故事时长拼回去。

## 快速开始

### 1. 安装 Skill

需要支持 `SKILL.md` 的 Agent 宿主（例如 Codex）、Python 3.10+、`ffmpeg` 和 `ffprobe`。

```bash
git clone https://github.com/peipeijiang/chronoforge.git \
  ~/.agents/skills/chronoforge
```

在 Agent 中提供源视频并调用：

```text
$chronoforge 分析并复刻 /path/to/source.mp4，视频模型每段固定 10 秒
```

### 2. 初始化非付费 Run

在 Skill 目录执行：

```bash
python3 scripts/init_run.py /path/to/source.mp4 \
  --out /path/to/run \
  --provider-clip-seconds 10 \
  --aspect-ratio 9:16
```

这一步只探测并哈希源视频、创建目录和初始化追加式账本，不会调用任何付费模型。

### 3. 编译并验证故事真值

参考 [`assets/story-truth.example.json`](assets/story-truth.example.json) 和 [`assets/timeline.example.json`](assets/timeline.example.json) 填写实际清单，然后验证：

```bash
python3 scripts/validate_story.py /path/to/run/analysis/story-truth.json
python3 scripts/validate_timeline.py /path/to/run/manifests/timeline.json
```

参考图通过 L1 QA 后必须停下来等待人工确认。参考包没有锁定前，不得提交付费视频任务。

### 4. 验证并提交模型任务

当前适配器只允许 UpDrama 的 `gpt-image-2` 与 `omni_flash-10s`。API Key 只能导出到当前 Shell，禁止写入请求或清单。

```bash
export UPDRAMA_API_KEY="<your-key>"

python3 scripts/updrama_runtime.py preflight
python3 scripts/updrama_runtime.py validate assets/omni-request.example.json
```

提交任务会产生费用，因此命令要求显式确认：

```bash
python3 scripts/updrama_runtime.py submit /path/to/run/requests/video/C01.json \
  --run-dir /path/to/run \
  --job-id C01-v1 \
  --confirm-paid I_UNDERSTAND_THIS_IS_PAID

python3 scripts/updrama_runtime.py status <task-id> \
  --run-dir /path/to/run
```

适配器会在 POST 前写入提交意图，在类 Unix 系统上串行创建任务，并记录结果不明的提交，同时拒绝在同一次调用中自动重试。但这不是服务端幂等保证：出现 `unknown_submission` 后，必须先对账，再决定是否人工重提。

### 5. 拼接已验收的容器

若路径写成 `media/containers/...`，请把 assembly 清单放在 Run 根目录，因为相对路径以清单位置为基准。

```bash
cp assets/assembly.example.json /path/to/run/assembly.json
# 先根据实际容器与保留时长修改清单。
python3 scripts/assemble.py /path/to/run/assembly.json
```

拼接器会统一画面尺寸、帧率、像素格式与音频，再裁剪和串联，并输出编码后的 probe 数据，用于核验时长和音视频流。

## 复刻验收契约

| 层级 | 验收内容 | 拒绝或返工条件 |
|---|---|---|
| L1 · 参考图 | 身份、环境、道具状态、角色隔离 | 状态错误、参考污染、故事关键道具缺失 |
| L2 · 原始容器 | 必要节拍与顺序、裁剪点前完成动作、连续性 | 技术合格，但因果倒置或关键动作缺失 |
| L3 · 母版 | 编辑顺序、接缝、音画连续、伏笔回收 | 仅修复拼接问题，绝不因此触发付费重生成 |

返工应定位到最早责任层，每次受控重试只改一个变量。技术通过，不代表故事通过。

## 一个 33 秒案例

ChronoForge 来自一次 33.111723 秒猫咖短视频复刻。早期版本保留了一些可见物，却误解了笑点：员工因为猫砂盆气味戴上口罩，处理排泄物，最后用“咖啡豆”视觉双关收束。原因一旦丢失，口罩、扔垃圾和结尾都会显得莫名其妙。

修正后的拓扑保留原始编辑节拍，并使用四个 10 秒生成容器：

| 容器 | 源视频范围 | 生成时长 | 保留时长 |
|---|---:|---:|---:|
| C01 | 0–10 秒 | 10 秒 | 10 秒 |
| C02 | 10–17 秒 | 10 秒 | 7 秒 |
| C03 | 17–27 秒 | 10 秒 | 10 秒 |
| C04 | 27–33.111723 秒 | 10 秒 | 6.111723 秒 |

多生成的尾部是模型包装开销，不是新的故事内容。短容器必须在裁剪点之前完成动作，之后保持稳定状态。

## 内置工具

| 脚本 | 用途 | 是否付费 |
|---|---|---:|
| `init_run.py` | 探测/哈希源视频并初始化 Run | 否 |
| `validate_story.py` | 拒绝缺少因果或回收关系的故事清单 | 否 |
| `validate_timeline.py` | 检查编辑镜头与模型容器覆盖 | 否 |
| `updrama_runtime.py` | 预检、验证、提交与查询任务 | 仅提交 |
| `assemble.py` | 标准化、裁剪、拼接并探测母版 | 否 |

完整契约位于 [`references/story-compiler.md`](references/story-compiler.md)、[`references/provider-runtime.md`](references/provider-runtime.md) 与 [`references/qa-contract.md`](references/qa-contract.md)。

## 已知限制

- ChronoForge 是 Agent 引导的生产协议，不是一条命令自动克隆视频。
- 源视频语义分析会调用已安装的 `watch` 等分析 Skill，本仓库不内置该能力。
- 当前模型适配器仅针对 UpDrama，运行时契约可能变化；付费前必须执行 `preflight`。
- `status` 会记录结果 URL，但不会自动下载并哈希媒体。
- 拼接器要求每个输入都有视频和音频，采用中心缩放裁切，并输出 H.264/AAC。
- 付费任务文件锁使用 `fcntl`，因此当前适配器面向 macOS 与 Linux。
- 初始化当前只支持 `9:16` 和 `16:9`。

## 许可证

目前尚未选择许可证。源码可以公开查看，但在添加许可证之前，复用需要获得仓库所有者许可。
