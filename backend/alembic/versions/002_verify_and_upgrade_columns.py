"""Verify and add missing columns to images and analysis_jobs tables

Revision ID: 002_upgrade_columns
Revises: 001_initial_schema
Create Date: 2026-09-26 04:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '002_upgrade_columns'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Verify and upgrade 'images' table columns
    if 'images' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('images')}

        # Missing column checks and additions
        missing_columns = [
            ('original_filename', sa.Column('original_filename', sa.String(length=255), nullable=True)),
            ('object_key', sa.Column('object_key', sa.String(length=512), nullable=True)),
            ('preview_key', sa.Column('preview_key', sa.String(length=512), nullable=True)),
            ('mime_type', sa.Column('mime_type', sa.String(length=64), nullable=True)),
            ('file_format', sa.Column('file_format', sa.String(length=32), nullable=True)),
            ('file_size', sa.Column('file_size', sa.BigInteger(), nullable=True)),
            ('checksum', sa.Column('checksum', sa.String(length=64), nullable=True)),
            ('width', sa.Column('width', sa.Integer(), nullable=True)),
            ('height', sa.Column('height', sa.Integer(), nullable=True)),
            ('band_count', sa.Column('band_count', sa.Integer(), nullable=True)),
            ('dtype', sa.Column('dtype', sa.String(length=32), nullable=True)),
            ('nodata', sa.Column('nodata', sa.Float(), nullable=True)),
            ('crs', sa.Column('crs', sa.String(length=255), nullable=True)),
            ('epsg_code', sa.Column('epsg_code', sa.Integer(), nullable=True)),
            ('resolution_x', sa.Column('resolution_x', sa.Float(), nullable=True)),
            ('resolution_y', sa.Column('resolution_y', sa.Float(), nullable=True)),
            ('bounds', sa.Column('bounds', sa.JSON(), nullable=True)),
            ('transform', sa.Column('transform', sa.JSON(), nullable=True)),
            ('acquisition_time', sa.Column('acquisition_time', sa.DateTime(timezone=True), nullable=True)),
            ('sensor', sa.Column('sensor', sa.String(length=128), nullable=True)),
            ('modality', sa.Column('modality', sa.String(length=64), nullable=False, server_default='unknown')),
            ('is_geospatial', sa.Column('is_geospatial', sa.Boolean(), nullable=False, server_default='0')),
            ('validation_status', sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='valid')),
            ('created_at', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)),
            ('updated_at', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)),
        ]

        # Handle legacy 'filename' column rename if present
        if 'filename' in existing_cols and 'original_filename' not in existing_cols:
            try:
                op.alter_column('images', 'filename', new_column_name='original_filename')
                existing_cols.add('original_filename')
            except Exception:
                pass

        for col_name, col_def in missing_columns:
            if col_name not in existing_cols:
                try:
                    op.add_column('images', col_def)
                except Exception as e:
                    # Ignore if already added by database-specific mechanism
                    pass

    # 2. Verify and upgrade 'analysis_jobs' table columns
    if 'analysis_jobs' in existing_tables:
        existing_job_cols = {col['name'] for col in inspector.get_columns('analysis_jobs')}

        if 'pair_id' not in existing_job_cols:
            try:
                op.add_column(
                    'analysis_jobs',
                    sa.Column('pair_id', sa.Uuid(), sa.ForeignKey('bi_temporal_pairs.id', ondelete='SET NULL'), nullable=True)
                )
                op.create_index(op.f('ix_analysis_jobs_pair_id'), 'analysis_jobs', ['pair_id'], unique=False)
            except Exception:
                pass

        if 'cross_modal_pair_id' not in existing_job_cols:
            try:
                op.add_column(
                    'analysis_jobs',
                    sa.Column('cross_modal_pair_id', sa.Uuid(), sa.ForeignKey('optical_sar_pairs.id', ondelete='SET NULL'), nullable=True)
                )
                op.create_index(op.f('ix_analysis_jobs_cross_modal_pair_id'), 'analysis_jobs', ['cross_modal_pair_id'], unique=False)
            except Exception:
                pass


def downgrade() -> None:
    pass
