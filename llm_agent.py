import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser

# Import the MCP Client tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

llm_json = ChatOllama(model="llama3.1", temperature=0, format="json")
llm_text = ChatOllama(model="llama3.1", temperature=0)

async def run_mcp_agent(user_message: str) -> str:
    # 1. Generate the Mongo Query 
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a MongoDB expert. Translate the user's natural language request into a MongoDB query. "
                   "The database collection has patients with the fields: ['patientNumber', 'location', 'administrationTime', 'routingPath']. \n"
                   "You MUST not edit or change the database."
                   "Output ONLY a valid list of MongoDB aggregation queries to fufill the request.\n"
                ),
        ("human", "{text}")
    ])
    
    query_chain = query_prompt | llm_json | JsonOutputParser()
    
    try:
        mongo_query = query_chain.invoke({"text": user_message})
        print(f"[*] Step 1 - Dynamic Mongo Query Generated: {mongo_query}")

        # 2. Define the connection to your separate MCP Server
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
        
        # 3. Connect to the MCP server and call the tool
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Execute the tool safely ON THE SERVER
                tool_result = await session.call_tool(
                    name="execute_mongo_query",
                    arguments={"query": mongo_query}
                )
                
                db_result = tool_result.content[0].text
                raw_db_result = f"DB_RESULT: User request - \"{user_message}\" returned: {db_result}"
                print(f"[*] Step 2 - MCP Server Result: {raw_db_result}")

                # 4. Humanize the final response
                humanize_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are the FindMyPatient friendly assistant. "
                               "Take the raw database result provided and turn it into a helpful, natural, and polite sentence in English. "
                               "Do not add information that is not in the raw data."),
                    ("human", "{raw_data}")
                ])
                
                humanize_chain = humanize_prompt | llm_text
                final_response = humanize_chain.invoke({"raw_data": raw_db_result})
                
                return final_response.content

    except Exception as e:
        return f"System processing error: {str(e)}"

# Synchronous wrapper so Flask can call this without changing server.py
def ask_assistant(user_message: str) -> str:
    return asyncio.run(run_mcp_agent(user_message))

if __name__ == "__main__":
    print(" FindMyPatient MCP Pipeline is starting up...")
    
    test_questions = [
        "How many patients are registered in the system?",          
        "Can you tell me where patient number 123 is located?",      
        "Show me all the patients that are currently in the ER",     
        "Are there any patients in the Cardiology department?"       
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n" + "="*50)
        print(f" TEST {i}")
        print(f" User Query: '{question}'")
        print("-" * 50)
        
        final_answer = ask_assistant(question)
        
        print("-" * 50)
        print(f" Final Answer:\n{final_answer}")