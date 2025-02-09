"""add string author_username to messages

Revision ID: cded7a22a306
Revises: 8e18f430758e
Create Date: 2024-12-10 16:20:12.865090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cded7a22a306'
down_revision: Union[str, None] = '8e18f430758e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('author_username', sa.String(length=24), nullable=False))
    op.create_foreign_key(None, 'messages', 'users', ['author_username'], ['username'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.drop_column('messages', 'author_username')
    # ### end Alembic commands ###
