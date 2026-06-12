# constants.py
from enum import Enum

PERMITTED_FIELDS = ["patientNumber", "location", "location_history", "routing_path"]

FIELD_TO_PERMITTED_TYPE = {"patientNumber": int, "location": str, "location_history": list , "routing_path": list}

RAMBAM_DEPARTMENTS_LIST = [
    "oncology", "urology", "orthopedics", "pediatric orthopedics",
    "otolaryngology (ent)", "gastroenterology", "geriatrics", "hematology",
    "organ transplantation", "general intensive care", "pediatric intensive care",
    "cardiac intensive care unit", "maternity and gynecology", "general surgery a",
    "general surgery b", "pediatric surgery", "plastic surgery",
    "cardiothoracic surgery", "vascular surgery", "oral and maxillofacial surgery",
    "neurology", "pediatrics a", "pediatrics b", "nephrology", "neurosurgery",
    "dermatology", "ophthalmology", "internal medicine a", "internal medicine b",
    "internal medicine c", "internal medicine d", "internal medicine e",
    "internal medicine f", "psychiatry", "neonatal intensive care unit (nicu)",
    "cardiology", "rheumatology", "pulmonology", "emergency medicine",
    "pediatric emergency medicine", "rehabilitation"
]

class PRESET_QUERIES(Enum):
    Locate_Patient = 1 
    Room_Occupancy = 2
    Total_Occupancy = 3
    Administration_Time = 4
    Idle_Time = 5
    Other = 6

# PRESET_QUERIES = ["Locate Patient", "Room Occupancy", "Total Occupancy", "Administration Time", "Idle Time", "Other"]

# Database Configurations
DB_NAME = 'Hackathon'
COLLECTION_NAME = 'HackathonData'
