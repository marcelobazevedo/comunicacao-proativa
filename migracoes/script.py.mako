"""${message}

Revisão: ${up_revision}
Revisão anterior: ${down_revision | comma,n}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}
revisao: str = ${repr(up_revision)}
revisao_anterior: Union[str, Sequence[str], None] = ${repr(down_revision)}
rotulos: Union[str, Sequence[str], None] = ${repr(branch_labels)}
dependencias: Union[str, Sequence[str], None] = ${repr(depends_on)}
revision = revisao
down_revision = revisao_anterior
branch_labels = rotulos
depends_on = dependencias

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
