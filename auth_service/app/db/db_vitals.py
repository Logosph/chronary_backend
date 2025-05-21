import json

import asyncpg
from asyncpg import InvalidCatalogNameError, connect
from fastapi import HTTPException, status
from sqlalchemy import create_engine, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.logger import logger
from app.config.settings import settings as config


Base = declarative_base()


async def _init_connection(conn):
    """Json codec for proper json fields encode/decode"""
    await conn.set_type_codec('jsonb',
                              encoder=json.dumps,
                              decoder=json.loads,
                              schema='pg_catalog'
                              )
    await conn.set_type_codec('json',
                              encoder=json.dumps,
                              decoder=json.loads,
                              schema='pg_catalog'
                              )


async def get_connection_pool():
    try:
        _connection_pool = await asyncpg.create_pool(
            min_size=1,
            max_size=40,
            command_timeout=60,
            max_queries=10,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DB_NAME,
            init=_init_connection,
            server_settings={'application_name': 'webapi (asyncpg)'}
            # ssl="require",
        )
        logger.info("Database pool connection opened")
        return _connection_pool

    except Exception as e:

        logger.error("Database pool connection opener error: ", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database pool connection opener error"
        )


def dumps(d):
    return json.dumps(d, default=str)

engine = create_engine(
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}"
    f"/{config.POSTGRES_DB_NAME}?application_name=webapi (SQLAlchemy)",
    max_overflow=40,
    json_serializer=dumps,
    pool_timeout=60,
    pool_pre_ping=True,
)

engine_for_celery = create_engine(
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}"
    f"/{config.POSTGRES_DB_NAME}?application_name=webapi (SQLAlchemy)",
    poolclass=NullPool,
    json_serializer=dumps,
)

from sqlalchemy.ext.automap import automap_base

AutomapBase = automap_base()
AutomapBase.prepare(autoload_with=engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


async def initiate_db():
    logger.info('Database initialization')
    try:
        logger.info(f'Try to connect to database {config.POSTGRES_DB_NAME}')
        await connect(
            user=config.POSTGRES_USER,
            database=config.POSTGRES_DB_NAME,
            password=config.POSTGRES_PASSWORD,
            port=config.POSTGRES_PORT,
            host=config.POSTGRES_HOST
        )
    except InvalidCatalogNameError:
        logger.warning(
            f'Database {config.POSTGRES_DB_NAME} does not exist. \n Creating database {config.POSTGRES_DB_NAME}')
        # Database does not exist, create it.
        sys_conn = await connect(
            user=config.POSTGRES_USER,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            password=config.POSTGRES_PASSWORD
        )
        await sys_conn.execute(
            f'CREATE DATABASE "{config.POSTGRES_DB_NAME}" OWNER "{config.POSTGRES_USER}"'
        )
        await sys_conn.close()
        logger.info(f'Successful create database {config.POSTGRES_DB_NAME}')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async_engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}"
    f"/{config.POSTGRES_DB_NAME}", max_overflow=40,
    pool_timeout=60,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def get_async_db():
    db = async_session()
    try:
        yield db
    finally:
        db.close()
