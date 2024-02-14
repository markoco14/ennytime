"""create shifts table

Revision ID: 4ededb06da88
Revises: bea424b65a41
Create Date: 2024-02-14 23:06:38.858846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ededb06da88'
down_revision: Union[str, None] = 'bea424b65a41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('etime_shifts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_etime_shifts_id'), 'etime_shifts', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_etime_shifts_id'), table_name='etime_shifts')
    op.drop_table('etime_shifts')
    # ### end Alembic commands ###
