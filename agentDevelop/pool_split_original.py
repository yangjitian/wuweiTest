"""每日瓜分奖池 —— 分账逻辑（题目附件原始版本）。

保持原样，仅用于复现问题与对照演示，不要修改本文件：
测试要拿它跑出「失败」的那次输出。
"""


def split_pool(pool_cents: int, weights: dict[str, int]) -> dict[str, int]:
    """按贡献权重把当天奖池分给达标用户，返回 {用户: 金额(分)}。"""
    total_weight = sum(weights.values())
    if total_weight == 0:
        return {user_id: 0 for user_id in weights}

    result: dict[str, int] = {}
    for user_id, weight in weights.items():
        result[user_id] = round(pool_cents * weight / total_weight)
    return result
