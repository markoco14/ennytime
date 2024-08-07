"""remove type field from shift type list

Revision ID: e24e4c8e0025
Revises: 0b6653486400
Create Date: 2024-07-25 11:46:45.201618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'e24e4c8e0025'
down_revision: Union[str, None] = '0b6653486400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('etime_shift_types', 'type')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('etime_shift_types', sa.Column('type', mysql.VARCHAR(length=255), nullable=False))
    # ### end Alembic commands ###
