# wuweiTest

三个后端练习 / 笔试题项目，各自独立可跑，互不依赖。

| 目录 | 题目 | 技术栈 | 入口 |
| --- | --- | --- | --- |
| [`agentDevelop/`](agentDevelop/) | 每日瓜分奖池：修 `split_pool` 的分账误差 | Python 3.12 · FastAPI · pytest | `uvicorn main:app` |
| [`backendExam/demo/`](backendExam/demo/) | Spring Boot 认证：登录换会话，访问受保护的 `Hello World` | Java 21 · Spring Boot 3.2.0 · Spring Security 6.2 · Maven | `mvn spring-boot:run` |
| [`pythonExam/`](pythonExam/) | FastAPI 流式接口：SSE 逐块推送 vs 一次性返回 | Python 3.12 · FastAPI · 原生 JS | `uvicorn main:app` |

---

## 1. agentDevelop —— 每日瓜分奖池 分账

题目给的 `split_pool` 用 `round()` 逐人取整，误差不守恒：100 分分给 6 个权重相同的人，
每人 16.67 分各自进到 17，合计发出 102 分，平台多掏 2 分。

修复用**最大余数法**（Hamilton）：先 `divmod` 取整数部分，再把剩下的零头按余数从大到小
一人补 1 分。全程整数运算，`sum(result) == pool_cents` 恒成立，且每人偏差 < 1 分。

- `pool_split_original.py` 题目原始版本，保持原样，用来跑出失败
- `pool_split.py` 修复版本
- `tests/` 反例 + 穷举 + 随机 + 边界，共 6 项；用 `--impl` 切换被测实现
- `main.py` FastAPI 校验台：`/api/split` 并排跑两版，`/api/scan` 穷举小规模输入
- `AI说明.md` AI 使用记录（提了什么、采纳了什么、怎么验证的）

```bash
cd agentDevelop
pip install -r requirements.txt
python -m pytest tests --impl=original   # 预期 5 failed, 1 passed
python -m pytest tests --impl=fixed      # 预期 6 passed
uvicorn main:app --reload                # http://127.0.0.1:8000
```

页面上把 pool 0..20、人数 1..4、权重 1..2 的 630 组全扫一遍：原始版本 319 组不满足，
修复版本 0 组。

## 2. backendExam/demo —— Spring Boot + Spring Security 认证

- `POST /api/auth/login` 登录建会话，`GET /api/hello` 返回 `Hello World`（需认证）
- Cookie + Session 方案，密码 BCrypt 存储，登录后更换 SessionId 防会话固定
- 未认证返回 401 JSON、无权限返回 403 JSON，不跳登录页
- 只引 `spring-boot-starter-web` + `spring-boot-starter-security`，无 JWT / Lombok

```bash
cd backendExam/demo
mvn spring-boot:run                      # http://localhost:8080
```

演示账号 `test` / `123456`。题目要求 JDK 17，本机只有 11 和 21，因此用 JDK 21
（改 `pom.xml` 的 `<java.version>` 为 17 即可降级，代码不用动）。细节见
[demo/README.md](backendExam/demo/README.md)。

## 3. pythonExam —— FastAPI 流式接口

同一段内置文本，两种传法并排跑，让首字延迟的差异可见。不接 LLM。

| | 流式 SSE | 一次性 JSON |
| --- | --- | --- |
| 首字延迟 | 4 ~ 5 ms | 3078 ms |
| 总耗时 | 3721 ms | 3078 ms |

后端是生成器逐块产出交给 `StreamingResponse`，每轮先查 `request.is_disconnected()`
避免用户关页面后白算；前端把两条流的时间线画在同一个坐标上对比。

```bash
cd pythonExam
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000    # http://127.0.0.1:8000 ，加 ?auto=1 自动开跑
curl -N "http://127.0.0.1:8000/api/stream/medium?delay=0.03"
```

---

## 环境与忽略规则

各项目依赖都不入仓库：Python 的 `.venv/`（46MB / 31MB）、`.idea/`、`__pycache__/`、
Maven 的 `target/` 等均在 `.gitignore` 中。根目录 `.gitignore` 管操作系统垃圾文件、
IDE 配置、日志、密钥；语言相关规则写在各自项目的 `.gitignore` 里。

克隆后按上面各节的 `pip install` / `mvn` 命令重建环境即可。
