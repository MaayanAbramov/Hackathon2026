import pytest
from unittest.mock import patch
from src.server.DB_API import DB_API, PatientInfo
from src.server.constants import PRESET_QUERIES
import requests

FLASK_URL = "http://132.68.34.90:5000"

# =====================================================================
# FIXTURES (Choose which one to use for each test!)
# =====================================================================

@pytest.fixture
def mock_db():
    """
    UNIT TEST FIXTURE: Fakes the database connection. 
    Use this for testing data validation and logic instantly without a network.
    """
    with patch('src.server.DB_API.MongoClient') as mock_client:
        DB_API._instance = None 
        yield mock_client


@pytest.fixture
def real_test_db():
    """
    INTEGRATION TEST FIXTURE: Connects to the real database's 'hackathon_test' collection.
    Use this ONLY when testing actual read/write operations to the DB.
    """
    from src.server.DB_API import db_string 
    fast_fail_db_string = f"{db_string}{'&' if '?' in db_string else '?'}serverSelectionTimeoutMS=2000"

    with patch('src.server.DB_API.COLLECTION_NAME', 'hackathon_test'), \
         patch('src.server.DB_API.db_string', fast_fail_db_string):
             
        DB_API._instance = None 
        yield 
        
        if DB_API._instance is not None:
            try:
                DB_API._instance.collection.delete_many({})
            except Exception as e:
                print(f"\n[!] Teardown skipped: Could not reach database ({e})")
            finally:
                DB_API._instance.client.close()

# =====================================================================
# 1. PURE LOGIC TESTS (No database needed at all)
# =====================================================================

def test_patient_info_invalid_id_type():
    with pytest.raises(TypeError, match="must be an integer"):
        PatientInfo(patientNumber=123.45, location="oncology")

def test_patient_info_invalid_location_type():
    p = PatientInfo(patientNumber=123, location="oncology")
    with pytest.raises(TypeError, match="Location must be a string"):
        p.location = 404


# =====================================================================
# 2. VALIDATION TESTS (Fast - Uses 'mock_db')
# =====================================================================

def test_raise_if_illegal_non_dict_input(mock_db):
    db = DB_API()
    with pytest.raises(TypeError, match="must be passed as dictionary"):
        db.raise_if_illegal(["patientNumber", 123])

def test_raise_if_illegal_none_values(mock_db):
    db = DB_API()
    with pytest.raises(ValueError, match="cannot be None"):
        db.raise_if_illegal({"patientNumber": None})

def test_raise_if_illegal_unpermitted_keys(mock_db):
    db = DB_API()
    with pytest.raises(ValueError, match="is not in"):
        db.raise_if_illegal({"patientNumber": 123, "location": "urology", "bloodType": "O-"})

def test_raise_if_illegal_patient_number_bounds(mock_db):
    db = DB_API()
    with pytest.raises(ValueError, match="must be with value greater than 0"):
        db.raise_if_illegal({"patientNumber": 0})
    with pytest.raises(ValueError, match="must be with value greater than 0"):
        db.raise_if_illegal({"patientNumber": -5})

def test_raise_if_illegal_unrecognized_location(mock_db):
    db = DB_API()
    with pytest.raises(ValueError, match="must be a legal value"):
        db.raise_if_illegal({"location": "cafeteria"})

def test_raise_if_illegal_location_case_insensitivity(mock_db):
    db = DB_API()
    try:
        db.raise_if_illegal({"location": "UrOlOgY"})
    except ValueError:
        pytest.fail("raise_if_illegal raised ValueError unexpectedly on mixed-case location.")

def test_custom_aggregation_blocks_out(mock_db):
    db = DB_API()
    malicious_pipeline = [{"$match": {"location": "urology"}}, {"$out": "hacked_collection"}]
    with pytest.raises(ValueError, match="strictly prohibited"):
        db.CustomAggregationQuery(malicious_pipeline)

def test_singleton_pattern(mock_db):
    db1 = DB_API()
    db2 = DB_API()
    assert db1 is db2, "DB_API is not acting as a true Singleton!"


# =====================================================================
# 3. INTEGRATION TESTS (Slower - Uses 'real_test_db')
# =====================================================================

def test_insert_and_search_patient(real_test_db):
    db = DB_API()
    
    # Insert a new patient
    new_patient = db.InsertNewPatient(patientNumber=999, location="urology")
    assert new_patient is not None
    assert new_patient.patientNumber == 999
    
    # Search for that exact patient
    found_patient = db.SearchForPatient(patientNumber=999)
    assert found_patient is not None
    assert found_patient.location == "urology"

def test_update_patient_location(real_test_db):
    pass
    db = DB_API()
    
    # Insert first
    db.InsertNewPatient(patientNumber=888, location="oncology")
    
    # Update location
    updated_patient = db.UpdatePatientLocation(patientNumber=888, new_location="cardiology")
    assert updated_patient is not None
    assert updated_patient.location == "cardiology"

def test_remove_patient(real_test_db):
    pass
    db = DB_API()
    
    # Insert first
    db.InsertNewPatient(patientNumber=777, location="neurology")
    
    # Delete them
    success = db.RemovePatient(patientNumber=777)
    assert success is True
    
    # Verify they are gone
    should_be_none = db.SearchForPatient(patientNumber=777)
    assert should_be_none is None

    # =====================================================================
    # 4. FLASK TESTS (Slower - Uses 'real_test_db')
    # =====================================================================

# def test_find_patient_basic(real_test_db):
#     db = DB_API()
    
#     payload = {
#         "request": PRESET_QUERIES.Locate_Patient,
#         "message": 1234
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] is None

#     db.InsertNewPatient(patientNumber=1234, location="plastic surgery")
    
#     payload = {
#         "request": PRESET_QUERIES.Locate_Patient,
#         "message": 1234
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] is not None

#     payload = {
#         "request": PRESET_QUERIES.Locate_Patient,
#         "message": "1234"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] is not None

#     payload = {
#         "request": PRESET_QUERIES.Locate_Patient,
#         "message": "1234a"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 500

# def test_room_occupancy_basic(real_test_db):
#     db = DB_API()
    
#     payload = {
#         "request": PRESET_QUERIES.Room_Occupancy,
#         "message": "plastic surgery"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] == 0

#     db.InsertNewPatient(patientNumber=1234, location="plastic surgery")
    
#     payload = {
#         "request": PRESET_QUERIES.Room_Occupancy,
#         "message": "plastic surgery"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] == 1

#     db.RemovePatient(patientNumber=1234)
    
#     payload = {
#         "request": PRESET_QUERIES.Room_Occupancy,
#         "message": "plastic surgery"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] == 0

#     payload = {
#         "request": PRESET_QUERIES.Room_Occupancy.value,
#         "message": "plastic surgery aaaaaaaaaaaaa"
#     }

#     response = requests.post(FLASK_URL+"/api/ask", json=payload)
#     assert response.status_code == 200
#     assert response.json()["response"] == 0

    