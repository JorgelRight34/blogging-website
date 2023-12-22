"""empty message

Revision ID: 70da83f82c54
Revises: faaa40ca5dbc
Create Date: 2023-12-21 19:24:24.140390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70da83f82c54'
down_revision = 'faaa40ca5dbc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_comments')
    op.drop_table('comments')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comments',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('blog_id', sa.INTEGER(), nullable=False),
    sa.Column('date', sa.DATETIME(), nullable=True),
    sa.Column('body', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'blog_id')
    )
    op.create_table('_alembic_tmp_comments',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('blog_id', sa.INTEGER(), nullable=False),
    sa.Column('date', sa.DATETIME(), nullable=False),
    sa.Column('body', sa.TEXT(), nullable=False),
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'blog_id')
    )
    # ### end Alembic commands ###
