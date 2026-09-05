"""seed usuarios de teste

Revision ID: 8fd1653c48e2
Revises: 68cfdc5f37c0
Create Date: 2026-09-05 19:44:11.303184

"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8fd1653c48e2'
down_revision: Union[str, Sequence[str], None] = '68cfdc5f37c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Senha padrao dos usuarios de teste (mesma usada nos fixtures de tests/).
SENHA_PADRAO = "SenhaForte#123"

USUARIOS_SEED = [
    {"nome": "Leandro", "email": "leandro@teste.com", "tipo_usuario": "fotografo"},
    {"nome": "Maria", "email": "maria@teste.com", "tipo_usuario": "leigo"},
]

usuario_table = sa.table(
    "usuario",
    sa.column("id", sa.String),
    sa.column("nome", sa.String),
    sa.column("email", sa.String),
    sa.column("senha_hash", sa.String),
    sa.column("tipo_usuario", sa.String),
    sa.column("criado_em", sa.DateTime),
    sa.column("atualizado_em", sa.DateTime),
)


def _hash(senha_plana: str) -> str:
    return bcrypt.hashpw(senha_plana.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def upgrade() -> None:
    """Seed dos usuarios de teste (RF01) para ambiente de dev/QA.

    Idempotente: pula quem ja existir (bancos de dev que ja tiveram
    cadastro manual via API nao devem quebrar a migracao).
    """
    bind = op.get_bind()
    emails = [usuario["email"] for usuario in USUARIOS_SEED]
    ja_existentes = {
        row[0]
        for row in bind.execute(
            sa.select(usuario_table.c.email).where(usuario_table.c.email.in_(emails))
        )
    }

    agora = datetime.now(UTC)
    novos = [
        {
            "id": str(uuid.uuid4()),
            "nome": usuario["nome"],
            "email": usuario["email"],
            "senha_hash": _hash(SENHA_PADRAO),
            "tipo_usuario": usuario["tipo_usuario"],
            "criado_em": agora,
            "atualizado_em": agora,
        }
        for usuario in USUARIOS_SEED
        if usuario["email"] not in ja_existentes
    ]
    if novos:
        op.bulk_insert(usuario_table, novos)


def downgrade() -> None:
    """No-op de proposito.

    upgrade() e idempotente e pula e-mails ja existentes, entao nao da pra
    saber aqui se a linha foi criada por esta migracao ou ja existia antes
    (ex.: cadastro manual via API). Deletar por e-mail e destrutivo demais:
    ja apagou usuarios de teste legitimos numa vez que essa migracao foi
    revertida. Se precisar remover os seeds manualmente, delete por id.
    """
