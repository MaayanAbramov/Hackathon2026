import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
db_string = os.getenv("DATABASE_URL")
from pymongo import MongoClient

class PatientInfo:
    def __init__(self, patientNumber, location):
        if not isinstance(patientNumber, int):
            raise TypeError(f"patientNumber must be an integer, got {type(patientNumber).__name__} instead.")
        self.__patientNumber = patientNumber
        self.location = location
    
    @property
    def patientNumber(self):
        return self.__patientNumber
    
    @property
    def location(self):
        return self.__location
    
    @location.setter
    def location(self, value):
        # Enforce that the new value is a string
        if not isinstance(value, str):
            raise TypeError(f"Location must be a string, got {type(value).__name__} instead.")
        
        # If it passes the check, save it to the internal private variable
        self.__location = value

    def __str__(self):
        return f"PatientInfo(patientNumber={self.__patientNumber}, location='{self.__location}')"
    def __repr__(self):
        return f"PatientInfo(patientNumber={self.__patientNumber}, location='{self.__location}')"
    
class DB_API:
    permitted_fields = ["patientNumber", "location"]
    field_to_permitted_type = {"patientNumber": int, "location": str}
    rambam_departments_list = [
    "oncology",
    "urology",
    "orthopedics",
    "pediatric orthopedics",
    "otolaryngology (ent)",
    "gastroenterology",
    "geriatrics",
    "hematology",
    "organ transplantation",
    "general intensive care",
    "pediatric intensive care",
    "cardiac intensive care unit",
    "maternity and gynecology",
    "general surgery a",
    "general surgery b",
    "pediatric surgery",
    "plastic surgery",
    "cardiothoracic surgery",
    "vascular surgery",
    "oral and maxillofacial surgery",
    "neurology",
    "pediatrics a",
    "pediatrics b",
    "nephrology",
    "neurosurgery",
    "dermatology",
    "ophthalmology",
    "internal medicine a",
    "internal medicine b",
    "internal medicine c",
    "internal medicine d",
    "internal medicine e",
    "internal medicine f",
    "psychiatry",
    "neonatal intensive care unit (nicu)",
    "cardiology",
    "rheumatology",
    "pulmonology",
    "emergency medicine",
    "pediatric emergency medicine",
    "rehabilitation"
]
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.client = MongoClient(db_string)
            cls.db = cls.client['Hackathon']
            cls.collection = cls.db['HackathonData']
        return cls._instance

    def raise_if_illegal(self, user_data):
        if not isinstance(user_data, dict):
            raise TypeError(f"user_data must be passed as dictionary, not as {type(user_data)}")
        for k, v in user_data.items():
            if v is None:
                raise ValueError(f"In user_data : {user_data}\nThe value for key '{k}' cannot be None")
            if not k in DB_API.permitted_fields:
                raise ValueError(f"In user_data : {user_data}.\nKey '{k}' is not in {DB_API.permitted_fields}")
            if not type(v) == DB_API.field_to_permitted_type.get(k, None):
                raise ValueError(f"In user_data : {user_data}\nValue '{v}' (associated with key '{k}') type is {type(v)} and the program expected it to be {DB_API.field_to_permitted_type.get(k, None)}")
            if k == "patientNumber" and not 0 < v < 9223372036854775807 :
                raise ValueError(f"Patient patientNumber must be with value greater than 0, got {v}")
            if k == "location" and v.lower() not in DB_API.rambam_departments_list:
                raise ValueError(f"Location value must be a legal value within the following list {DB_API.rambam_departments_list}")
    def SearchForPatient(self, patientNumber):
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
        
        p_info = self.SearchForPatient(patientNumber=patientNumber)
        if p_info is None:
            raise LookupError(f"An error occoured , Patient patientNumber = {patientNumber} was not found in database records.")
        else:
            # 2. Validate the new data before hitting the database
            self.raise_if_illegal(user_data={"patientNumber": patientNumber, "location": new_location})
            
            try:
                # 3. Update the document in MongoDB
                # The first dictionary is the filter (find the document)
                # The second dictionary uses "$set" to change specific fields
                self.collection.update_one(
                    {"patientNumber": patientNumber}, 
                    {"$set": {"location": new_location}}
                )
                
                # 4. Update your local Python object and return it
                p_info.location = new_location
                print(f"Successfully updated Patient {patientNumber}'s location to {new_location}")
                return p_info
                
            except Exception as e:
                print(f"Database update failed: {e}")
                return None

    def InsertNewPatient(self, patientNumber=None, location=None):
        # 1. Check if the patient already exists to prevent duplicates
        existing_patient = self.SearchForPatient(patientNumber=patientNumber)
        if existing_patient is not None:
            # If SearchForPatient returns an object, the patient is already in the DB
            raise ValueError(f"Cannot insert: Patient patientNumber {patientNumber} already exists in the database.")
        
        # 2. Prepare the data and validate it
        user_data = {"patientNumber": patientNumber, "location": location}
        self.raise_if_illegal(user_data=user_data)

        try:
            # 3. Insert the new document into MongoDB
            self.collection.insert_one(user_data)
            print(f"Successfully inserted new Patient {patientNumber} at location '{location}'.")
            
            # 4. Return the new PatientInfo object
            return PatientInfo(patientNumber=patientNumber, location=location)

        except Exception as e:
            print(f"Database insertion failed: {e} ")
            return None
        
if __name__ == "__main__":
     print("Hola señor") 