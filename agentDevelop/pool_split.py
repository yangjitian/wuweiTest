"""每日瓜分奖池 —— 分账逻辑（修复版）。

修复思路：最大余数法（Largest Remainder / Hamilton）

1. 先按权重算出每人应得的整数部分（向下取整）；
2. 剩下的几分钱（0 ~ 人数-1）按小数部分从大到小依次补 1 分；
3. 全程 divmod 整数运算，不引入浮点误差。

这样总额恒等于 pool_cents，且每人金额与理论值的偏差不超过 1 分。
"""


def split_pool(pool_cents: int, weights: dict[str, int]) -> dict[str, int]:
    """按贡献权重把当天奖池分给达标用户，返回 {用户: 金额(分)}。

    保证 sum(result.values()) == pool_cents。
    """
    if pool_cents < 0:
        raise ValueError("pool_cents 不能为负数")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("权重不能为负数")
    if not weights:
        if pool_cents == 0:
            return {}
        raise ValueError("没有参与者，无法分配非零奖池")

    # 全员权重为 0 时退化成均分，避免除零；否则按权重分
    shares = dict(weights) if sum(weights.values()) > 0 else dict.fromkeys(weights, 1)
    total = sum(shares.values())

    base: dict[str, int] = {}
    remains: dict[str, int] = {}
    for user_id, weight in shares.items():
        base[user_id], remains[user_id] = divmod(pool_cents * weight, total)

    # 待补的零头：0 <= left < 人数，所以每人最多被补 1 分，不存在重复倾斜
    left = pool_cents - sum(base.values())
    if left:
        # 余数大的先补；余数相同按传入顺序（sorted 是稳定排序），结果可复现
        for user_id in sorted(base, key=lambda uid: -remains[uid])[:left]:
            base[user_id] += 1
    return base
