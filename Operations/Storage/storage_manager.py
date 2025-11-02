import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

DB_CLUSTER = os.getenv("DB_CLUSTER")
DB_NAME = os.getenv("DB_NAME")
DB_COLLECTION = os.getenv("DB_COLLECTION")

# Connect to MongoDB
cluster = MongoClient(DB_CLUSTER)
db = cluster[DB_NAME]
collection = db[DB_COLLECTION]


# ------------------------------
# 🟢 INSERT (Push Data)
# ------------------------------
def insert_one(data: Dict[str, Any]):
    """Insert a single document into the MongoDB collection."""
    result = collection.insert_one(data)
    print(f"✅ Inserted document with _id: {result.inserted_id}")
    return result.inserted_id


def insert_many(data_list: List[Dict[str, Any]]):
    """Insert multiple documents into the MongoDB collection."""
    result = collection.insert_many(data_list)
    print(f"✅ Inserted {len(result.inserted_ids)} documents.")
    return result.inserted_ids


# ------------------------------
# 🔵 RETRIEVE (Get Data)
# ------------------------------
def get_all():
    """Retrieve all documents from the collection."""
    data = list(collection.find({}, {"_id": 0}))  # exclude _id for clarity
    print(f"📄 Retrieved {len(data)} documents.")
    return data

def get_by_link(link: str):
    """Retrieve documents matching a specific link (e.g., 'https://www.youtube.com')."""
    data = list(collection.find({"link": link}, {"_id": 0}))
    print(f"📄 Found {len(data)} documents with status '{link}'.")
    return data


# ------------------------------
# 🟠 UPDATE (Modify Data)
# ------------------------------
def update_status(title: str, new_status: str):
    """Update the status of a document based on its title."""
    result = collection.update_one({"title": title}, {"$set": {"status": new_status}})
    if result.modified_count > 0:
        print(f"✅ Updated status for '{title}' → {new_status}")
    else:
        print(f"⚠️ No document found with title '{title}'.")


def update_reminder(title: str, reminder_state: bool):
    """Update the reminder field for a given title."""
    result = collection.update_one({"title": title}, {"$set": {"reminder": reminder_state}})
    if result.modified_count > 0:
        print(f"✅ Updated reminder for '{title}' → {reminder_state}")
    else:
        print(f"⚠️ No document found with title '{title}'.")


# ------------------------------
# 🧹 OPTIONAL: DELETE (Cleanup)
# ------------------------------
def delete_by_title(title: str):
    """Delete a document based on title."""
    result = collection.delete_one({"title": title})
    if result.deleted_count > 0:
        print(f"🗑️ Deleted '{title}' successfully.")
    else:
        print(f"⚠️ No document found with title '{title}'.")


# # ------------------------------
# # 🧪 SAMPLE USAGE
# # ------------------------------

# print(get_by_link("https://www.metacareers.com/login"))