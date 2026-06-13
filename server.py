from flask import Flask, request, jsonify
import traceback 
from llm_agent import ask_assistant
from src.server.DB_API import DB_API
from src.server.constants import PRESET_QUERIES , RAMBAM_DEPARTMENTS_LIST
from src.llms.voice_to_text import transcribe


app = Flask(__name__)
db = DB_API()


def processApiRequest(request, message):
    try:
        if type(request) != int:
            return jsonify({"error": "Request must be numeric."}), 500
        user_request = int(request)
        user_message = message
    except Exception as e:
        print(f" ERROR in /api/ask: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    try:
        response = None
        if user_request == PRESET_QUERIES.Locate_Patient.value:
            if not message.isnumeric():
                return jsonify({"error": "Patient number must be numeric."}), 500
            p_info = db.SearchForPatient(int(user_message))
            response = p_info.location.capitalize() if p_info else "Patient not found."
        elif user_request == PRESET_QUERIES.Room_Occupancy.value:
            response = db.GetRoomPatientsCount(user_message)
        elif user_request == PRESET_QUERIES.Total_Occupancy.value:
            response = db.GetTotalPatientsCount()
        elif user_request == PRESET_QUERIES.Administration_Time.value:
            if not message.isnumeric():
                return jsonify({"error": "Patient number must be numeric."}), 500
            response = db.GetAdministrationTime(int(user_message))
        elif user_request == PRESET_QUERIES.Idle_Time.value:
            if not message.isnumeric():
                return jsonify({"error": "Patient number must be numeric."}), 500
            response = db.GetIdleTime(int(user_message))
        elif user_request == PRESET_QUERIES.Other.value:
            response = ask_assistant(user_message)
        else:
            response = "Unknown request. Please provide a request from the allegeable list."
        return jsonify({"response": response}), 200
    except Exception as e:
        print(f" ERROR in /api/ask: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/ask/voice', methods=['POST'])
def handle_ask_assistant_voice():
    audio_bytes = request.data

    with open("received.ogg", "wb") as f:
        f.write(audio_bytes)
    
    # FIX: Changed "r" to "rb" here so it can read the binary header
    with open("received.ogg", "rb") as f:
        header = f.read(4)
        f.seek(0)

        if header != b"OggS":
            return {"error": "Invalid OGG file"}, 400

    # No language parameter needed here anymore, we hardcoded it in the pipeline
    stt = transcribe("received.ogg")

    # Access the text from the returned dictionary and ensure PRESET_QUERIES uses .value
    return processApiRequest(PRESET_QUERIES.Other.value, stt['text'])

    
@app.route('/api/ask', methods=['POST'])
def handle_ask_assistant():
    data = request.json

    if not data.get("request") or not data.get("message"):
        return jsonify({"error": "Missing payload. Please provide with both the fields \"request\" and \"message\"."}), 400

    return processApiRequest(data.get("request"), data.get("message"))
    # try:
    #     if not data.get("request").isnumeric():
    #         return jsonify({"error": "Request must be numeric."}), 500
    #     user_request = int(data.get("request"))
    #     user_message = data.get("message")
    # except Exception as e:
    #     print(f" ERROR in /api/ask: {e}")
    #     traceback.print_exc()
    #     return jsonify({"error": str(e)}), 500

    # try:
    #     response = None
    #     if user_request == PRESET_QUERIES.Locate_Patient:
    #         if not data.get("message").isnumeric():
    #             return jsonify({"error": "Patient number must be numeric."}), 500
    #         response = db.SearchForPatient(int(user_message))
    #     elif user_request == PRESET_QUERIES.Room_Occupancy:
    #         response = db.GetRoomPatientsCount(user_message)
    #     elif user_request == PRESET_QUERIES.Total_Occupancy:
    #         response = db.GetTotalPatientsCount()
    #     elif user_request == PRESET_QUERIES.Administration_Time:
    #         if not data.get("message").isnumeric():
    #             return jsonify({"error": "Patient number must be numeric."}), 500
    #         response = db.GetAdministrationTime(int(user_message))
    #     elif user_request == PRESET_QUERIES.Idle_Time:
    #         if not data.get("message").isnumeric():
    #             return jsonify({"error": "Patient number must be numeric."}), 500
    #         response = db.GetIdleTime(int(user_message))
    #     elif user_request == PRESET_QUERIES.Other:
    #         response = ask_assistant(user_message)
    #     else:
    #         response = "Unknown request. Please provide a request from the allegeable list."
    #     return jsonify({"response": response}), 200
    # except Exception as e:
    #     print(f" ERROR in /api/ask: {e}")
    #     traceback.print_exc()
    #     return jsonify({"error": str(e)}), 500
@app.route('/api/update_location', methods=['POST'])
def handle_update_location():
    data = request.json
    patient_num = data.get("patientNumber")
    is_doctor_flow = data.get("isDoctorFlow", False)

    if not patient_num:
        return jsonify({"error": "Missing patientNumber"}), 400
    
    try: 
        p_num_int = int(patient_num)  
        
        # -----------------------------
        # DOCTOR FLOW: Handle Routing
        # -----------------------------
        if is_doctor_flow:
            routing_path = data.get("routingPath")
            
            if not routing_path:
                return jsonify({"error": "Missing routingPath for doctor flow"}), 400
            
            # Ensure the patient exists in the DB before adding a routing path
            if not db.SearchForPatient(p_num_int):
                db.InsertNewPatient(p_num_int, "Triage") # Or whatever default location makes sense
                
            # NOTE: You will need to implement this method in your DB_API class.
            # routing_path will be parsed as a list of lists: [[room_int, urgency_int], ...]
            db.UpdatePatientRouting(p_num_int, routing_path)
            
            return jsonify({"status": "success", "message": f"Patient {patient_num} routing path updated."}), 200

        # -----------------------------
        # NURSE FLOW: Handle Room Scan
        # -----------------------------
        else:
            new_location = data.get("roombarcode")
            
            if not new_location:
                return jsonify({"error": "Missing roombarcode"}), 400

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
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)