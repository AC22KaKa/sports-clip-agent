# Sports Clip Agent

从结构化比赛事件流生成篮球集锦的 Python 原型。当前阶段先验证“事件索引 + 规则查询 + FFmpeg 渲染”链路；检测、追踪和事件推理模块提供可替换接口，不包含模型权重或真实视频 CV 推理。

## 阶段状态与精度口径

| 阶段 | 目标 | 当前状态与精度承诺 |
| --- | --- | --- |
| 1. 篮球关键时刻 | 从事件流筛选得分、抢断、盖帽并生成片段 | 已实现查询、规划、清单和渲染；未接入 CV。10 分钟视频至少 3 个正确进球片段是待真实视频与模型接入后的验收目标，当前没有真实视频实测结果。 |
| 2. 篮球球员参与片段 | 基于持球 ID 输出连续时间窗 | 仅提供接口；人工标注 5 个窗口 IoU >= 0.6 是目标，尚未验证。 |
| 3. 足球关键时刻 | 输出进球、点球、角球、黄牌等事件 | 仅提供接口；召回率 >= 80%、每场误报不超过 2 个是目标，尚未验证。 |
| 4. 足球球员参与片段 | 按 PathCRF 或球员轨迹邻近度输出参与时间窗 | 仅提供接口。结果是“参与片段”而非逐次触球，会包含无球跑动，也可能漏掉快速一脚出球。 |

当前实现不宣称任何模型准确率。球员号码 OCR、LLM 事件提议、PathCRF 和真实模型加载均未实现。

## 安装与运行

仅使用 Python 标准库。渲染需要本机安装 FFmpeg，并确保 `ffmpeg`、`ffprobe` 在 PATH 中。

```powershell
cd sports-clip-agent
python -m unittest discover -s tests -v
python cli.py --video match.mp4 --events events.jsonl --query "all scoring plays" --output-dir out --preview
python cli.py --video match.mp4 --events events.jsonl --query "最后5分钟关键时刻" --output-dir out --render
```

`--preview` 和 `--render` 必须且只能指定一个。两种模式都会写出 `clips.json`；预览输出低码率 `preview.mp4`，正式模式输出 `highlights.mp4`。中间切片保存在输出目录的 `preview_segments/` 或 `render_segments/`。事件默认前后各扩 3 秒，可用 `--padding-seconds 0` 关闭。无法解析、跳过的事件行和渲染失败会记录到 `diagnostics.jsonl`，其中包含阶段、时间戳/帧号、原因和是否恢复。

## 事件 JSONL

每行是独立 JSON 对象。帧号从 0 开始，`start_frame` 含首帧、`end_frame` 不含尾帧；置信度范围为 0 到 1。坏行会写入诊断并跳过，其余有效行继续处理。

```json
{"type":"MADE_3PT","start_frame":1200,"end_frame":1230,"confidence":0.94,"player_id":3}
{"type":"STEAL","start_frame":2410,"end_frame":2430,"confidence":0.81}
```

阶段 1 的得分查询接受 `SCORE`、`MADE_2PT`、`MADE_3PT`、`MADE_FT` 等命中类型，不把未命中投篮作为得分。关键时刻查询使用得分、`STEAL` 和 `BLOCK`。支持英文 `all scoring plays`、`last 5 minutes key moments`，以及中文“所有得分回合”“最后5分钟关键时刻”。未知查询会返回可读错误。

## 模块边界

- `cv/detector.py`、`cv/tracker.py`：检测与 ByteTrack/BoT-SORT 适配接口。
- `cv/basketball_events.py`、`cv/soccer_events.py`、`cv/possession.py`：篮球/足球事件与控球推断接口。
- `index/event_index.py`：JSONL 校验、事件过滤和帧窗口合并。
- `agent/query_parser.py`、`agent/clip_planner.py`：查询归一化与带上下文的剪辑清单。
- `render/ffmpeg_renderer.py`：ffprobe 信息读取、切片编码与 MP4 拼接。

可用 `python -m unittest discover -s tests -v` 跑单元测试。FFmpeg 集成测试会临时生成短视频；缺少 FFmpeg/ffprobe 时自动跳过。
