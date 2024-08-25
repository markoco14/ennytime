"""remove unique_sender_receiver constraint

change to unique sender_id and unique receiver_id because more accurately reflects the application logic and enforces from the DB level

Revision ID: 5f30b87e029c
Revises: 9812cf6766a0
Create Date: 2024-08-25 13:05:16.421168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f30b87e029c'
down_revision: Union[str, None] = '9812cf6766a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('uix_sender_id_receiver_id', table_name='etime_shares')
    op.drop_index('ix_etime_shares_receiver_id', table_name='etime_shares')
    op.create_index(op.f('ix_etime_shares_receiver_id'), 'etime_shares', ['receiver_id'], unique=True)
    op.drop_index('ix_etime_shares_sender_id', table_name='etime_shares')
    op.create_index(op.f('ix_etime_shares_sender_id'), 'etime_shares', ['sender_id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_etime_shares_sender_id'), table_name='etime_shares')
    op.create_index('ix_etime_shares_sender_id', 'etime_shares', ['sender_id'], unique=False)
    op.drop_index(op.f('ix_etime_shares_receiver_id'), table_name='etime_shares')
    op.create_index('ix_etime_shares_receiver_id', 'etime_shares', ['receiver_id'], unique=False)
    op.create_index('uix_sender_id_receiver_id', 'etime_shares', ['sender_id', 'receiver_id'], unique=True)
    # ### end Alembic commands ###