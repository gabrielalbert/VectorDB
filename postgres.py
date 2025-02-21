import os
import asyncpg
import dotenv
from typing import Optional

dotenv.load_dotenv()

conn_pool: Optional[asyncpg.Pool] = None

async def init_postgres() -> None:
    """
    Initialize the PostgreSQL connection pool and create the products table if it doesn't exist.

    This function is meant to be called at the startup of the FastAPI app to
    initialize a connection pool to PostgreSQL and ensure that the required
    database schema is in place.
    """
    global conn_pool
    try:
        print("Initializing PostgreSQL connection pool...")

        conn_pool = await asyncpg.create_pool(
            dsn = "postgres://postgres:HUAiXjXTJNXrkAyzgxkdpkjJqzPhpXSK@autorack.proxy.rlwy.net:25335/railway",
            #dsn=os.getenv("DATABASE_URL"),
            min_size=1, max_size=10
        )
        print("PostgreSQL connection pool created successfully.")

    except Exception as e:
        print(f"Error initializing PostgreSQL connection pool: {e}")
        raise
    #try:
    #    async with conn_pool.acquire() as conn:
    #        create_table_query = """
    #        CREATE TABLE IF NOT EXISTS products (
    #            id SERIAL PRIMARY KEY,
    #            name VARCHAR(100) NOT NULL,
    #            price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    #            quantity INT NOT NULL CHECK (quantity >= 0),
    #            description VARCHAR(255)
    #        );
    #        """
    #        async with conn.transaction():
    #            await conn.execute(create_table_query)
    #        logger.info("Products table ensured to exist.")

    #except Exception as e:
    #    logger.error(f"Error creating the products table: {e}")
    #    raise


async def get_postgres() -> asyncpg.Pool:
    """
    Return the PostgreSQL connection pool.

    This function returns the connection pool object, from which individual
    connections can be acquired as needed for database operations. The caller
    is responsible for acquiring and releasing connections from the pool.

    Returns
    -------
    asyncpg.Pool
        The connection pool object to the PostgreSQL database.

    Raises
    ------
    ConnectionError
        Raised if the connection pool is not initialized.
    """
    global conn_pool
    if conn_pool is None:
        print("Connection pool is not initialized.")
        raise ConnectionError("PostgreSQL connection pool is not initialized.")
    try:
        return conn_pool
    except Exception as e:
        print(f"Failed to return PostgreSQL connection pool: {e}")
        raise


async def close_postgres() -> None:
    """
    Close the PostgreSQL connection pool.

    This function should be called during the shutdown of the FastAPI app
    to properly close all connections in the pool and release resources.
    """
    global conn_pool
    if conn_pool is not None:
        try:
            print("Closing PostgreSQL connection pool...")
            await conn_pool.close()
            print("PostgreSQL connection pool closed successfully.")
        except Exception as e:
            print(f"Error closing PostgreSQL connection pool: {e}")
            raise
    else:
        print("PostgreSQL connection pool was not initialized.")