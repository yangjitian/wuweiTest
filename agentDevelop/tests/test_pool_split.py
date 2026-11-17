"""split_pool 的规则测试。

同一份测试，用 --impl 切换被测实现：
    python -m pytest tests -q --impl=original   # 应失败
    python -m pytest tests -q --impl=fixed      # 应通过
"""

import itertools
import random

import pytest


def test_题目反例_金额之和必须等于奖池(under_test):
    """题目要求的那组输入：100 分分给 6 个权重相同的用户。"""
    pool_cents = 100
    weights = {f"u{i}": 1 for i in range(1, 7)}

    result = under_test(pool_cents, weights)
    actual = sum(result.values())

    assert actual == pool_cents, (
        f"输入: pool_cents={pool_cents}, weights={weights}\n"
        f"实际的和={actual} 分，应有的和={pool_cents} 分，差额={actual - pool_cents:+d} 分"
    )


def test_小额奖池比人数还少(under_test):
    """3 分分给 5 个人，向下取整会有人拿 0，向上取整会多分。"""
    pool_cents = 3
    weights = {f"u{i}": 1 for i in range(1, 6)}

    result = under_test(pool_cents, weights)
    assert sum(result.values()) == pool_cents, f"实际={sum(result.values())}, 应有={pool_cents}"


def test_极小规模穷举(under_test):
    """穷举 pool 0..30 × 人数 1..4 × 权重 1..3，共 3720 组，不依赖手写样例。"""
    for users in range(1, 5):
        for combo in itertools.product((1, 2, 3), repeat=users):
            weights = {f"u{i + 1}": w for i, w in enumerate(combo)}
            for pool_cents in range(31):
                result = under_test(pool_cents, weights)
                assert sum(result.values()) == pool_cents, (
                    f"pool_cents={pool_cents}, weights={weights}, "
                    f"实际={sum(result.values())}"
                )


def test_随机输入(under_test):
    """随机 500 组，覆盖大池子、悬殊权重、单人等组合。"""
    rng = random.Random(20261117)
    for _ in range(500):
        users = rng.randint(1, 8)
        weights = {f"u{i + 1}": rng.randint(1, 1000) for i in range(users)}
        pool_cents = rng.randint(0, 500_000)

        result = under_test(pool_cents, weights)
        assert sum(result.values()) == pool_cents, (
            f"pool_cents={pool_cents}, weights={weights}, 实际={sum(result.values())}"
        )


def test_每人金额与理论值偏差不超过1分(under_test):
    """除了总额相等，还要分得公平：不能把零头全砸给一个人。"""
    pool_cents = 10_000
    weights = {"a": 1, "b": 1, "c": 1, "d": 7, "e": 13}
    total = sum(weights.values())

    result = under_test(pool_cents, weights)
    for user_id, weight in weights.items():
        ideal = pool_cents * weight / total
        assert abs(result[user_id] - ideal) < 1, f"{user_id} 拿到 {result[user_id]}，理论应为 {ideal:.2f}"


def test_边界输入(under_test):
    """零奖池、单人、权重全为 0、没有参与者。"""
    assert sum(under_test(0, {"a": 1, "b": 2}).values()) == 0
    assert under_test(7, {"solo": 5}) == {"solo": 7}

    # 全员权重为 0：退化成均分（10 分给 2 人各 5 分），不能出现除零
    even = under_test(10, {"a": 0, "b": 0})
    assert sum(even.values()) == 10, f"权重全 0 时实际={sum(even.values())}, 应有=10"

    assert under_test(0, {}) == {}
    with pytest.raises(ValueError):
        under_test(100, {})  # 没有参与者却要分钱，只能拒绝，不能凭空发钱
