# 实施验证记录（2026-10-19）

- 本机内部昼白 v0.3 混音只读复测：ffmpeg `volumedetect` 报 sample peak -1.0 dBFS（工具显示一位小数，报告中 -1.02 dBFS 为不同精度/口径），mean_volume -20.3 dB；`ebur128=peak=true` 报 integrated -16.3 LUFS、true peak -1.0 dBFS。输入 SHA-256 为 `a58241e0c5e1d91436e671f26614af9a48895ec8e20bd901bb21b9dea9565921`。未由混音推断同步人声/音乐床差，也未将样本阈值当项目通则。音频可独立复测，但环境缺少系统 `ffprobe`，故完整 `check_media.py` 门禁对该真实视频不能声称 PASS；人工听感与授权也未在本轮重新批准。
- 合成音频单元测试覆盖新版阈值 pass/fail、缺分轨/区间/阈值/工具 blocked、sample peak 与 true peak/LUFS/RMS 口径分离，旧配置和新版 Schema 回归。G1 文本门禁夹具涵盖有声已选/未选/版本变更、无旁白授权 N/A，以及验证档 PASS 不等同于 G3。
- 最小验证范围仅由 Markdown Brief/交付合同表达：旧包 schema 没有增加必填字段，验证档升级后重新核查新范围。两个已有样例包校验结果 PASS。
- `git status --short` 未发现内部测试报告、品牌素材或音视频文件进入仓库；本变更仅提交代码、文档、合成测试及不含素材的结果摘要。未发布。

- 最终验证：`python -m unittest discover -s production-data/tests -q` 共 35 项通过；`examples/valid` 11 条、`examples/advanced-valid` 17 条确定性 PASS；`openspec validate --all --strict` 2 项通过/0 失败；`git diff --check` 无问题；HTML 内部锚点/标记闭合/移动端媒体查询通过。完整真实媒体门禁仍因本机 `ffprobe` 缺失未执行，不能据此认定实际样片 G2/G3 已批准。主规格同步与归档留待独立 OPSX 步骤，本轮未发布。
