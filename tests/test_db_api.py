import pytest
from unittest.mock import patch, MagicMock

# Assuming your main script is named db_api.py
from db_api import DB_API, PatientInfo

@pytest.fixture(autouse=True)
def mock_mongo_client():
    """
    Automatically mocks the MongoClient for all tests so we don't 
    accidentally hit a real database during edge-case testing.
    """
    with patch('db_api.MongoClient') as mock_client:
        # Reset the Singleton instance before each test to ensure a clean slate
        DB_API._instance = None 
        yield mock_client

## --- PatientInfo Edge Cases ---

def test_patient_info_invalid_id_type():
    # Edge Case: Passing a float or string instead of an int for patientNumber
    with pytest.raises(TypeError, match="must be an integer"):
        PatientInfo(patientNumber=123.45, location="oncology")

def test_patient_info_invalid_location_type():
    # Edge Case: Setting location to an int or None
    p = PatientInfo(patientNumber=123, location="oncology")
    with pytest.raises(TypeError, match="Location must be a string"):
        p.location = 404

## --- DB_API Data Validation Edge Cases ---

def test_raise_if_illegal_non_dict_input():
    db = DB_API()
    # Edge Case: Passing a list or string instead of a dictionary
    with pytest.raises(TypeError, match="must be passed as dictionary"):
        db.raise_if_illegal(["patientNumber", 123])

def test_raise_if_illegal_none_values():
    db = DB_API()
    # Edge Case: Dictionary has permitted keys, but None values
    with pytest.raises(ValueError, match="cannot be None"):
        db.raise_if_illegal({"patientNumber": None})

def test_raise_if_illegal_unpermitted_keys():
    db = DB_API()
    # Edge Case: User tries to inject an extra, unpermitted field
    with pytest.raises(ValueError, match="is not in"):
        db.raise_if_illegal({"patientNumber": 123, "location": "urology", "bloodType": "O-"})

def test_raise_if_illegal_patient_number_bounds():
    db = DB_API()
    # Edge Case: patientNumber is 0 (boundary)
    with pytest.raises(ValueError, match="must be with value greater than 0"):
        db.raise_if_illegal({"patientNumber": 0})
        
    # Edge Case: patientNumber is negative
    with pytest.raises(ValueError, match="must be with value greater than 0"):
        db.raise_if_illegal({"patientNumber": -5})

def test_raise_if_illegal_unrecognized_location():
    db = DB_API()
    # Edge Case: Valid string, but not a recognized department
    with pytest.raises(ValueError, match="must be a legal value"):
        db.raise_if_illegal({"location": "cafeteria"})

def test_raise_if_illegal_location_case_insensitivity():
    db = DB_API()
    # Edge Case: Ensure the validation accepts weird casing (since you use .lower())
    # This should NOT raise an exception
    try:
        db.raise_if_illegal({"location": "UrOlOgY"})
    except ValueError:
        pytest.fail("raise_if_illegal raised ValueError unexpectedly on mixed-case location.")

## --- DB_API Aggregation Security Edge Cases ---

def test_custom_aggregation_invalid_type():
    db = DB_API()
    # Edge Case: Passing a dictionary instead of a list of dictionaries
    with pytest.raises(TypeError, match="must be passed as a list"):
        db.CustomAggregationQuery({"$match": {"location": "oncology"}})

def test_custom_aggregation_blocks_out():
    db = DB_API()
    # Edge Case: Malicious attempt to write data using $out
    malicious_pipeline = [
        {"$match": {"location": "urology"}},
        {"$out": "hacked_collection"}
    ]
    with pytest.raises(ValueError, match="strictly prohibited"):
        db.CustomAggregationQuery(malicious_pipeline)

def test_custom_aggregation_blocks_merge():
    db = DB_API()
    # Edge Case: Malicious attempt to write data using $merge
    malicious_pipeline = [
        {"$group": {"_id": "$location"}},
        {"$merge": "hacked_collection"}
    ]
    with pytest.raises(ValueError, match="strictly prohibited"):
        db.CustomAggregationQuery(malicious_pipeline)

## --- DB_API Singleton Verification ---

def test_singleton_pattern():
    # Edge Case: Ensure multiple instantiations don't create multiple DB connections
    db1 = DB_API()
    db2 = DB_API()
    assert db1 is db2, "DB_API is not acting as a true Singleton!"