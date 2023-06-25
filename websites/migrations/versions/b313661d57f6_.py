"""empty message

Revision ID: b313661d57f6
Revises: 13a41cdace4a
Create Date: 2023-06-23 21:25:19.886888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b313661d57f6'
down_revision = '13a41cdace4a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('distress_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('time', sa.Time(), nullable=True),
    sa.Column('distress_level', sa.String(length=50), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('distress_log')
    # ### end Alembic commands ###
