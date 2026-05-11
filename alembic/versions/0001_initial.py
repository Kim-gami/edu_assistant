"""initial: jobs, transcripts, quizzes

Revision ID: 0001
Revises:
Create Date: 2026-05-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE job_status AS ENUM ('pending', 'processing', 'done', 'failed')"))
    op.execute(sa.text("""
        CREATE TABLE jobs (
            id BIGSERIAL PRIMARY KEY,
            audio_filename VARCHAR(255) NOT NULL,
            audio_path VARCHAR(500) NOT NULL,
            status job_status NOT NULL DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE transcripts (
            id BIGSERIAL PRIMARY KEY,
            job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            full_text TEXT NOT NULL,
            segments JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (job_id)
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE quizzes (
            id BIGSERIAL PRIMARY KEY,
            job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            quizzes JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS quizzes"))
    op.execute(sa.text("DROP TABLE IF EXISTS transcripts"))
    op.execute(sa.text("DROP TABLE IF EXISTS jobs"))
    op.execute(sa.text("DROP TYPE IF EXISTS job_status"))
