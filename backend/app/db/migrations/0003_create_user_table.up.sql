-- Migration: Create User Table and Seed Initial Users
-- Version: 0003

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'cashier',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);

-- Seed initial users (admin/admin123, cashier/cashier123)
-- Role: owner, manager, cashier
INSERT INTO user (username, hashed_password, full_name, role) 
VALUES 
('admin', '$2b$12$Cit7eB22IGOzLRBvhG0sB.U4BYZYX4sLvZoZOSzR.up2R3TlnaI1i', 'Administrator', 'owner'),
('cashier', '$2b$12$lq.iB8mYuLXfgIoaD6l4Q.6XgFhKJNiapZH3KyZEeTrRvA10NUYKO', 'Cashier One', 'cashier');
