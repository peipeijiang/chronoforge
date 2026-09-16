# ChronoForge · v3

[English](README.en.md) · [完整 Skill](SKILL.md)

从上传视频复刻、从商品链接创作产品视频，或在商品事实约束下仿拍参考视频。三条路线共用版本化故事、参考图锁定、安全付费执行、L1/L2/L3 和 FFmpeg 装配。

| 输入 | 路线 | 前置工作 |
|---|---|---|
| 上传/本地视频 | recreation | watch 全片取证、原始时间码、音频线索、故事和状态 |
| 商品链接 | product_video | product-ugc 完整采集与视觉认知、卖点证据、原创整片剧情 |
| 商品链接＋上传视频 | hybrid | 两套证据＋明确改编映射，商品事实优先 |

只有提供源视频的路线调用 watch。未知链接先检查页面性质，无法确定时询问。商品评论/竞品研究按需进行，不能把推测写成用户评价或趋势结论。

默认图片为 LK888/upDrama **tt-image-2.5**，已知失败且授权允许时可用 **tt-image-2**。独立视频段用 **omni_flash-10s**，真正连续接拍用 **omni_flash-10s-fl**，特定短段可用 **omni-flash**。新运行不调用老张图片或 VEO；已有媒体不会因此失效。

## 开始

Python 3.10+、FFmpeg/ffprobe；付费运行时面向 macOS/Linux。商品采集使用已安装的 product-ugc-pipeline（不修改它）；源视频分析使用 watch。

```bash
git clone --branch v2 https://github.com/peipeijiang/chronoforge.git
cd chronoforge
python3 scripts/init_run.py /path/source.mp4 --out /path/remake
python3 scripts/init_run.py --product-url 'https://shop.example/product' --duration 30 --out /path/product-run
python3 scripts/init_run.py /path/source.mp4 --product-url 'https://shop.example/product' --duration 30 --out /path/hybrid-run
```

Git 发布分支仍为 v2；新运行契约版本为 v3。旧运行保持兼容，不直接覆盖已有安装的本地修改。

## 制作与验收

先写完整影片/广告，再分配编辑镜头和模型任务；三个独立广告版本不是一条 30 秒广告的三段。保留源片实测 source_range，选择的编辑时间用 editorial_range；商品原创不伪造源片时间。

参考图生成 → L1 实际检查 → 用户锁定 → 编译请求 → 当前供应商契约检查 → 串行创建、并行轮询 → L2 原始片段检查 → FFmpeg 装配与后期文字/声音 → L3 实际交付母版。

模型容器不能替代编辑镜头。新场景引用故事板和身份图；续拍严格引用前段通过 L2 的真实末帧和本段目标末帧。每张图片有有序角色与排除项。快剪细节镜头可以承担说明作用，无需硬编原因和反应。

```bash
python3 scripts/compile_prompt.py --run-dir RUN --plan RUN/manifests/execution-plan.json --job C01 --output RUN/requests/video/C01-v1.json
python3 scripts/updrama_runtime.py preflight --run-dir RUN --models tt-image-2.5 omni_flash-10s
python3 scripts/updrama_runtime.py validate RUN/requests/video/C01-v1.json --ready --run-dir RUN
```

Ready 检查需要真实的能力快照审核记录、参考图 L1 与用户锁定。付费前写提交意图；已知任务复用，结果不明先对账，不盲目重复 POST。运行时不计算账户总预算，批次数量及重试额度按用户授权执行。

白色文字在后期叠加。内置装配器支持 generated/silent 音频，文字/旁白混音需要另行本地编辑并重新 L3。技术测试通过不代表视频语义或商品效果已通过。

## 详细规范与测试

- [三条路线及证据](references/route-workflows.md)
- [整片提示词与引用图](references/prompt-and-reference-contract.md)
- [付费与恢复](references/provider-runtime.md)
- [模型契约](references/updrama-contract.md)
- [分路线 QA](references/qa-contract.md)
- [参考资产与锁定](references/reference-execution.md)
- [装配及交付](references/delivery-and-canary.md)
- [历史 v2 审计](references/v2-restoration-audit.md)

```bash
python3 -m unittest discover -s tests -v
```

测试使用合成素材和模拟服务验证流程、去重、锁定、引用、时间线及装配。真实付费前仍需检查供应商当时能力并完成实际视觉/音频审核。历史案例不包含媒体或有效授权；保留作兼容性样本。
