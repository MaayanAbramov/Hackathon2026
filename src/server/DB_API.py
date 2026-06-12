import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
from zoneinfo import ZoneInfo

# Import the extracted constants
from src.server.constants import (
    PERMITTED_FIELDS, 
    FIELD_TO_PERMITTED_TYPE, 
    RAMBAM_DEPARTMENTS_LIST, 
    DB_NAME, 
    COLLECTION_NAME
)

load_dotenv()  # Load environment variables from .env file
db_string = os.getenv("DATABASE_URL")
 
class PatientInfo:
    def __init__(self, patientNumber, location, location_history=None, routing_path=None): 
        """Initializes a new PatientInfo instance with a validated patient number, location, and routing path."""
        if not isinstance(patientNumber, int):
            raise TypeError(f"patientNumber must be an integer, got {type(patientNumber).__name__} instead.")
        self.__patientNumber = patientNumber
        self.location = location
        self.__location_history = location_history if location_history is not None else []
        self.__routing_path = routing_path if routing_path is not None else []
        
        if not self.__location_history:
            self.location_history_append(location)
    
    @property
    def patientNumber(self):
        """Returns the patient's unique identifying number."""
        return self.__patientNumber
    
    @property
    def location(self):
        """Returns the patient's current hospital location."""
        return self.__location
        
    @property
    def location_history(self):
        """Returns the patient's current history list of (location, time_stamp) tuples"""
        return self.__location_history
        
    @property
    def routing_path(self):
        """Returns the doctor's assigned routing path list of lists/tuples: [[room, urgency], ...]"""
        return self.__routing_path
    
    @location.setter
    def location(self, value):
        """Updates the patient's location after verifying the input is a string."""
        if not isinstance(value, str):
            raise TypeError(f"Location must be a string, got {type(value).__name__} instead.")
        self.__location = value

    @routing_path.setter
    def routing_path(self, value):
        """Updates the patient's routing path after verifying the input is a list."""
        if not isinstance(value, list):
            raise TypeError(f"Routing path must be a list, got {type(value).__name__} instead.")
        self.__routing_path = value

    def location_history_append(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Location must be a string, got {type(value).__name__} instead.")
        now = datetime.now(ZoneInfo("Asia/Jerusalem"))
        self.__location_history.append((value, now))

    def __str__(self):
        """Returns a human-readable string representation of the patient's info."""
        return f"PatientInfo(patientNumber={self.__patientNumber}, location='{self.__location}', location_history='{self.location_history}', routing_path='{self.routing_path}')"
    
    def __repr__(self):
        """Returns a formal string representation of the patient's info."""
        return self.__str__()
    
    def to_dict(self, key_list):
        """Converts the object to a JSON-safe dictionary."""
        formatted_history = []
        for loc, time_stamp in self.__location_history:
            time_str = time_stamp.isoformat() if isinstance(time_stamp, datetime) else time_stamp
            formatted_history.append({"location": loc, "timestamp": time_str})
          
        dict_ = {
            "patientNumber": self.__patientNumber,
            "location": self.location,
            "location_history": formatted_history,
            "routing_path": self.__routing_path
        }
        return { key:dict_[key] for key in key_list if key in dict_.keys()}


class DB_API:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Ensures only a single database connection instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.client = MongoClient(db_string)
            cls.db = cls.client[DB_NAME]
            cls.collection = cls.db[COLLECTION_NAME]
        return cls._instance

    def raise_if_illegal(self, user_data):
        """Validates that the provided data conforms to permitted fields, types, and departmental values."""
        if not isinstance(user_data, dict):
            raise TypeError(f"user_data must be passed as dictionary, not as {type(user_data)}")
        for k, v in user_data.items():
            if v is None:
                raise ValueError(f"In user_data : {user_data}\nThe value for key '{k}' cannot be None")
            if not k in PERMITTED_FIELDS:
                raise ValueError(f"In user_data : {user_data}.\nKey '{k}' is not in {PERMITTED_FIELDS}")
            if not type(v) == FIELD_TO_PERMITTED_TYPE.get(k, None):
                raise ValueError(f"In user_data : {user_data}\nValue '{v}' (associated with key '{k}') type is {type(v)} and the program expected it to be {FIELD_TO_PERMITTED_TYPE.get(k, None)}")
            if k == "patientNumber" and not 0 < v < 9223372036854775807 :
                raise ValueError(f"Patient patientNumber must be with value greater than 0, got {v}")
            if k == "location" and v.lower() not in RAMBAM_DEPARTMENTS_LIST:
                raise ValueError(f"Location value must be a legal value within the following list {RAMBAM_DEPARTMENTS_LIST}")
    
    def SearchForPatient(self, patientNumber):
        """Searches the database for a patient by their number and returns a PatientInfo object."""
        user_data = {"patientNumber" : patientNumber}
        try:
            self.raise_if_illegal(user_data=user_data)
            document = self.collection.find_one(user_data)
            
            if document:
                return PatientInfo(
                    patientNumber=document.get("patientNumber"), 
                    location=document.get("location"),
                    location_history=document.get("location_history"),
                    routing_path=document.get("routing_path", []) # Fetch routing path if it exists
                )
            else:
                return None

        except Exception as e:
            print(f"Database query failed: {e}")
            return None
        
    def GetTotalPatientsCount(self):
        """ returns the total numbers of patients currently in the database."""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"Database count failed: {e}")
            return 0

    def UpdatePatientLocation(self, patientNumber = None, new_location = None):
        """Updates an existing patient's location in the database and returns the updated object."""
        p_info = self.SearchForPatient(patientNumber=patientNumber)
        if p_info is None:
            raise LookupError(f"An error occoured , Patient patientNumber = {patientNumber} was not found in database records.")
        else:
            self.raise_if_illegal(user_data={"patientNumber": patientNumber, "location": new_location})
            try:
                p_info.location_history_append(new_location)
                p_info.location = new_location
                self.collection.update_one(
                    {"patientNumber": p_info.patientNumber}, 
                    {"$set": {
                        "location": p_info.location,
                        "location_history": p_info.location_history
                    }}
                )
                
                print(f"Successfully updated Patient {p_info.patientNumber}'s location to {p_info.location}")
                return p_info
            except Exception as e:
                print(f"Database update failed: {e}")
                return None

    def UpdatePatientRouting(self, patientNumber=None, routing_path=None):
        """Saves the doctor's assigned routing path for a patient."""
        p_info = self.SearchForPatient(patientNumber=patientNumber)
        if p_info is None:
            raise LookupError(f"An error occurred, Patient patientNumber = {patientNumber} was not found in database records.")
        
        if not isinstance(routing_path, list):
            raise TypeError(f"routing_path must be a list, got {type(routing_path).__name__} instead.")

        try:
            p_info.routing_path = routing_path
            self.collection.update_one(
                {"patientNumber": p_info.patientNumber}, 
                {"$set": {
                    "routing_path": p_info.routing_path
                }}
            )
            print(f"Successfully updated Patient {p_info.patientNumber}'s routing path to {routing_path}")
            return p_info
        except Exception as e:
            print(f"Database routing update failed: {e}")
            return None

    def InsertNewPatient(self, patientNumber=None, location=None):
        """Validates and inserts a completely new patient record into the database."""
        existing_patient = self.SearchForPatient(patientNumber=patientNumber)
        if existing_patient is not None:
            raise ValueError(f"Cannot insert: Patient patientNumber {patientNumber} already exists in the database.")
        now = datetime.now(ZoneInfo("Asia/Jerusalem"))
        user_data = {
            "patientNumber": patientNumber, 
            "location": location, 
            "location_history": [(location, now)],
            "routing_path": []
        }
        self.raise_if_illegal(user_data=user_data)

        try:
            self.collection.insert_one(user_data)
            print(f"Successfully inserted new Patient {patientNumber} at location '{location}'.")
            return PatientInfo(patientNumber=patientNumber, location=location)
        except Exception as e:
            print(f"Database insertion failed: {e} ")
            return None

    def RemovePatient(self, patientNumber=None):
        """Removes a patient from the database based on their unique patient number."""
        self.raise_if_illegal(user_data={"patientNumber": patientNumber})

        try:
            result = self.collection.delete_one({"patientNumber": patientNumber})
            if result.deleted_count > 0:
                print(f"Successfully removed Patient {patientNumber} from the database.")
                return True
            else:
                print(f"Patient {patientNumber} was not found. Nothing was removed.")
                return False
        except Exception as e:
            print(f"Database deletion failed: {e}")
            return False

    def CustomAggregationQuery(self, pipeline):
        """Executes a safe, read-only aggregation pipeline by blocking write-stages like $out and $merge."""
        if not isinstance(pipeline, list):
            raise TypeError("Aggregation pipeline must be passed as a list of dictionaries.")
            
        for stage in pipeline:
            if "$out" in stage or "$merge" in stage:
                raise ValueError("Write operations ($out, $merge) are strictly prohibited in this read-only query.")
                
        try:
            cursor = self.collection.aggregate(pipeline) 
            return list(cursor)
        except Exception as e:
            print(f"Aggregation query failed: {e}")
            return None
        
    def GetRoomPatientsCount(self, room):
        """ returns the total numbers of patients currently in a given room."""
        if not room in RAMBAM_DEPARTMENTS_LIST:
            return 0
        else:
            try:
                return self.collection.count_documents({"location":room}) 
            except Exception as e:
                print(f"Database count failed: {e}")
                return 0
        
    def GetAdministrationTime(self, patientNumber=None):
        """ returns the time of administration of a patient."""
        self.raise_if_illegal(user_data={"patientNumber": patientNumber})

        try:
            if (l:=self.collection.find_one({"patientNumber:":patientNumber}).get("location_history",[])) :
                return str(l[0][1])
            else:
                 return "Patient Not Found"
        except Exception as e:
            print(f"Database count failed: {e}")
            return "Error Communicating with Server"
        
    def GetIdleTime(self, patientNumber=None):
        """ returns the time of administration of a patient."""
        self.raise_if_illegal(user_data={"patientNumber": patientNumber})

        try:
            if (l:=self.collection.find_one({"patientNumber:":patientNumber}).get("location_history",[])) :
                 return str(l[-1][1])
            else:
                return "Patient Not Found" 
        except Exception as e:
            print(f"Database count failed: {e}")
            return "Error Communicating with Server"
        
if __name__ == "__main__":
    y= PatientInfo(patientNumber=1,location="urology")
    print(y)