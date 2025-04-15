# 🤖 MCP Server with Gemini AI Integration

This project demonstrates a powerful integration between a **Model Context Protocol (MCP)** server and **Gemini AI** by Google to interact with a **PostgreSQL** database using natural language. Users can ask questions in plain English, which are intelligently converted into SQL queries, executed on a local PostgreSQL server, and returned as friendly responses using AI.

---

## 🔧 Features

- ✅ **FastMCP Server** setup with custom tools and resources
- 🧠 **Gemini AI integration** to parse and process user queries
- 🗣️ Converts user input into SQL queries using Gemini function calling
- 🗃️ Connects to local **PostgreSQL** database to fetch data
- 📚 Returns database schema as structured JSON
- 💬 Explains query results in **natural, human-readable language**

---

## 🚀 How It Works

1. Start a local **MCP server** (`server.py`) that exposes:
   - Tools like `add`, `subtract`, `multiply`, and a read-only SQL `query`
   - Resources like database schema (`resource://getSchema`) and static greetings
2. Run the **client** (`client.py`), which:
   - Accepts natural language input from the user
   - Sends schema + prompt to **Gemini AI**
   - Gemini returns a function call with the correct tool and parameters
   - Executes SQL via MCP and returns results
   - Gemini then explains the SQL results in plain English

---

## 🗄️ Database Requirements

Ensure you have a PostgreSQL database running locally with:
- Database name: `hr_DB`
- User: `postgres`
- Password: `Dreams@2024`
- Port: `5432`

Set up the following environment variable in a `.env` file:

