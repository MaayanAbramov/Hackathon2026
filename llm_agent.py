from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from src.server.DB_API import DB_API 

db = DB_API()

llm_json = ChatOllama(model="llama3.1", temperature=0, format="json")
llm_text = ChatOllama(model="llama3.1", temperature=0)

def ask_assistant(user_message: str) -> str:
    # text to mongo
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a MongoDB expert. Translate the user's natural language request into a MongoDB query. "
                   "The database collection has patients with fields like 'patientNumber', 'location', etc. "
                   "Output ONLY a valid JSON object with exactly two keys:\n"
                   "1. 'action': strictly use 'find' to search for records, or 'count' to get a total number.\n"
                   "2. 'filter': a valid MongoDB query dictionary.\n"
                   "Examples:\n"
                   "- For 'where is patient 123?': {{\"action\": \"find\", \"filter\": {{\"patientNumber\": 123}}}}\n"
                   "- For 'how many patients are there?': {{\"action\": \"count\", \"filter\": {{}}}}\n"
                   "- For 'find all patients in the ER': {{\"action\": \"find\", \"filter\": {{\"location\": \"ER\"}}}}"),
        ("human", "{text}")
    ])
    
    query_chain = query_prompt | llm_json | JsonOutputParser()
    
    try:
        # text to query
        mongo_query = query_chain.invoke({"text": user_message})
        print(f"[*] Step 1 - Dynamic Mongo Query: {mongo_query}")
        
        action = mongo_query.get("action")
        query_filter = mongo_query.get("filter", {})
        
        
        if not action:
            return "Could not generate a valid database action."
            
        db_result = db.ExecuteDynamicQuery(action, query_filter)
        
        raw_db_result = f"DB_RESULT: Action '{action}' with filter {query_filter} returned: {db_result}"
        print(f"[*] Step 2 - Raw DB Result: {raw_db_result}")

     
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

if __name__ == "__main__":
    print(" FindMyPatient Dynamic Pipeline is starting up...")
    
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