"""drop owner_id and guest_id fields from db

Revision ID: 9812cf6766a0
Revises: 01c56302efb5
Create Date: 2024-08-24 15:32:11.630611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9812cf6766a0'
down_revision: Union[str, None] = '01c56302efb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### drop unique pair constraint ###
    op.drop_constraint('uix_owner_id_guest_id', table_name='etime_shares', type_='unique')

    # ### drop columns ###
    op.drop_column('etime_shares', 'owner_id')
    op.drop_column('etime_shares', 'guest_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('etime_shares', sa.Column(
        'guest_id', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('etime_shares', sa.Column(
        'owner_id', mysql.INTEGER(), autoincrement=False, nullable=True))

    # Set sender_id and receiver_id to NULL
    op.execute('''
        UPDATE etime_shares
        SET owner_id = sender_id, guest_id = receiver_id
    ''')

    # Alter the columns to be non-nullable
    op.alter_column('etime_shares', 'guest_id', nullable=False,
                    existing_type=mysql.INTEGER())
    op.alter_column('etime_shares', 'owner_id', nullable=False,
                    existing_type=mysql.INTEGER())

    op.create_unique_constraint('uix_owner_id_guest_id', 'etime_shares',
                                ['owner_id', 'guest_id'])
    # ### end Alembic commands ###
