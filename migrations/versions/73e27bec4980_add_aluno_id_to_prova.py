"""Add aluno_id to Prova

Revision ID: 73e27bec4980
Revises: a9c3cbf2a27e
Create Date: 2024-04-18 17:44:56.176323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73e27bec4980'
down_revision = 'a9c3cbf2a27e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('aluno_cursos', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_aluno_cursos_aluno_id', 'aluno', ['aluno_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_aluno_cursos_curso_id', 'curso', ['curso_id'], ['id'], ondelete='CASCADE')

def downgrade():
    with op.batch_alter_table('aluno_cursos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_aluno_cursos_aluno_id', type_='foreignkey')
        batch_op.drop_constraint('fk_aluno_cursos_curso_id', type_='foreignkey')
