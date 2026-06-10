from flask import Flask, request, jsonify
import traceback 
from llm_agent import ask_assistant
from src.server.DB_API import DB_API

app = Flask(__name__)
db = DB_API()

@app.route('/api/ask', methods=['POST'])
def handle_ask_assistant():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    try:
        ai_response = ask_assistant(user_message)
        return jsonify({"response": ai_response}), 200
    except Exception as e:
        print(f" ERROR in /api/ask: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/update_location', methods=['POST'])
def handle_update_location():
    data = request.json
    patient_num = data.get("patientNumber")
    new_location = data.get("roombarcode")

    if not patient_num or not new_location:
        return jsonify({"error":"Missing patientNumber or roombarcode"}), 400
    
    try: 
        p_num_int = int(patient_num)  
        if db.SearchForPatient(p_num_int):
            db.UpdatePatientLocation(p_num_int, new_location)
        else: 
            db.InsertNewPatient(p_num_int, new_location) 
        return jsonify({"status": "success", "message": f"Patient {patient_num} moved to {new_location}"}), 200
        
    except Exception as e:
     
        print(f"\n CRASH in /api/update_location:")
        print(f"Message: {e}")
        traceback.print_exc() 
        print("-" * 40 + "\n")
        
        return jsonify({"error": str(e)}), 500

@app.route('/api/remove_patient', methods=['POST'])
def handle_remove_patient():
    data = request.json
    patient_num = data.get("patientNumber")

    if not patient_num:
        return jsonify({"error":"Missing patientNumber"}), 400
    
    try:
        p_num_int = int(patient_num)
        
        if db.SearchForPatient(p_num_int) is None:
            return jsonify({"error": f"Patient {patient_num} does not exist"}), 404
        else:
            db.RemovePatient(p_num_int)
            
        return jsonify({"status": "success", "message": f"Patient {patient_num} was removed successfully"}), 200
        
    except Exception as e:
        print(f"\n CRASH in /api/remove_patient:")
        print(f"Message: {e}")
        traceback.print_exc()
        print("-" * 40 + "\n")
        
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    print(" Starting Flask API Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)