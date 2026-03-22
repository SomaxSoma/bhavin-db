import sqlite3
from datetime import date, timedelta
import hashlib

DB_PATH = "lost_found.db"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS USER (
        User_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
        Name      TEXT    NOT NULL,
        Email     TEXT    NOT NULL UNIQUE,
        Phone     TEXT,
        Password  TEXT    NOT NULL,
        Role      TEXT    NOT NULL DEFAULT 'user' CHECK(Role IN ('user','admin'))
    );

    CREATE TABLE IF NOT EXISTS CATEGORY (
        Category_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
        Category_Name TEXT    NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS LOST_ITEM (
        Lost_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
        Item_Name   TEXT    NOT NULL,
        Description TEXT,
        Date_Lost   TEXT    NOT NULL,
        Location    TEXT,
        Status      TEXT    NOT NULL DEFAULT 'Lost' CHECK(Status IN ('Lost','Matched','Returned')),
        User_ID     INTEGER NOT NULL,
        Category_ID INTEGER,
        FOREIGN KEY (User_ID)     REFERENCES USER(User_ID),
        FOREIGN KEY (Category_ID) REFERENCES CATEGORY(Category_ID)
    );

    CREATE TABLE IF NOT EXISTS FOUND_ITEM (
        Found_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
        Item_Name   TEXT    NOT NULL,
        Description TEXT,
        Date_Found  TEXT    NOT NULL,
        Location    TEXT,
        Status      TEXT    NOT NULL DEFAULT 'Unclaimed' CHECK(Status IN ('Unclaimed','Claimed','Returned')),
        User_ID     INTEGER NOT NULL,
        Category_ID INTEGER,
        FOREIGN KEY (User_ID)     REFERENCES USER(User_ID),
        FOREIGN KEY (Category_ID) REFERENCES CATEGORY(Category_ID)
    );

    CREATE TABLE IF NOT EXISTS CLAIM (
        Claim_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
        Lost_ID    INTEGER NOT NULL,
        Found_ID   INTEGER NOT NULL,
        Status     TEXT    NOT NULL DEFAULT 'Pending' CHECK(Status IN ('Pending','Approved','Rejected')),
        Claimed_On TEXT    NOT NULL DEFAULT (DATE('now')),
        FOREIGN KEY (Lost_ID)  REFERENCES LOST_ITEM(Lost_ID),
        FOREIGN KEY (Found_ID) REFERENCES FOUND_ITEM(Found_ID)
    );

    -- Trigger: when a claim is approved, update both item statuses
    CREATE TRIGGER IF NOT EXISTS trg_claim_approved
    AFTER UPDATE OF Status ON CLAIM
    WHEN NEW.Status = 'Approved'
    BEGIN
        UPDATE LOST_ITEM  SET Status = 'Returned' WHERE Lost_ID  = NEW.Lost_ID;
        UPDATE FOUND_ITEM SET Status = 'Returned' WHERE Found_ID = NEW.Found_ID;
    END;

    -- Trigger: mark items as Matched when a claim is created (Pending)
    CREATE TRIGGER IF NOT EXISTS trg_claim_pending
    AFTER INSERT ON CLAIM
    BEGIN
        UPDATE LOST_ITEM  SET Status = 'Matched' WHERE Lost_ID  = NEW.Lost_ID;
        UPDATE FOUND_ITEM SET Status = 'Claimed' WHERE Found_ID = NEW.Found_ID;
    END;
    """)

    # Seed categories
    categories = [
        "Electronics", "Wallets & Bags", "ID Cards & Documents",
        "Keys", "Clothing", "Books & Stationery", "Jewellery", "Others"
    ]
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO CATEGORY(Category_Name) VALUES (?)", (cat,))

    # Seed users
    users = [
        ("Admin User",   "admin@tiet.edu",   "9000000000", hash_password("admin123"),   "admin"),
        ("Bhavin Bhatti","bhavin@tiet.edu",  "9876543210", hash_password("bhavin123"),  "user"),
        ("Bhoomi Mittal","bhoomi@tiet.edu",  "9876543211", hash_password("bhoomi123"),  "user"),
        ("Aatish Sahu",  "aatish@tiet.edu",  "9876543212", hash_password("aatish123"),  "user"),
        ("Rahul Sharma", "rahul@tiet.edu",   "9123456789", hash_password("rahul123"),   "user"),
        ("Priya Singh",  "priya@tiet.edu",   "9234567890", hash_password("priya123"),   "user"),
    ]
    for u in users:
        c.execute("INSERT OR IGNORE INTO USER(Name,Email,Phone,Password,Role) VALUES (?,?,?,?,?)", u)

    today = date.today()
    def dago(n): return (today - timedelta(days=n)).isoformat()

    # Seed lost items
    lost_items = [
        ("Blue JBL Earphones", "Left them in the library reading room",          dago(5),  "Main Library",         2, 1),
        ("Student ID Card",    "ID card of Roll No 1024030811",                  dago(3),  "Cafeteria",            2, 3),
        ("Black Wallet",       "Leather wallet with some cash and cards",         dago(7),  "Sports Complex",       3, 2),
        ("Physics Textbook",   "Halliday Resnick, name written inside",           dago(2),  "Lecture Hall B-Block", 4, 6),
        ("Silver Ring",        "Plain silver ring with a small stone",            dago(10), "Hostel A",             5, 7),
        ("Laptop Bag",         "Dell laptop bag, dark blue, charger inside",      dago(1),  "Seminar Hall",         6, 2),
        ("Bunch of Keys",      "4 keys on a Thapar keychain",                    dago(4),  "Parking Lot",          3, 4),
        ("Spectacles",         "Black frame glasses in a brown case",             dago(6),  "Canteen",              4, 8),
    ]
    for item in lost_items:
        c.execute("""INSERT OR IGNORE INTO LOST_ITEM
                     (Item_Name,Description,Date_Lost,Location,User_ID,Category_ID)
                     VALUES (?,?,?,?,?,?)""", item)

    # Seed found items
    found_items = [
        ("JBL Earphones",      "Found near reading room table",                  dago(4),  "Main Library",         5, 1),
        ("ID Card",            "Found on cafeteria table, Thapar ID",            dago(3),  "Cafeteria",            6, 3),
        ("Brown Wallet",       "Wallet found near gym entrance",                 dago(6),  "Sports Complex",       2, 2),
        ("Physics Book",       "Found in lecture hall, has student name inside", dago(1),  "Lecture Hall B-Block", 3, 6),
        ("Silver Ring",        "Small silver ring found on stairs",              dago(9),  "Hostel A Block",       4, 7),
        ("Blue Laptop Bag",    "Dell bag with laptop charger, found in hall",    dago(1),  "Seminar Hall",         5, 2),
        ("Wired Earphones",    "White earphones found in corridor",              dago(8),  "Academic Block",       6, 1),
        ("Red Umbrella",       "Umbrella left in classroom",                     dago(12), "Room 204 C-Block",     2, 8),
    ]
    for item in found_items:
        c.execute("""INSERT OR IGNORE INTO FOUND_ITEM
                     (Item_Name,Description,Date_Found,Location,User_ID,Category_ID)
                     VALUES (?,?,?,?,?,?)""", item)

    # Seed claims
    claims = [
        (1, 1, "Approved", dago(2)),  # earphones matched
        (2, 2, "Approved", dago(1)),  # ID card matched
        (3, 3, "Pending",  dago(5)),  # wallet pending
        (4, 4, "Pending",  dago(0)),  # book pending
    ]
    for cl in claims:
        c.execute("""INSERT OR IGNORE INTO CLAIM(Lost_ID,Found_ID,Status,Claimed_On)
                     VALUES (?,?,?,?)""", cl)

    conn.commit()
    conn.close()
    print("Database initialised at", DB_PATH)

if __name__ == "__main__":
    init()
