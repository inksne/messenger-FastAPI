"""add chat_id

Revision ID: f5cc543b566b
Revises: 6fcc1dc56af4
Create Date: 2024-12-06 19:52:06.021906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5cc543b566b'
down_revision: Union[str, None] = '6fcc1dc56af4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_chats', sa.Column('chat_id', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'user_chats', ['chat_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user_chats', type_='unique')
    op.drop_column('user_chats', 'chat_id')
    # ### end Alembic commands ###
