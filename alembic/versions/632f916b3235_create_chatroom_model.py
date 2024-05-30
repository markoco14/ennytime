"""Create ChatRoom model

Revision ID: 632f916b3235
Revises: 11af5294ac59
Create Date: 2024-05-30 23:54:34.274654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '632f916b3235'
down_revision: Union[str, None] = '11af5294ac59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('etime_chat_rooms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.String(length=255), nullable=False),
    sa.Column('chat_users', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_etime_chat_rooms_room_id'), 'etime_chat_rooms', ['room_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_etime_chat_rooms_room_id'), table_name='etime_chat_rooms')
    op.drop_table('etime_chat_rooms')
    # ### end Alembic commands ###
