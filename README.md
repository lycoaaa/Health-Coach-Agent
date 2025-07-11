# 🏃‍♂️ 健康习惯教练（Health-Coach Agent）

*轻量、本地化、可一键运行的健康智能体：Streamlit + SQLite + DeepSeek LLM*

<img width="2180" height="1199" alt="image" src="https://github.com/user-attachments/assets/e6a885fc-6eff-45c7-ac64-e5342eca6621" />

<img width="2176" height="1078" alt="image" src="https://github.com/user-attachments/assets/216b9c09-c003-4413-b63e-310ba4d21702" />

---

## ✨ 功能亮点

| 层级 | 特色 |
|------|------|
| **前端采集** | - 侧边栏**个人档案**（姓名 / 性别 / 年龄 / 身高 / 体重 / 职业）<br>- **每日打卡**表单（睡眠、饮水、步数、情绪等） |
| **持久化** | - 本地 **SQLite**，无需额外服务<br>- 3 张表：`events / weekly_summary / user_profile` |
| **指标聚合** | - 每天 00:05 自动检测“完整周”并聚合<br>- `metrics.compute_metrics.aggregate_unprocessed_weeks()` |
| **智能反馈** | - DeepSeek Chat API<br>- Prompt 包含个人档案 + 周统计 + WHO 指南<br>- 生成「周度总结 + 3 条行动计划（周期周数 + 动力寄语）」 |
| **可视化** | - KPI 五连卡（睡眠 / 步数 / 情绪 / 运动 / BMI）<br>- 当周 4×日折线 + 最近 4 周双折线<br>- 建议卡片：目标值 + 目标周期 + 动力 emoji |
| **技术栈** | Python 3.11, Streamlit 1.35, Pandas, APScheduler, Pydantic v2, python-dotenv |

---

## 📂 目录结构
```

health-coach-agent/
├─ src/
│  ├─ ui/                    # Streamlit 前端
│  │   ├─ app.py
│  │   ├─ form.py
│  │   ├─ profile\_form.py
│  │   └─ dashboard.py
│  ├─ database/
│  │   └─ db\_adapter.py
│  ├─ metrics/
│  │   └─ compute\_metrics.py
│  ├─ agent/
│  │   ├─ prompt\_templates.py
│  │   ├─ call\_local\_llm.py
│  │   ├─ report\_schema.py
│  │   └─ feedback\_agent.py
│  └─ notification/
│     └─ push.py
├─ scheduler/
│  └─ jobs.py
├─ data/                     # SQLite 数据库
├─ .env.example
└─ README.md

````

---

## 快速上手

编辑 `.env`，填写 **DeepSeek API Key** 及推送信息：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

```

### 运行前端

```bash
streamlit run src/ui/app.py
```

浏览器打开 `http://localhost:8501` →

1. 在侧边栏填写个人档案并保存；
2. 每日几秒钟完成打卡；
3. 一周后点击 **📑 生成本周周报** 按钮即可。

---

## 开发提示

* **绝对导入 + `sys.path` 注入**：`src/ui/app.py` 冒头 3 行已将 `src/` 加入 `sys.path`，保证 Streamlit 可直接 `streamlit run`.
* 想换数据库 → 仅需改 `db_adapter._get_conn()` 即可切换到 DuckDB / Postgres。
* Prompt 与校验 schema 全在 `src/agent/`，方便快速实验。

---

## Road-map

* [ ] 行动计划「打勾完成」+ 完成率统计
* [ ] Apple Health / Google Fit 同步
* [ ] 多用户模式（登录 + 独立数据）
* [ ] 单元测试 & GitHub CI

---

## 贡献

欢迎 Issue / PR！请遵循 Conventional Commits 规范，并在提交前运行 `black`。

---

## License

MIT © 2025 Ray
