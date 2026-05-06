"""add_promotion_and_promotion_item_tables

Revision ID: a1b2c3d4e5f6
Revises: 98a514493ad6
Create Date: 2026-05-06 14:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '98a514493ad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create promotion and promotion_item tables."""
    op.create_table(
        'promotion',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('discount_type', sa.String(length=20), nullable=False),  # 'percent' | 'amount'
        sa.Column('discount_value', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'promotion_item',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),  # 'title' | 'volume'
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotion.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('promotion_id', 'target_type', 'target_id', name='_promo_target_uc'),
    )


def downgrade() -> None:
    """Drop promotion and promotion_item tables."""
    op.drop_table('promotion_item')
    op.drop_table('promotion')
