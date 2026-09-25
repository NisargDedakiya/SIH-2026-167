"""Initial schema for SatQuery AI

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-26 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. images table
    op.create_table(
        'images',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('object_key', sa.String(length=512), nullable=False),
        sa.Column('preview_key', sa.String(length=512), nullable=True),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('file_format', sa.String(length=32), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('band_count', sa.Integer(), nullable=False),
        sa.Column('dtype', sa.String(length=32), nullable=False),
        sa.Column('nodata', sa.Float(), nullable=True),
        sa.Column('crs', sa.String(length=255), nullable=True),
        sa.Column('epsg_code', sa.Integer(), nullable=True),
        sa.Column('resolution_x', sa.Float(), nullable=True),
        sa.Column('resolution_y', sa.Float(), nullable=True),
        sa.Column('bounds', sa.JSON(), nullable=True),
        sa.Column('transform', sa.JSON(), nullable=True),
        sa.Column('acquisition_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sensor', sa.String(length=128), nullable=True),
        sa.Column('modality', sa.String(length=64), nullable=False, server_default='unknown'),
        sa.Column('is_geospatial', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='valid'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('object_key'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_images_id'), 'images', ['id'], unique=False)
    except Exception:
        pass

    # 2. image_metadata table
    op.create_table(
        'image_metadata',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('image_id', sa.Uuid(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_image_metadata_image_id'), 'image_metadata', ['image_id'], unique=False)
    except Exception:
        pass

    # 3. bi_temporal_pairs table
    op.create_table(
        'bi_temporal_pairs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('image_t1_id', sa.Uuid(), nullable=False),
        sa.Column('image_t2_id', sa.Uuid(), nullable=False),
        sa.Column('acquisition_time_t1', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acquisition_time_t2', sa.DateTime(timezone=True), nullable=True),
        sa.Column('spatially_compatible', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('temporally_valid', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('overlap_ratio', sa.Float(), nullable=True),
        sa.Column('crs_t1', sa.String(length=255), nullable=True),
        sa.Column('crs_t2', sa.String(length=255), nullable=True),
        sa.Column('resolution_t1', sa.Float(), nullable=True),
        sa.Column('resolution_t2', sa.Float(), nullable=True),
        sa.Column('bounds_t1', sa.JSON(), nullable=True),
        sa.Column('bounds_t2', sa.JSON(), nullable=True),
        sa.Column('alignment_status', sa.String(length=32), nullable=False, server_default='NOT_REQUIRED'),
        sa.Column('registration_method', sa.String(length=64), nullable=True),
        sa.Column('registration_metadata', sa.JSON(), nullable=True),
        sa.Column('validation_result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['image_t1_id'], ['images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_t2_id'], ['images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_bi_temporal_pairs_id'), 'bi_temporal_pairs', ['id'], unique=False)
        op.create_index(op.f('ix_bi_temporal_pairs_image_t1_id'), 'bi_temporal_pairs', ['image_t1_id'], unique=False)
        op.create_index(op.f('ix_bi_temporal_pairs_image_t2_id'), 'bi_temporal_pairs', ['image_t2_id'], unique=False)
    except Exception:
        pass

    # 4. optical_sar_pairs table
    op.create_table(
        'optical_sar_pairs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('optical_image_id', sa.Uuid(), nullable=False),
        sa.Column('sar_image_id', sa.Uuid(), nullable=False),
        sa.Column('optical_modality', sa.String(length=64), nullable=False, server_default='optical'),
        sa.Column('sar_modality', sa.String(length=64), nullable=False, server_default='sar'),
        sa.Column('optical_sensor', sa.String(length=128), nullable=True),
        sa.Column('sar_sensor', sa.String(length=128), nullable=True),
        sa.Column('optical_acquisition_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sar_acquisition_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('optical_crs', sa.String(length=255), nullable=True),
        sa.Column('sar_crs', sa.String(length=255), nullable=True),
        sa.Column('optical_resolution', sa.Float(), nullable=True),
        sa.Column('sar_resolution', sa.Float(), nullable=True),
        sa.Column('optical_bounds', sa.JSON(), nullable=True),
        sa.Column('sar_bounds', sa.JSON(), nullable=True),
        sa.Column('registration_status', sa.String(length=32), nullable=False, server_default='UNALIGNED'),
        sa.Column('spatial_compatibility', sa.String(length=32), nullable=False, server_default='COMPATIBLE'),
        sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='VALID'),
        sa.Column('overlap_ratio', sa.Float(), nullable=True),
        sa.Column('alignment_method', sa.String(length=64), nullable=True),
        sa.Column('alignment_metadata', sa.JSON(), nullable=True),
        sa.Column('validation_result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['optical_image_id'], ['images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sar_image_id'], ['images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_optical_sar_pairs_id'), 'optical_sar_pairs', ['id'], unique=False)
        op.create_index(op.f('ix_optical_sar_pairs_optical_image_id'), 'optical_sar_pairs', ['optical_image_id'], unique=False)
        op.create_index(op.f('ix_optical_sar_pairs_sar_image_id'), 'optical_sar_pairs', ['sar_image_id'], unique=False)
    except Exception:
        pass

    # 5. analysis_jobs table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('image_id', sa.Uuid(), nullable=False),
        sa.Column('pair_id', sa.Uuid(), nullable=True),
        sa.Column('cross_modal_pair_id', sa.Uuid(), nullable=True),
        sa.Column('task', sa.String(length=64), nullable=False),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('confidence_method', sa.String(length=64), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pair_id'], ['bi_temporal_pairs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cross_modal_pair_id'], ['optical_sar_pairs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_analysis_jobs_id'), 'analysis_jobs', ['id'], unique=False)
        op.create_index(op.f('ix_analysis_jobs_image_id'), 'analysis_jobs', ['image_id'], unique=False)
        op.create_index(op.f('ix_analysis_jobs_pair_id'), 'analysis_jobs', ['pair_id'], unique=False)
        op.create_index(op.f('ix_analysis_jobs_cross_modal_pair_id'), 'analysis_jobs', ['cross_modal_pair_id'], unique=False)
        op.create_index(op.f('ix_analysis_jobs_task'), 'analysis_jobs', ['task'], unique=False)
        op.create_index(op.f('ix_analysis_jobs_status'), 'analysis_jobs', ['status'], unique=False)
    except Exception:
        pass

    # 6. agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('analysis_id', sa.Uuid(), nullable=True),
        sa.Column('original_query', sa.Text(), nullable=False),
        sa.Column('normalized_query', sa.Text(), nullable=False),
        sa.Column('detected_task', sa.String(length=64), nullable=False),
        sa.Column('classification_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('selected_tools', sa.JSON(), nullable=False),
        sa.Column('plan_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='started'),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('confidence_method', sa.String(length=64), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)
        op.create_index(op.f('ix_agent_runs_analysis_id'), 'agent_runs', ['analysis_id'], unique=False)
        op.create_index(op.f('ix_agent_runs_detected_task'), 'agent_runs', ['detected_task'], unique=False)
        op.create_index(op.f('ix_agent_runs_status'), 'agent_runs', ['status'], unique=False)
    except Exception:
        pass

    # 7. agent_trace_events table
    op.create_table(
        'agent_trace_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('agent_run_id', sa.Uuid(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('tool_name', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='completed'),
        sa.Column('parameters_json', sa.JSON(), nullable=True),
        sa.Column('output_metadata_json', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_agent_trace_events_id'), 'agent_trace_events', ['id'], unique=False)
        op.create_index(op.f('ix_agent_trace_events_agent_run_id'), 'agent_trace_events', ['agent_run_id'], unique=False)
    except Exception:
        pass

    # 8. evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('analysis_id', sa.Uuid(), nullable=False),
        sa.Column('image_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False, server_default='bounding_box'),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('geometry_json', sa.JSON(), nullable=True),
        sa.Column('pixel_geometry_json', sa.JSON(), nullable=False),
        sa.Column('geo_geometry_json', sa.JSON(), nullable=True),
        sa.Column('artifact_key', sa.String(length=512), nullable=True),
        sa.Column('crop_artifact_key', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    try:
        op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
        op.create_index(op.f('ix_evidence_analysis_id'), 'evidence', ['analysis_id'], unique=False)
        op.create_index(op.f('ix_evidence_image_id'), 'evidence', ['image_id'], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    op.drop_table('evidence')
    op.drop_table('agent_trace_events')
    op.drop_table('agent_runs')
    op.drop_table('analysis_jobs')
    op.drop_table('optical_sar_pairs')
    op.drop_table('bi_temporal_pairs')
    op.drop_table('image_metadata')
    op.drop_table('images')
