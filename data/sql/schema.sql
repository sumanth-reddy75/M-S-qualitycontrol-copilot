-- =============================================================================
-- Multi-Source RAG + Text-to-SQL Database Schema
-- E-commerce database: customers, products, orders
-- =============================================================================

-- -------------------------
-- Table: customers
-- -------------------------
CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)        NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    segment         VARCHAR(50)         NOT NULL CHECK (segment IN ('SMB', 'Enterprise', 'Individual')),
    country         VARCHAR(100)        NOT NULL DEFAULT 'USA',
    created_at      TIMESTAMP           NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_segment  ON customers (segment);
CREATE INDEX IF NOT EXISTS idx_customers_country  ON customers (country);
CREATE INDEX IF NOT EXISTS idx_customers_email    ON customers (email);

-- -------------------------
-- Table: products
-- -------------------------
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)        NOT NULL,
    category        VARCHAR(100)        NOT NULL,
    price           DECIMAL(10, 2)      NOT NULL CHECK (price >= 0),
    stock_quantity  INT                 NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description     TEXT,
    created_at      TIMESTAMP           NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_price    ON products (price);

-- -------------------------
-- Table: orders
-- -------------------------
CREATE TABLE IF NOT EXISTS orders (
    id               SERIAL PRIMARY KEY,
    customer_id      INT             NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    order_date       DATE            NOT NULL DEFAULT CURRENT_DATE,
    total_amount     DECIMAL(10, 2)  NOT NULL CHECK (total_amount >= 0),
    status           VARCHAR(50)     NOT NULL DEFAULT 'Pending'
                         CHECK (status IN ('Pending', 'Processing', 'Delivered', 'Cancelled')),
    shipping_address TEXT,
    created_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date  ON orders (order_date);

-- -------------------------
-- Auto-update updated_at
-- -------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

