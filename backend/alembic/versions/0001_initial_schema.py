"""0001 Initial Schema for Peblo TV Mini

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-19 10:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='editor'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'editor')", name='chk_user_role'),
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. shows table
    op.create_table(
        'shows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('section', sa.String(length=50), nullable=True),
        sa.Column('categories', sa.JSON(), nullable=False),
        sa.Column('synopsis', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'published')", name='chk_show_status'),
        sa.CheckConstraint("section IS NULL OR section IN ('featured', 'series', 'minisodes', 'songs')", name='chk_show_section'),
    )
    op.create_index('ix_shows_id', 'shows', ['id'], unique=False)
    op.create_index('ix_shows_title', 'shows', ['title'], unique=False)
    op.create_index('ix_shows_slug', 'shows', ['slug'], unique=True)
    op.create_index('ix_shows_section', 'shows', ['section'], unique=False)
    op.create_index('ix_shows_status', 'shows', ['status'], unique=False)
    op.create_index('ix_show_section_status', 'shows', ['section', 'status'], unique=False)

    # 3. seasons table
    op.create_table(
        'seasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('show_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('season_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('show_id', 'season_number', name='uq_show_season_number'),
        sa.CheckConstraint('season_number >= 0', name='chk_season_number_non_negative'),
    )
    op.create_index('ix_seasons_id', 'seasons', ['id'], unique=False)
    op.create_index('ix_seasons_show_id', 'seasons', ['show_id'], unique=False)
    op.create_index('ix_season_show_number', 'seasons', ['show_id', 'season_number'], unique=False)

    # 4. episodes table
    op.create_table(
        'episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('custom_id', sa.String(length=50), nullable=True),
        sa.Column('show_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('episode_title', sa.String(length=255), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('content_group', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('artwork_available', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('content_group', 'language', name='uq_episode_content_group_language'),
        sa.CheckConstraint("status IN ('draft', 'published')", name='chk_episode_status'),
        sa.CheckConstraint("language IN ('en', 'hi')", name='chk_episode_language'),
        sa.CheckConstraint('episode_number >= 1', name='chk_episode_number_positive'),
        sa.CheckConstraint('duration_seconds IS NULL OR duration_seconds > 0', name='chk_episode_duration_positive'),
    )
    op.create_index('ix_episodes_id', 'episodes', ['id'], unique=False)
    op.create_index('ix_episodes_custom_id', 'episodes', ['custom_id'], unique=True)
    op.create_index('ix_episodes_show_id', 'episodes', ['show_id'], unique=False)
    op.create_index('ix_episodes_season_id', 'episodes', ['season_id'], unique=False)
    op.create_index('ix_episodes_episode_title', 'episodes', ['episode_title'], unique=False)
    op.create_index('ix_episodes_language', 'episodes', ['language'], unique=False)
    op.create_index('ix_episodes_content_group', 'episodes', ['content_group'], unique=False)
    op.create_index('ix_episodes_status', 'episodes', ['status'], unique=False)
    op.create_index('ix_episode_content_group_lang', 'episodes', ['content_group', 'language'], unique=False)
    op.create_index('ix_episode_show_season_epnum', 'episodes', ['show_id', 'season_id', 'episode_number'], unique=False)

    # 5. artwork table
    op.create_table(
        'artwork',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('show_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shows.id', ondelete='CASCADE'), nullable=True),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=True),
        sa.Column('artwork_type', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('show_id', 'artwork_type', name='uq_show_artwork_type'),
        sa.UniqueConstraint('episode_id', 'artwork_type', name='uq_episode_artwork_type'),
        sa.CheckConstraint("entity_type IN ('show', 'episode')", name='chk_artwork_entity_type'),
        sa.CheckConstraint("artwork_type IN ('poster', 'banner', 'thumbnail')", name='chk_artwork_type'),
        sa.CheckConstraint(
            "(entity_type = 'show' AND show_id IS NOT NULL AND episode_id IS NULL) OR "
            "(entity_type = 'episode' AND episode_id IS NOT NULL AND show_id IS NULL)",
            name='chk_artwork_entity_integrity'
        ),
    )
    op.create_index('ix_artwork_id', 'artwork', ['id'], unique=False)
    op.create_index('ix_artwork_entity_type', 'artwork', ['entity_type'], unique=False)
    op.create_index('ix_artwork_show_id', 'artwork', ['show_id'], unique=False)
    op.create_index('ix_artwork_episode_id', 'artwork', ['episode_id'], unique=False)
    op.create_index('ix_artwork_artwork_type', 'artwork', ['artwork_type'], unique=False)
    op.create_index('ix_artwork_entity_type_type', 'artwork', ['entity_type', 'artwork_type'], unique=False)

    # 6. publish_runs table
    op.create_table(
        'publish_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('triggered_by', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('show_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('episode_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('success', 'failed')", name='chk_publish_status'),
        sa.CheckConstraint('version >= 1', name='chk_publish_version_positive'),
    )
    op.create_index('ix_publish_runs_id', 'publish_runs', ['id'], unique=False)
    op.create_index('ix_publish_runs_version', 'publish_runs', ['version'], unique=True)
    op.create_index('ix_publish_runs_published_at', 'publish_runs', ['published_at'], unique=False)
    op.create_index('ix_publish_runs_triggered_by', 'publish_runs', ['triggered_by'], unique=False)
    op.create_index('ix_publish_runs_status', 'publish_runs', ['status'], unique=False)
    op.create_index('ix_publish_status_version', 'publish_runs', ['status', 'version'], unique=False)

def downgrade() -> None:
    op.drop_table('publish_runs')
    op.drop_table('artwork')
    op.drop_table('episodes')
    op.drop_table('seasons')
    op.drop_table('shows')
    op.drop_table('users')
