-- PostgreSQL MCP Server Test Database Initialization
-- This script creates test tables and sample data for testing

-- Create test tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES
('testuser1', 'test1@example.com'),
('testuser2', 'test2@example.com'),
('testuser3', 'test3@example.com')
ON CONFLICT (username) DO NOTHING;

INSERT INTO products (name, price, description) VALUES
('Laptop', 999.99, 'High-performance laptop'),
('Mouse', 29.99, 'Wireless mouse'),
('Keyboard', 79.99, 'Mechanical keyboard'),
('Monitor', 299.99, '27-inch 4K monitor')
ON CONFLICT (name) DO NOTHING;

INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES
(1, 1, 1, 999.99),
(1, 2, 2, 59.98),
(2, 3, 1, 79.99),
(3, 4, 1, 299.99)
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;
