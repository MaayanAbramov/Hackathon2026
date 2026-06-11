from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from src.server.DB_API import DB_API 

db = DB_API()

tools = []
llm_json = ChatOllama(model="llama3.1", temperature=0, format="json")
llm_text = ChatOllama(model="llama3.1", temperature=0)

def ask_assistant(user_message: str) -> str:

    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a medical data extractor. Analyze the user's input and determine their intent. "
                   "Output ONLY a valid JSON object based on the following rules:\n"
                   "- If they ask about a specific patient, output: {{\"intent\": \"find_patient\", \"patientNumber\": 123}}\n"
                   "- If they ask for the total number/sum/amount of patients, output: {{\"intent\": \"count_patients\"}}"),
        ("human", "{text}")
    ])
    
    query_chain = query_prompt | llm_json | JsonOutputParser()
    
    try:
        mongo_query_params = query_chain.invoke({"text": user_message})
        print(f"[*] Step 1 - AI Generated Query Params: {mongo_query_params}")
        
        intent = mongo_query_params.get("intent")
        

        if intent == "count_patients":
         
            total_count = db.GetTotalPatientsCount()
            raw_db_result = f"DB_RESULT: The total number of patients currently in the hospital is {total_count}."
            
        elif intent == "find_patient":
        
            patient_num = mongo_query_params.get("patientNumber")
            if not patient_num:
                return "Could not understand which patient number you are looking for."
                
            p_info = db.SearchForPatient(int(patient_num))
            
            if p_info:
                raw_db_result = f"DB_RESULT: Patient {patient_num} found. Location: {p_info.location}."
            else:
                raw_db_result = f"DB_RESULT: Patient {patient_num} does not exist in records."
        
        else:
            return "Sorry, I didn't understand the request."
            
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
    print("🚀 FindMyPatient Pipeline is starting up...")
    
   
    test_question_1 = "Give the sum of total clients"
    print(f"\n--- Test 1 ---")
    print(f"User Query: '{test_question_1}'")
    print(f"💬 Final Answer:\n{ask_assistant(test_question_1)}")

    test_question_2 = "Where is client 1 located?"
    print(f"\n--- Test 2 ---")
    print(f"User Query: '{test_question_2}'")
    print(f"💬 Final Answer:\n{ask_assistant(test_question_2)}")