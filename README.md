# Lost & Found Portal

**UCS310 – Database Management Systems Project**
Thapar Institute of Engineering & Technology | B.Tech 2nd Year | 2025–26

**Group Members:**
- Bhavin Bhatti — 1024030811
- Bhoomi Mittal — 1024030814
- Aatish Kumar Sahu — 10240307

---

## Overview

A centralized database-driven Lost and Found system for a college campus. Built with SQLite, Flask, and Datasette.

**GitHub Pages site:** https://SomaxSoma.github.io/bhavin-db

## Features

- User registration & login (SHA-256 hashing, role-based access)
- Report lost / found items with category, date, and location
- Claim matching — API suggests same-category found items for a lost item
- SQL triggers auto-update item statuses on claim events
- Admin panel — approve/reject claims, view user list & category stats
- Datasette viewer for raw database exploration

## Database Schema

| Table | Description |
|-------|-------------|
| `USER` | Registered users (students + admin) |
| `CATEGORY` | Item categories (Electronics, Wallets, etc.) |
| `LOST_ITEM` | Items reported as lost |
| `FOUND_ITEM` | Items that were turned in |
| `CLAIM` | Links between lost and found items |

Normalised to **3NF/BCNF**. Foreign key constraints enforce referential integrity. Two triggers handle automatic status updates.

## Quick Start

```bash
# Install dependencies
pip install flask sqlite-utils datasette

# Initialise database & start both servers
bash start.sh
```

| Service | URL |
|---------|-----|
| Flask Frontend | http://localhost:5000 |
| Datasette (raw DB) | http://localhost:8001 |

**Demo credentials:**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tiet.edu | admin123 |
| User | bhavin@tiet.edu | bhavin123 |

## Tech Stack

- **Database:** SQLite with triggers & constraints
- **Backend:** Python + Flask
- **DB Viewer:** Datasette
- **Frontend:** Jinja2 templates, custom CSS/JS
