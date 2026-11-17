# 每日瓜分奖池 · 分账

`split_pool` 不满足「所有人金额之和 == 奖池总额」。下面是反例、修复、测试与两次运行输出。

## 1. 反例（三个数）

| 项 | 值 |
| --- | --- |
| 输入 | `pool_cents = 100`，`weights = {u1..u6: 1}`（100 分给 6 个权重相同的用户） |
| 实际的和 | **102** 分 |
| 应有的和 | **100** 分 |
| 差额 | **+2 分（平台多发）** |

原因：`round(pool_cents * weight / total_weight)` 是逐人取整，每人 16.67 分被四舍五入成 17 分，
6 个人各自向上取整，误差没有地方回收，合计就多出 2 分。反方向同样会错：

| 输入 | 实际的和 | 应有的和 | 差额 |
| --- | --- | --- | --- |
| `pool_cents=100`，3 人权重 1 | 99 | 100 | −1（有人没拿到钱） |
| `pool_cents=3`，5 人权重 1 | 5 | 3 | +2（平台多发） |
| `pool_cents=1`，2 人权重 1 | 0 | 1 | −1（`round(0.5)` 走银行家舍入） |

## 2. 修复：最大余数法

`pool_split.py`，三步，全程整数运算：

1. 按权重算出每人的整数部分：`base[i], r[i] = divmod(pool_cents * w[i], total_weight)`；
2. 剩下 `left = pool_cents - sum(base)`，理论上 `0 <= left < 人数`；
3. 把 `left` 个 1 分，发给小数部分（余数 `r[i]`）最大的 `left` 个人。

因为 `left` 恒小于人数，每人最多被补 1 分，所以：**总额必然相等**，且每人金额与理论值偏差 < 1 分。
不引入浮点，也就没有了 `round()` 那种「0.5 往哪边倒」的隐式行为。

边界约定（写进代码的 `ValueError` / 退化规则）：

| 输入 | 行为 |
| --- | --- |
| `pool_cents = 0` | 全部返回 0 |
| 只有 1 个用户 | 全给他 |
| 权重全为 0 | 退化成均分（避免除零） |
| `pool_cents < 人数` | 余数大的前几人各 1 分，其余 0 分 |
| `weights = {}` | `pool_cents=0` 返回 `{}`；`pool_cents>0` 抛 `ValueError`（没有参与者，不能凭空发钱） |
| 负数奖池 / 负权重 | 抛 `ValueError` |

## 3. 测试与两次运行输出

同一套测试，用 `--impl` 切换被测实现，避免「两套测试各测各的」。

### 3.1 未修改的 `split_pool`（`pool_split_original.py`）——应为失败

```bash
python -m pytest tests --impl=original --tb=short
```

> 为便于阅读，下面省略了回溯里的 `where 5 = sum(...)` 对象地址行，失败项与断言信息未改动。

