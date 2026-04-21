from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import AppError


_DEFAULT_K_RENT = 0.05          # 5% giá bán → giá thuê/ngày
_DEFAULT_K_DEPOSIT = 0.30       # 30% giá bán → tiền cọc
_DEFAULT_D_FLOOR = 1000         # sàn tối thiểu 1.000đ
_DEFAULT_USED_DEMAND_FACTOR = 1.0
_DEFAULT_USED_CAP_RATIO = 1.0
_DEFAULT_P_SELL_NEW = 30000


@dataclass(frozen=True, slots=True)
class PriceRuleSnapshot:
    rule_id: int | None
    version_no: int
    k_rent: float
    k_deposit: float
    d_floor: int
    used_demand_factor: float
    used_cap_ratio: float


def _build_default_rule() -> PriceRuleSnapshot:
    return PriceRuleSnapshot(
        rule_id=None,
        version_no=0,
        k_rent=_DEFAULT_K_RENT,
        k_deposit=_DEFAULT_K_DEPOSIT,
        d_floor=_DEFAULT_D_FLOOR,
        used_demand_factor=_DEFAULT_USED_DEMAND_FACTOR,
        used_cap_ratio=_DEFAULT_USED_CAP_RATIO,
    )


def _validate_rule_sanity(rule: PriceRuleSnapshot) -> None:
    issues: list[dict[str, object]] = []
    if not 0.05 <= rule.k_rent <= 0.95:
        issues.append({"field": "k_rent", "value": rule.k_rent})
    if not 0.1 <= rule.k_deposit <= 3.0:
        issues.append({"field": "k_deposit", "value": rule.k_deposit})
    if rule.k_deposit < rule.k_rent:
        issues.append(
            {
                "field": "k_deposit",
                "value": rule.k_deposit,
                "expected": ">= k_rent",
                "k_rent": rule.k_rent,
            }
        )
    if not 1000 <= rule.d_floor <= 5_000_000:
        issues.append({"field": "d_floor", "value": rule.d_floor})
    if not 0.2 <= rule.used_demand_factor <= 2.0:
        issues.append(
            {"field": "used_demand_factor", "value": rule.used_demand_factor}
        )
    if not 0.2 <= rule.used_cap_ratio <= 1.0:
        issues.append({"field": "used_cap_ratio", "value": rule.used_cap_ratio})

    if issues:
        raise AppError(
            code="PRICE_RULE_SANITY_FAILED",
            message="Active pricing rule failed sanity checks.",
            status_code=status.HTTP_409_CONFLICT,
            details=issues,
        )


async def resolve_active_price_rule(session: AsyncSession) -> PriceRuleSnapshot:
    try:
        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    version_no,
                    k_rent,
                    k_deposit,
                    d_floor,
                    used_demand_factor,
                    used_cap_ratio
                FROM price_rule
                WHERE status = 'active'
                  AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
                  AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP)
                ORDER BY activated_at DESC, id DESC
                LIMIT 1;
                """
            )
        )
    except SQLAlchemyError as exc:
        if "no such table: price_rule" in str(exc).lower():
            return _build_default_rule()
        raise

    row = result.mappings().first()
    if row is None:
        return _build_default_rule()

    resolved = PriceRuleSnapshot(
        rule_id=int(row["id"]),
        version_no=int(row["version_no"]),
        k_rent=float(row["k_rent"]),
        k_deposit=float(row["k_deposit"]),
        d_floor=int(row["d_floor"]),
        used_demand_factor=float(row["used_demand_factor"]),
        used_cap_ratio=float(row["used_cap_ratio"]),
    )
    _validate_rule_sanity(resolved)
    return resolved


def _used_condition_factor(condition_level: int) -> float:
    bounded = max(0, min(condition_level, 100))
    return max(0.2, bounded / 100.0)


def compute_sell_price(
    *,
    condition_level: int,
    p_sell_new: int = _DEFAULT_P_SELL_NEW,
    used_demand_factor: float = _DEFAULT_USED_DEMAND_FACTOR,
    used_cap_ratio: float = _DEFAULT_USED_CAP_RATIO,
) -> int:
    if condition_level >= 100:
        return max(int(p_sell_new), 1000)

    condition_factor = _used_condition_factor(condition_level)
    used_price = int(round(p_sell_new * condition_factor * used_demand_factor))
    capped_price = int(round(p_sell_new * used_cap_ratio))
    return max(min(used_price, capped_price), 1000)


def compute_rent_price(
    *,
    condition_level: int,
    p_sell_new: int = _DEFAULT_P_SELL_NEW,
    k_rent: float = _DEFAULT_K_RENT,
) -> int:
    bounded_condition = max(20, min(condition_level, 100))
    quality_factor = bounded_condition / 100.0
    calculated = int(round(p_sell_new * k_rent * quality_factor))
    return max(calculated, 2000)


def compute_deposit(
    *,
    p_sell_new: int | None = None,
    k_deposit: float = _DEFAULT_K_DEPOSIT,
    d_floor: int = _DEFAULT_D_FLOOR,
    rent_price: int | None = None,
) -> int:
    if p_sell_new is None:
        fallback_rent = max(int(rent_price or 0), 0)
        return max(fallback_rent * 4, d_floor)

    based_on_sell_price = int(round(p_sell_new * k_deposit))
    return max(based_on_sell_price, d_floor)
