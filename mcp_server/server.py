from mcp.server.fastmcp import FastMCP
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse
import json

load_dotenv()

# Create an MCP server
mcp = FastMCP()

db_params = {
    'dbname': 'hr_DB',
    'user': 'postgres',
    'password': 'Dreams@2024',
    'host': 'localhost',  # or your database host/IP
    'port': '5432'         # default PostgreSQL port
}

# ---------------------- DATABASE CONFIG ----------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("Please set the DATABASE_URL environment variable")

parsed_url = urlparse(DATABASE_URL)

# Rebuild netloc without password
netloc = f"{parsed_url.hostname}:{parsed_url.port}"
if parsed_url.username:
    netloc = f"{parsed_url.username}@{netloc}"

resource_base_url = urlunparse((
    "postgres",      # scheme
    netloc,          # netloc (username@host:port)
    parsed_url.path,
    "", "", "",      # params, query, fragment
))

# ---------------------- TOOL DEFINITIONS ----------------------
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print(f"Adding {a} and {b}")
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers with discritionary arguments"""
    print(f"Subtracting {a} and {b}")
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print(f"Multiplying {a} and {b}")
    return a * b

@mcp.tool(name="query", description="Run a read-only SQL query")
def query(sql: str) -> str:
    print(f"Executing SQL: {sql}")
    conn = psycopg2.connect(**db_params)
    print("Connected to database")
    try:
        
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchall()
            return str(result)
    finally:
        conn.rollback()
        conn.close()

# ---------------------- RESOURCES ----------------------
@mcp.resource("resource://getSchema")
def list_resources():
    """Get the schema of the database in JSON format"""
    conn = psycopg2.connect(**db_params)
    print("connected to database for resources...")
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    tc.constraint_type,
                    kcu.constraint_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM 
                    information_schema.columns c
                LEFT JOIN 
                    information_schema.key_column_usage kcu 
                    ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
                LEFT JOIN 
                    information_schema.table_constraints tc 
                    ON kcu.constraint_name = tc.constraint_name
                LEFT JOIN 
                    information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name AND tc.constraint_type = 'FOREIGN KEY'
                WHERE 
                    c.table_schema = 'public'
                ORDER BY 
                    c.table_name, c.ordinal_position;
            """)
            
            rows = cur.fetchall()

            schema = {}

            for row in rows:
                table_name, column_name, data_type, is_nullable, column_default, constraint_type, _, foreign_table, foreign_column = row

                if table_name not in schema:
                    schema[table_name] = {'columns': []}

                constraint = None
                if constraint_type == 'PRIMARY KEY':
                    constraint = 'PRIMARY KEY'
                elif constraint_type == 'UNIQUE':
                    constraint = 'UNIQUE'
                elif constraint_type == 'FOREIGN KEY':
                    constraint = f'FOREIGN KEY → {foreign_table}({foreign_column})'

                schema[table_name]['columns'].append({
                    'name': column_name,
                    'type': data_type,
                    'nullable': is_nullable.lower() == 'yes',
                    'default': column_default,
                    'constraint': constraint
                })

            return schema  # clean JSON-ready Python dict

    finally:
        conn.close()

# @mcp.resource(dynamic=True)
# def read_resource(uri: str) -> ReadResourceResponse:
#     parsed = urlparse(uri)
#     parts = parsed.path.strip("/").split("/")
#     if len(parts) < 2 or parts[-1] != SCHEMA_PATH:
#         raise ValueError("Invalid resource URI")

#     table_name = parts[-2]

#     conn = psycopg2.connect(DATABASE_URL)
#     try:
#         with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
#             cur.execute(
#                 "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
#                 (table_name,)
#             )
#             columns = cur.fetchall()
#             return {
#                 "contents": [
#                     Content(
#                         uri=uri,
#                         mimeType="application/json",
#                         text=str(columns)
#                     )
#                 ]
#             }
#     finally:
#         conn.close()

# ---------------------- STATIC RESOURCES ----------------------
@mcp.resource("resource://some_static_resource")
def get_static_resource() -> str:
    """Static resource data"""
    return "Any static data can be returned"

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# ---------------------- PROMPTS ----------------------
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: str) -> list[tuple]:
    return [
        ("user", "I'm seeing this error:"),
        ("user", error),
        ("assistant", "I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    mcp.run(transport='sse')