```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.2.0, pluggy-1.7.0
被测实现: original
rootdir: C:\Users\Asus\Desktop\wuweiTest\agentDevelop
plugins: anyio-4.16.0
collected 6 items

tests\test_pool_split.py FFFF.F                                          [100%]

================================== FAILURES ===================================
____________________________ test_题目反例_金额之和必须等于奖池 _____________________________
tests\test_pool_split.py:22: in test_题目反例_金额之和必须等于奖池
    assert actual == pool_cents, (
E   AssertionError: 输入: pool_cents=100, weights={'u1': 1, 'u2': 1, 'u3': 1, 'u4': 1, 'u5': 1, 'u6': 1}
E     实际的和=102 分，应有的和=100 分，差额=+2 分
E   assert 102 == 100
_______________________________ test_小额奖池比人数还少 ________________________________
tests\test_pool_split.py:34: in test_小额奖池比人数还少
    assert sum(result.values()) == pool_cents, f"实际={sum(result.values())}, 应有={pool_cents}"
E   AssertionError: 实际=5, 应有=3
E   assert 5 == 3
_________________________________ test_极小规模穷举 _________________________________
tests\test_pool_split.py:44: in test_极小规模穷举
    assert sum(result.values()) == pool_cents, (
E   AssertionError: pool_cents=1, weights={'u1': 1, 'u2': 1}, 实际=0
E   assert 0 == 1
__________________________________ test_随机输入 __________________________________
tests\test_pool_split.py:59: in test_随机输入
    assert sum(result.values()) == pool_cents, (
E   AssertionError: pool_cents=106063, weights={'u1': 25, 'u2': 995, 'u3': 240}, 实际=106062
E   assert 106062 == 106063
__________________________________ test_边界输入 __________________________________
tests\test_pool_split.py:83: in test_边界输入
    assert sum(even.values()) == 10, f"权重全 0 时实际={sum(even.values())}, 应有=10"
E   AssertionError: 权重全 0 时实际=0, 应有=10
E   assert 0 == 10
=========================== short test summary info ===========================
FAILED tests/test_pool_split.py::test_题目反例_金额之和必须等于奖池 - Asserti...
FAILED tests/test_pool_split.py::test_小额奖池比人数还少 - AssertionError: 实...
FAILED tests/test_pool_split.py::test_极小规模穷举 - AssertionError: pool_cen...
FAILED tests/test_pool_split.py::test_随机输入 - AssertionError: pool_cents=1...
FAILED tests/test_pool_split.py::test_边界输入 - AssertionError: 权重全 0 时...
========================= 5 failed, 1 passed in 0.07s =========================
```

### 3.2 修改后的 `split_pool`（`pool_split.py`）——应为通过

```bash
python -m pytest tests --impl=fixed --tb=short
```

```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.2.0, pluggy-1.7.0
被测实现: fixed
rootdir: C:\Users\Asus\Desktop\wuweiTest\agentDevelop
plugins: anyio-4.16.0
collected 6 items

tests\test_pool_split.py ......                                          [100%]

============================== 6 passed in 0.04s ==============================
```

## 4. 目录与运行

```text
pool_split_original.py   题目附件原始版本（保持原样，用来跑出失败）
pool_split.py            修复后的 split_pool
tests/conftest.py        --impl 参数：切换被测实现
tests/test_pool_split.py 反例 + 穷举 + 随机 + 边界，共 6 项
main.py                  FastAPI：/api/split、/api/scan、演示页
static/index.html        单页对比演示（同输入跑两版，实时显示差额）
AI说明.md                第 4 项：AI 使用情况
```

```bash
pip install -r requirements.txt
uvicorn main:app --reload      # 打开 http://127.0.0.1:8000
```

页面上可做的事：改奖池和权重 → 并排看两版逐人金额与合计 → 一键穷举扫描，
直接显示「原始版本 319/630 组不满足，修复版本 0/630」。

## 5. 可选项的回答

**覆盖了多少组？** 极小规模穷举 3720 组（pool 0..30 × 人数 1..4 × 权重 1..3）+ 随机 500 组（含大池子、悬殊权重、单人）
+ 边界输入（零奖池、单人、权重全 0、无参与者）；页面上的穷举扫描默认再跑 630 组。
手写几个样例只能证明「存在错误」，穷举和随机才能证明「修复后不存在错误」。

**多出/缺少的几分钱给了谁？** 给了余数最大的那几个人；余数相同时按传入顺序（`sorted` 是稳定排序）。
依据是「误差最小 + 结果可复现」——同一组输入跑一万次，拿钱的人都一样，事后对账查得清。
换成别人当然可行，比如按 uid 字典序，或给当天最先达标的几个人；前提是规则写死、可解释、可复现。

**这段代码还有其他会出错的输入吗？** 有，而且是两个方向都会错：
`round()` 在半分处走「银行家舍入」（`round(0.5) == 0`），小额奖池会漏发；
权重全为 0 时原始版本直接把池子扣下（`total=0` 返回全 0）；
`pool_cents < 人数` 时每人被舍入到 1 分，合计直接超额。

AI 使用情况见 [AI说明.md](AI说明.md)。
