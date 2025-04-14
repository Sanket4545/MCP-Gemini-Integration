import speech_recognition as sr
import pyttsx3  # For offline TTS
from mcp import ClientSession
from mcp.client.sse import sse_client
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import asyncio
import json

load_dotenv()

chat_history = []

async def handle_database_related_query(session, user_input, gemini_client, gemini_tool):
    schema_response = await session.read_resource("resource://getSchema")
    if not schema_response or not schema_response.contents:
        return "Failed to retrieve database schema."
    schema = schema_response.contents[0].text
    prompt = (
    "You are an intelligent agent. Based on the user input, generate the appropriate SQL query. "
    "Here is a database schema. Understand it carefully:\n\n"
    "leave_type column contain the Sick, Vacation, Personal,Comp Off\n"
    f"Schema: {json.dumps(schema, indent=2)}\n\n"
    "Here is a user input:\n\n"
    f"User Input: {user_input}"
)
    tools = types.Tool(function_declarations=gemini_tool)
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(tools=[tools]),
    )

    chat_history.append(response.text)
    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        responseText = response.candidates[0].content.parts[0].text
    else:
        pass

    return response.text

async def handle_tool_response(session, input, gemini_client, gemini_tool):
    prompt = (
        "You are an intelligent agent. Based on the user input, decide which tool to call. "
        "and return the responce"
        f"User Input: {input}"
    )
    tools = types.Tool(function_declarations=gemini_tool)
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(tools=[tools]),
    )

    chat_history.append(response.text)
    part = response.candidates[0].content.parts[0]

    if hasattr(part, "function_call") and part.function_call:
        function_call = part.function_call
        result = await session.call_tool(
            name=function_call.name,
            arguments=function_call.args
        )
        reply_text = result.content[0].text
        return reply_text
    else:
        pass

    return response.text

async def modified_responce(session, input, first_input, gemini_client):  
    prompt = (
        "You are a helpful assistant. Your job is to explain database query results in simple, spoken English, "
        "as if you're talking to someone who doesn't know anything about databases. "
        "Don't use any technical or SQL terms. "
        "Just describe the information clearly and naturally, like you’re explaining it in a conversation.\n\n"
        f"Previous context: {first_input}\n\n"
        f"New query result: {input}\n\n"
        "Please explain this in plain, natural language suitable for voice output."
    )

    chat_history.append(prompt)
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text

async def run():
    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            tools = tools_response.tools
            resources = await session.list_resources()

            gemini_tool_declarations = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.inputSchema.get("properties", {}),
                        "required": tool.inputSchema.get("required", []),
                    },
                }
                for tool in tools
            ]

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            gemini_tool = types.Tool(function_declarations=gemini_tool_declarations)

            while True:
                user_input = input("Enter your question: ")
                if user_input:
                    reply_text = await handle_database_related_query(session, user_input, client, gemini_tool_declarations)
                    query_responce = await handle_tool_response(session, reply_text, client, gemini_tool_declarations)
                    final_text = await modified_responce(session, query_responce, user_input, client)
                    print("Reply:", final_text)
                else:
                    continue

                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run())
