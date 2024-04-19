"""atualizaçao tabelas

Revision ID: c728c6efd378
Revises: 73e27bec4980
Create Date: 2024-04-18 19:45:03.413433

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c728c6efd378'
down_revision = '73e27bec4980'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('prova', schema=None) as batch_op:
        batch_op.add_column(sa.Column('aluno_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prova_aluno', 'aluno', ['aluno_id'], ['id'], ondelete='CASCADE')

def downgrade():
    with op.batch_alter_table('prova', schema=None) as batch_op:
        batch_op.drop_constraint('fk_prova_aluno', type_='foreignkey')
        batch_op.drop_column('aluno_id')

    # ### end Alembic commands ###
