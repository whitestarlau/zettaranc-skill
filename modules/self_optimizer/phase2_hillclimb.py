"""Phase 2 hill-climbing: ratchet + reflex_blacklist + break_signal."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from modules.harness_updater import HarnessUpdater
from modules.self_optimizer.reflex_blacklist import check_all
from modules.self_optimizer.scorer import compute_total_score


@dataclass
class RoundResult:
    """单轮迭代结果."""

    round: int
    old_score: float
    new_score: float
    delta: float
    status: Literal["keep", "revert", "break"]
    violations: list[str]
    proposed_diff: str
    timestamp: str


def check_break_signal(history: list[RoundResult], threshold: float = 2.0) -> bool:
    """连续 2 轮 delta < threshold → True (触发 break)."""
    if len(history) < 2:
        return False
    return abs(history[-1].delta) < threshold and abs(history[-2].delta) < threshold


def _harness_propose(_old_score: float) -> dict:
    """调 HarnessUpdater 生成 Guardrails 更新建议.

    返回结构: {proposed, analysis, execution_log}
    """
    updater = HarnessUpdater()
    analysis = updater.analyze_strategy_performance()
    if not analysis.get("success"):
        return {
            "proposed": [],
            "analysis": {"strategy_stats": []},
            "execution_log": [{"action": "analyze", "status": "failure", "raised": False}],
        }
    updates = updater.generate_guardrails_update(analysis)
    return {
        "proposed": updates.get("updates", []),
        "analysis": analysis,
        "execution_log": [{"action": "analyze", "status": "success", "raised": False}],
    }


def _score_proposal(proposed: dict, old_monthly_stats: dict) -> float:
    """评估提议后的总分."""
    total, _ = compute_total_score("latest", old_monthly_stats, proposed=proposed)
    return total


def run_round(
    round_n: int,
    old_score: float,
    target: str,
    history: list[RoundResult],
) -> RoundResult:
    """单轮迭代: propose → blacklist check → score → ratchet."""
    timestamp = datetime.now().isoformat()
    proposal = _harness_propose(old_score)

    # 1. reflex_blacklist 硬阻断
    blacklist_ctx = {
        **proposal,
        "llm_input": {"contains_harness_output": False},
        "history": [{"status": h.status} for h in history],
        "scoring": {"real_weight": 0.6, "llm_weight": 0.4, "hard_rule_weight": 0.0},
    }
    violations = check_all(blacklist_ctx)
    if violations:
        return RoundResult(
            round=round_n,
            old_score=old_score,
            new_score=old_score,
            delta=0.0,
            status="revert",
            violations=[v.name for v in violations],
            proposed_diff=str(proposal.get("proposed", [])),
            timestamp=timestamp,
        )

    # 2. 评分
    new_score = _score_proposal(proposal, old_monthly_stats={})  # V1 stub monthly_stats

    # 3. ratchet: new > old 才 keep
    delta = new_score - old_score
    status: Literal["keep", "revert"] = "keep" if delta > 0 else "revert"

    result = RoundResult(
        round=round_n,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        status=status,
        violations=[],
        proposed_diff=str(proposal.get("proposed", [])),
        timestamp=timestamp,
    )

    # 4. break signal: 连续 2 轮 delta<2 → 终止迭代
    if check_break_signal(history + [result]):
        result.status = "break"

    return result
