# constants.py

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

# Database Configurations
DB_NAME = 'Hackathon'
COLLECTION_NAME = 'HackathonData'

test ="yipee"