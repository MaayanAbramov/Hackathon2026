import os
from dotenv import load_dotenv
from pymongo import MongoClient

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
    def __init__(self, patientNumber, location):
        """Initializes a new PatientInfo instance with a validated patient number and location."""
        if not isinstance(patientNumber, int):
            raise TypeError(f"patientNumber must be an integer, got {type(patientNumber).__name__} instead.")
        self.__patientNumber = patientNumber
        self.location = location
    
    @property
    def patientNumber(self):
        """Returns the patient's unique identifying number."""
        return self.__patientNumber
    
    @property
    def location(self):
        """Returns the patient's current hospital location."""
        return self.__location
    
    @location.setter
    def location(self, value):
        """Updates the patient's location after verifying the input is a string."""
        if not isinstance(value, str):
            raise TypeError(f"Location must be a string, got {type(value).__name__} instead.")
        self.__location = value

    def __str__(self):
        """Returns a human-readable string representation of the patient's info."""
        return f"PatientInfo(patientNumber={self.__patientNumber}, location='{self.__location}')"
    
    def __repr__(self):
        """Returns a formal string representation of the patient's info."""
        return f"PatientInfo(patientNumber={self.__patientNumber}, location='{self.__location}')"
    
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
                    location=document.get("location")
                )
            else:
                return None

        except Exception as e:
            print(f"Database query failed: {e}")
            return None

    def UpdatePatientLocation(self, patientNumber = None, new_location = None):
        """Updates an existing patient's location in the database and returns the updated object."""
        p_info = self.SearchForPatient(patientNumber=patientNumber)
        if p_info is None:
            raise LookupError(f"An error occoured , Patient patientNumber = {patientNumber} was not found in database records.")
        else:
            self.raise_if_illegal(user_data={"patientNumber": patientNumber, "location": new_location})
            try:
                self.collection.update_one(
                    {"patientNumber": patientNumber}, 
                    {"$set": {"location": new_location}}
                )
                p_info.location = new_location
                print(f"Successfully updated Patient {patientNumber}'s location to {new_location}")
                return p_info
            except Exception as e:
                print(f"Database update failed: {e}")
                return None

    def InsertNewPatient(self, patientNumber=None, location=None):
        """Validates and inserts a completely new patient record into the database."""
        existing_patient = self.SearchForPatient(patientNumber=patientNumber)
        if existing_patient is not None:
            raise ValueError(f"Cannot insert: Patient patientNumber {patientNumber} already exists in the database.")
        
        user_data = {"patientNumber": patientNumber, "location": location}
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
if __name__ == "__main__":
    print("hola")