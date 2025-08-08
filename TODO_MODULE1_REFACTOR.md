# Module1 重构 Todo 清单

目标：前置引导、实时反馈、细粒度与可逆操作、非打断式错误呈现，提升“进入下一步”的转化率与稳定性。

范围：仅 Module1（数据导入与基础配置）与直接关联的子组件/工具类（StatusDisplayWidget、CardiacCycleWidget、LayoutManager、ConfigManager、Session）。

优先级标注：P0 紧急/关键路径，P1 高，P2 中。规模估算：S/M/L。

---

## 1) 实时步骤清单/进度条（P0 / M）

- [x] 在主界面固定位置展示步骤完成度（数据导入、患者信息、舒张末期、收缩末期）。
  - [x] 新建 `StepChecklistWidget` 并集成到 `Module1Widget`。
  - [x] 复用状态计算逻辑，新增 `_get_step_status()` 并在 `_update_interface_state()` 中刷新。
  - [x] 心动周期标记完成后即时刷新（`CardiacCycleWidget.phaseMarked` → `_update_interface_state()`）。
- 关联文件：`tavi_analytics/module1/module1_widget.py`，`tavi_analytics/module1/step_checklist_widget.py`

## 2) 订阅事件自动刷新（P0 / M）

- [x] 订阅 MRML Scene 事件，自动更新状态与按钮可用性，减少“刷新状态”依赖。
  - [x] 监听 `NodeAddedEvent` / `NodeRemovedEvent` / `EndBatchProcessEvent` → `_update_interface_state()` 去抖更新。
  - [x] 已连接 `CardiacCycleWidget.phaseMarked` 实时反映关键相位标记。
- [x] 订阅序列浏览器节点 `NodeModifiedEvent`（选择帧变化/驱动端变化时的必要刷新）。
- [x] 将“刷新状态”降级为“重新检测”（保留为兜底，次要样式，带 tooltip，点击执行自检与完整刷新）。
- [ ] Session 事件总线设计：为患者信息/配置变化提供信号（或在保存入口统一触发）。
- 关联文件：`module1_widget.py`，`cardiac_cycle_widget.py`，`core/session.py`

## 3) CTA 文案与导航解耦（P0 / S）

- [x] 将“进入模块二：瓣膜分割”调整为主 CTA “继续”。
- [x] 在按钮下方以小字显示“已完成 X/4 项”。
- [ ] 如存在流程分支，再提供分支入口（次要按钮或菜单）。
- 关联文件：`module1_widget.py`

## 4) 重置操作细分 + 撤销（P1 / M）

- [ ] 将“重置数据”改为带下拉菜单的分项重置：
  - [ ] 仅清除时相标记
  - [ ] 仅重置患者信息
  - [ ] 全部重置（危险操作，需二次确认）
- [ ] 提供一次性撤销（Undo 1 step），时间窗口内可恢复。
- 关联文件：`module1_widget.py`，`core/session.py`

## 5) 错误/提示横幅（P0 / S）

- [ ] 在 `StatusDisplayWidget` 中新增顶部横幅区域，集中显示最近错误/警告与建议操作。
- [ ] 降低阻断性弹窗（仅在关键不可逆/需确认时弹出）。
- 关联文件：`status_display_widget.py`

## 6) 导入入口明确化 + 结果摘要卡（P1 / M）

- [ ] 导入前：明确入口选项
  - [ ] “从 DICOM 导入”
  - [ ] “从现有场景创建序列”
- [ ] 导入后：在状态区域展示数据摘要卡（患者ID、时间点、序列数量、图像质量/帧数等）。
- [ ] 在摘要卡提供“编辑患者信息”快捷入口。
- 关联文件：`data_loading_dialog.py`，`module1_widget.py`，`status_display_widget.py`

## 7) 无数据空状态 + 懒加载（P1 / M）

- [ ] 在无数据前隐藏/折叠 `CardiacCycleWidget`，显示空状态说明与主 CTA（导入数据）。
- [ ] 数据就绪后再初始化或展开心动周期区域（改善启动性能与心智负担）。
- 关联文件：`module1_widget.py`，`cardiac_cycle_widget.py`

## 8) 可达性与易用性（P2 / S）

- [ ] 完善 Tab 顺序与键盘操作路径；为主要按钮添加快捷键与工具提示。
- [ ] 统一文案与本地化（从字符串硬编码迁移到资源/常量）。
- 关联文件：`module1_widget.py`，`ui/styles.py`，`utils/qt_utils.py`

## 9) 患者信息管理入口一致性（P1 / S）

- [ ] 导入完成后在主界面显著位置提供“编辑患者信息”入口，并在状态中回显关键字段。
- 关联文件：`module1_widget.py`，`status_display_widget.py`

## 10) 进度保存与恢复（P2 / M-L）

- [ ] 自动保存关键配置（导入状态、标记结果、患者信息）。
- [ ] 提供“最近会话/继续上次”入口。
- [ ] 规划数据结构与落盘位置（可复用 `ConfigManager`）。
- 关联文件：`utils/config_manager.py`，`core/session.py`，`module1_widget.py`

---

## 技术与设计一致性（横向）

- [ ] 使用 `LayoutManager/StyleManager` 统一样式，避免局部覆盖冲突。
- [ ] 日志级别与格式统一，所有用户可见错误均通过状态横幅呈现并记录日志。
- [ ] 新增/变更的字符串进入 i18n/常量管理，避免散落硬编码。

---

## 交付验收（Definition of Done）

- [ ] 无需点击“重新检测”即可在导入/标记后实时更新主 CTA 与步骤清单（仅在极端场景使用“重新检测”）。
- [ ] 未满足条件时，主界面能直观看到缺失项与操作入口，无需点“继续”才发现。
- [ ] 重置支持分项与撤销；危险操作需二次确认。
- [ ] 错误主要以横幅方式呈现；弹窗仅用于阻断型确认。
- [ ] 无数据时展现空状态；有数据后显示摘要卡与可操作入口。
- [ ] 所有改动通过现有/新增单元测试或手测用例验证。

---

## 参考文件路径

- `tavi_analytics/module1/module1_widget.py`
- `tavi_analytics/module1/status_display_widget.py`
- `tavi_analytics/module1/cardiac_cycle_widget.py`
- `tavi_analytics/module1/data_loading_dialog.py`
- `tavi_analytics/core/session.py`
- `tavi_analytics/utils/config_manager.py`
- `tavi_analytics/ui/styles.py`
- `tavi_analytics/utils/layout_manager.py`
