from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from src.server.Server import DB_API 

db = DB_API()

llm_json = ChatOllama(model="llama3.1", temperature=0, format="json")
llm_text = ChatOllama(model="llama3.1", temperature=0)

def ask_assistant(user_message: str) -> str:

    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a medical data extractor. Extract the patient number from the user's input. "
                   "Output ONLY a valid JSON object representing a database query filter. "
                   "Example: {{\"patientNumber\": 123}}"),
        ("human", "{text}")
    ])
    
    query_chain = query_prompt | llm_json | JsonOutputParser()
    
    try:
        mongo_query_params = query_chain.invoke({"text": user_message})
        print(f"[*] Step 1 - AI Generated Query Params: {mongo_query_params}")
        
        patient_num = mongo_query_params.get("patientNumber")
        
        if not patient_num:
            return "Could not understand which patient number you are looking for."
            
        p_info = db.SearchForPatient(int(patient_num))
        
        if p_info:
            raw_db_result = f"DB_RESULT: Patient {patient_num} found. Location: {p_info.location}."
        else:
            raw_db_result = f"DB_RESULT: Patient {patient_num} does not exist in records."
            
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
    print(" FindMyPatient Pipeline is starting up...")
    
    test_question = "I want to know how many patients are there in total?"
    print(f"\nUser Query: '{test_question}'\n")
    print("-" * 10)
    
    final_answer = ask_assistant(test_question)
    
    print("-" * 10)
    print(f" Final Humanized Answer:\n{final_answer}")