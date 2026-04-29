from __future__ import annotations


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_id INTEGER NOT NULL,
    invoice_month TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    plan_name TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    resolution_hours REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
"""


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    invoice_month DATE NOT NULL,
    amount_usd NUMERIC(12, 2) NOT NULL,
    plan_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id INTEGER PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'demo',
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    created_at DATE NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    resolution_hours NUMERIC(8, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_workspace_id ON invoices(workspace_id);
CREATE INDEX IF NOT EXISTS idx_invoices_month ON invoices(invoice_month);
CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_workspace_id ON support_tickets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_priority ON support_tickets(priority);
"""
