"""empty message

Revision ID: 950db8d91023
Revises: e3aec6c9b7af
Create Date: 2023-12-23 12:55:22.486901

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '950db8d91023'
down_revision = 'e3aec6c9b7af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notifications')
    # ### end Alembic commands ###
