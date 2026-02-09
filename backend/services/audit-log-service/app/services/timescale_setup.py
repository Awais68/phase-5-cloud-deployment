"""
TimescaleDB setup and configuration.
"""
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
import structlog

from app.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


async def setup_timescaledb(engine: AsyncEngine) -> None:
    """
    Setup TimescaleDB hypertable and compression.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        try:
            # Enable TimescaleDB extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            logger.info("timescaledb_extension_enabled")

            # Check if hypertable already exists
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'audit_events'
                    );
                """)
            )
            table_exists = result.scalar()

            if table_exists:
                # Check if already a hypertable
                result = await conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM timescaledb_information.hypertables
                            WHERE hypertable_name = 'audit_events'
                        );
                    """)
                )
                is_hypertable = result.scalar()

                if not is_hypertable:
                    # Convert to hypertable
                    await conn.execute(
                        text("""
                            SELECT create_hypertable(
                                'audit_events',
                                'timestamp',
                                if_not_exists => TRUE,
                                migrate_data => TRUE
                            );
                        """)
                    )
                    logger.info("audit_events_hypertable_created")
                else:
                    logger.info("audit_events_already_hypertable")

                # Add compression policy (compress data older than 30 days)
                await conn.execute(
                    text(f"""
                        SELECT add_compression_policy(
                            'audit_events',
                            INTERVAL '{settings.compression_days} days',
                            if_not_exists => TRUE
                        );
                    """)
                )
                logger.info(
                    "compression_policy_added",
                    compression_days=settings.compression_days
                )

                # Add retention policy (delete data older than retention period)
                await conn.execute(
                    text(f"""
                        SELECT add_retention_policy(
                            'audit_events',
                            INTERVAL '{settings.retention_days} days',
                            if_not_exists => TRUE
                        );
                    """)
                )
                logger.info(
                    "retention_policy_added",
                    retention_days=settings.retention_days
                )

            else:
                logger.info("audit_events_table_not_yet_created")

        except Exception as e:
            logger.error(
                "failed_to_setup_timescaledb",
                error=str(e),
                exc_info=True
            )
            raise
