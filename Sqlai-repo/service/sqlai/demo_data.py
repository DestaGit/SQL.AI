"""Seed the local DuckDB warehouse with fictional demo data (same shape as the standalone demo)."""
from __future__ import annotations

import datetime as dt
import random
import sys
from pathlib import Path

import duckdb

FIRST = ["Ana", "Ben", "Chloe", "Diego", "Elif", "Farah", "Gus", "Hana", "Ivan", "Jade", "Kofi", "Lena", "Mateo", "Nora",
         "Omar", "Pia", "Quinn", "Rosa", "Sven", "Tara", "Uma", "Vik", "Wen", "Yusuf", "Zoe", "Leo", "Mia", "Noah", "Ines", "Ravi"]
LAST = ["Alvarez", "Berg", "Chen", "Dubois", "Eriksen", "Fischer", "Gallo", "Haddad", "Ito", "Jensen", "Kowalski", "Lindqvist",
        "Moreau", "Nakamura", "Okoro", "Patel", "Quint", "Rossi", "Silva", "Tanaka", "Ueda", "Varga", "Weber", "Xu", "Yilmaz", "Zimmer"]
COUNTRIES = {"NA": ["US", "Canada", "Mexico"], "EU": ["Germany", "France", "Spain", "Netherlands", "Sweden"],
             "APAC": ["Japan", "Australia", "Singapore", "India"]}
PRODUCTS = ["Workbench seats", "Policy pack", "Audit add-on", "Warehouse connector"]
DEPTS = {"Sales": ("Account executive", 95000), "Support": ("Support engineer", 72000), "Engineering": ("Software engineer", 142000),
         "Finance": ("Financial analyst", 98000), "HR": ("People partner", 88000), "Marketing": ("Marketing manager", 104000)}


def _w(r: random.Random, pairs):
    x, s = r.random(), 0.0
    for v, w in pairs:
        s += w
        if x < s:
            return v
    return pairs[-1][0]


def _between(r: random.Random, a: dt.date, b: dt.date) -> dt.date:
    return a + dt.timedelta(days=r.randint(0, (b - a).days))


def seed(path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    r = random.Random(20261014)
    D = dt.date
    customers, orders, tickets, employees = [], [], [], []
    for i in range(240):
        cid = 1001 + i
        f, l = r.choice(FIRST), r.choice(LAST)
        region = _w(r, [("NA", .45), ("EU", .35), ("APAC", .2)])
        signup = _between(r, D(2025, 1, 5), D(2026, 9, 20))
        status, churn = "active", None
        if r.random() < .2 and signup < D(2026, 8, 1):
            status = "churned"
            churn = _between(r, max(signup + dt.timedelta(days=30), D(2025, 6, 1)), D(2026, 9, 30))
        customers.append((cid, f"{f} {l}", f"{f}.{l}{cid % 97}".lower() + "@example.com", f"+1 555-0{r.randint(0, 999):03d}",
                          region, r.choice(COUNTRIES[region]), _w(r, [("Free", .45), ("Pro", .4), ("Enterprise", .15)]), signup, status, churn))
    paying = [c for c in customers if c[6] != "Free"]
    oid = 50001
    for _ in range(1500):
        c = r.choice(paying)
        start, end = max(c[7], D(2026, 1, 1)), c[9] or D(2026, 9, 30)
        if start > end:
            continue
        amt = 2000 + r.random() * 16000 if c[6] == "Enterprise" else 200 + r.random() * 1300
        orders.append((oid, c[0], _between(r, start, end), r.choice(PRODUCTS), round(amt, 2), c[4]))
        oid += 1
    for i in range(520):
        c = r.choice(customers)
        tickets.append((70001 + i, c[0], _between(r, D(2026, 1, 1), D(2026, 9, 30)),
                        _w(r, [("Access", .24), ("Billing", .18), ("Data quality", .22), ("Bug", .2), ("How-to", .16)]),
                        _w(r, [("Low", .35), ("Medium", .4), ("High", .2), ("Urgent", .05)]),
                        r.randint(1, 5) if r.random() < .7 else None, c[4]))
    for i in range(48):
        d = r.choice(list(DEPTS))
        title, base = DEPTS[d]
        employees.append((501 + i, f"{r.choice(FIRST)} {r.choice(LAST)}", d, title, _w(r, [("NA", .5), ("EU", .35), ("APAC", .15)]),
                          int(round(base * (.8 + r.random() * .45) / 500) * 500),
                          f"9{r.randint(0, 99):02d}-{r.randint(0, 99):02d}-{r.randint(0, 9999):04d}", _between(r, D(2018, 3, 1), D(2026, 8, 30))))
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE customers (customer_id INTEGER, full_name VARCHAR, email VARCHAR, phone VARCHAR, region VARCHAR, country VARCHAR, tier VARCHAR, signup_date DATE, status VARCHAR, churn_date DATE)")
    con.execute("CREATE TABLE orders (order_id INTEGER, customer_id INTEGER, order_date DATE, product VARCHAR, amount DOUBLE, region VARCHAR)")
    con.execute("CREATE TABLE tickets (ticket_id INTEGER, customer_id INTEGER, opened_date DATE, category VARCHAR, priority VARCHAR, csat INTEGER, region VARCHAR)")
    con.execute("CREATE TABLE employees (employee_id INTEGER, full_name VARCHAR, department VARCHAR, title VARCHAR, region VARCHAR, salary INTEGER, ssn VARCHAR, hire_date DATE)")
    con.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?)", customers)
    con.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
    con.executemany("INSERT INTO tickets VALUES (?,?,?,?,?,?,?)", tickets)
    con.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?)", employees)
    con.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/warehouse.duckdb"
    seed(target)
    print(f"Seeded fictional demo data into {target}")
