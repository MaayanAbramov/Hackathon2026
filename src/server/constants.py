# constants.py
from enum import Enum

PERMITTED_FIELDS = ["patientNumber", "location"]

FIELD_TO_PERMITTED_TYPE = {"patientNumber": int, "location": str}

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
    Locate_Patient = 0
    Room_Occupancy = 1
    Total_Occupancy = 2
    Administration_Time = 3
    Idle_Time = 4
    Other = 5

# PRESET_QUERIES = ["Locate Patient", "Room Occupancy", "Total Occupancy", "Administration Time", "Idle Time", "Other"]

# Database Configurations
DB_NAME = 'Hackathon'
COLLECTION_NAME = 'HackathonData'
