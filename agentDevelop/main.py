"""每日瓜分奖池 · 分账校验台（FastAPI + 单页演示）

- GET  /            演示页面
- POST /api/split   同一组输入，分别跑「原始版本」与「修复版本」，并给出三数结论
- POST /api/scan    穷举小规模输入，统计两个版本各有多少组不满足规则
"""

import itertools
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from pool_split import split_pool
from pool_split_original import split_pool as split_pool_original

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="每日瓜分奖池 · 分账校验台")

# 题目里的主反例：100 分 / 6 人权重各 1，原始版本会发出 102 分
DEMO_CASE = {"pool_cents": 100, "weights": {f"u{i}": 1 for i in range(1, 7)}}


class SplitRequest(BaseModel):
    pool_cents: int = Field(..., ge=0, le=1_000_000_000)
    weights: dict[str, int]

    @field_validator("weights")
    @classmethod
    def _check_weights(cls, value: dict[str, int]) -> dict[str, int]:
        if not value:
            raise ValueError("至少需要一个达标用户")
        if any(weight < 0 for weight in value.values()):
            raise ValueError("权重不能为负数")
        return value


class ScanRequest(BaseModel):
    pool_max: int = Field(20, ge=0, le=200, description="奖池从 0 枚举到该值")
    weight_max: int = Field(2, ge=1, le=9, description="单人权重取值范围 1..weight_max")
    users_max: int = Field(4, ge=1, le=6, description="人数从 1 枚举到该值")


def _run(split, pool_cents: int, weights: dict[str, int]) -> dict:
    """跑一次分账，并算出实际和、应有和、差额。"""
    try:
        amounts = split(pool_cents, weights)
    except ValueError as exc:
        return {"error": str(exc)}

    total = sum(amounts.values())
    return {
        "amounts": amounts,
        "total": total,
        "expected": pool_cents,
        "diff": total - pool_cents,  # >0 多发，<0 有人的钱没发出
        "ok": total == pool_cents,
    }


def _ideal(pool_cents: int, weights: dict[str, int]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        total, weights = len(weights), dict.fromkeys(weights, 1)
    return {uid: round(pool_cents * weight / total, 2) for uid, weight in weights.items()}


@app.post("/api/split")
def api_split(req: SplitRequest):
    weights = {uid: int(weight) for uid, weight in req.weights.items()}
    return {
        "pool_cents": req.pool_cents,
        "weights": weights,
        "ideal": _ideal(req.pool_cents, weights),
        "original": _run(split_pool_original, req.pool_cents, weights),
        "fixed": _run(split_pool, req.pool_cents, weights),
    }


@app.post("/api/scan")
def api_scan(req: ScanRequest):
    combos = sum(req.weight_max**n for n in range(1, req.users_max + 1))
    total_cases = combos * (req.pool_max + 1)
    if total_cases > 100_000:
        raise HTTPException(status_code=400, detail=f"组合过多（{total_cases} 组），请调小参数")

    checked = 0
    original_fail = 0
    fixed_fail = 0
    samples: list[dict] = []

    for users in range(1, req.users_max + 1):
        for weights_tuple in itertools.product(range(1, req.weight_max + 1), repeat=users):
            weights = {f"u{i + 1}": w for i, w in enumerate(weights_tuple)}
            for pool_cents in range(req.pool_max + 1):
                checked += 1
                original = _run(split_pool_original, pool_cents, weights)
                fixed = _run(split_pool, pool_cents, weights)
                if not original.get("ok"):
                    original_fail += 1
                    if len(samples) < 5:
                        samples.append(
                            {
                                "pool_cents": pool_cents,
                                "weights": weights,
                                "total": original["total"],
                                "diff": original["diff"],
                            }
                        )
                if not fixed.get("ok"):
                    fixed_fail += 1

    return {
        "checked": checked,
        "original_fail": original_fail,
        "fixed_fail": fixed_fail,
        "samples": samples,
    }


@app.get("/api/case")
def api_case():
    return DEMO_CASE


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
