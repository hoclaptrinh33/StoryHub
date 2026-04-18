from __future__ import annotations


def compute_sell_price(*, condition_level: int) -> int:
    base_price = 30_000
    quality_discount = max(0, 100 - condition_level) * 120
    return max(base_price - quality_discount, 5_000)


def compute_rent_price(*, condition_level: int) -> int:
    base_price = 8_000
    quality_discount = max(0, 100 - condition_level) * 30
    return max(base_price - quality_discount, 2_000)


def compute_deposit(*, rent_price: int) -> int:
    return max(rent_price * 4, 10_000)
