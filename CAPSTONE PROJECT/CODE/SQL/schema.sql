-- ============================================================
-- Olist E-Commerce  –  3NF Schema
-- Authors: Monish L, Prasannakumar S, S Hari Surendran
-- ============================================================
-- Run: mysql -u olist_admin -p < sql/schema.sql
-- Idempotent: safe to re-run (drops in reverse-dependency order)
-- ============================================================

CREATE DATABASE IF NOT EXISTS olist
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE olist;

-- ── Drop tables in reverse-dependency order ────────────────────
DROP TABLE IF EXISTS order_reviews;
DROP TABLE IF EXISTS order_payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product_categories;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS geolocation;

-- ── 1. geolocation ─────────────────────────────────────────────
CREATE TABLE geolocation (
    zip_prefix      VARCHAR(5)      NOT NULL,
    city            VARCHAR(100)    NOT NULL,
    state           CHAR(2)         NOT NULL,
    avg_lat         DECIMAL(10,6)   NOT NULL DEFAULT 0,
    avg_lng         DECIMAL(10,6)   NOT NULL DEFAULT 0,
    PRIMARY KEY (zip_prefix)
) ENGINE=InnoDB;

-- ── 2. customers ───────────────────────────────────────────────
CREATE TABLE customers (
    customer_id         CHAR(32)    NOT NULL,
    customer_unique_id  CHAR(32)    NOT NULL,
    zip_prefix          VARCHAR(5)  NOT NULL,
    PRIMARY KEY (customer_id),
    INDEX idx_cust_zip (zip_prefix),
    INDEX idx_cust_unique (customer_unique_id),
    CONSTRAINT fk_cust_geo
        FOREIGN KEY (zip_prefix) REFERENCES geolocation(zip_prefix)
) ENGINE=InnoDB;

-- ── 3. sellers ─────────────────────────────────────────────────
CREATE TABLE sellers (
    seller_id   CHAR(32)    NOT NULL,
    zip_prefix  VARCHAR(5)  NOT NULL,
    PRIMARY KEY (seller_id),
    INDEX idx_seller_zip (zip_prefix),
    CONSTRAINT fk_seller_geo
        FOREIGN KEY (zip_prefix) REFERENCES geolocation(zip_prefix)
) ENGINE=InnoDB;

-- ── 4. product_categories ──────────────────────────────────────
CREATE TABLE product_categories (
    category_name       VARCHAR(100)    NOT NULL,
    category_name_en    VARCHAR(100)    NULL,
    PRIMARY KEY (category_name),
    UNIQUE INDEX idx_cat_en (category_name_en)
) ENGINE=InnoDB;

-- ── 5. products ────────────────────────────────────────────────
CREATE TABLE products (
    product_id      CHAR(32)        NOT NULL,
    category_name   VARCHAR(100)    NULL,
    weight_g        INT             NULL,
    length_cm       INT             NULL,
    height_cm       INT             NULL,
    width_cm        INT             NULL,
    photos_qty      INT             NULL,
    PRIMARY KEY (product_id),
    INDEX idx_prod_cat (category_name),
    CONSTRAINT fk_prod_cat
        FOREIGN KEY (category_name) REFERENCES product_categories(category_name)
) ENGINE=InnoDB;

-- ── 6. orders ──────────────────────────────────────────────────
CREATE TABLE orders (
    order_id                    CHAR(32)    NOT NULL,
    customer_id                 CHAR(32)    NOT NULL,
    order_status                VARCHAR(20) NOT NULL,
    order_purchase_timestamp    DATETIME    NOT NULL,
    order_approved_at           DATETIME    NULL,
    order_delivered_carrier_date DATETIME   NULL,
    order_delivered_customer_date DATETIME  NULL,
    order_estimated_delivery_date DATETIME  NULL,
    PRIMARY KEY (order_id),
    INDEX idx_ord_cust (customer_id),
    INDEX idx_ord_purchase_ts (order_purchase_timestamp),
    INDEX idx_ord_status (order_status),
    CONSTRAINT fk_ord_cust
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

-- ── 7. order_items ─────────────────────────────────────────────
CREATE TABLE order_items (
    order_id            CHAR(32)        NOT NULL,
    order_item_id       INT             NOT NULL,
    product_id          CHAR(32)        NOT NULL,
    seller_id           CHAR(32)        NOT NULL,
    shipping_limit_date DATETIME        NOT NULL,
    price               DECIMAL(10,2)   NOT NULL,
    freight_value       DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    INDEX idx_oi_prod (product_id),
    INDEX idx_oi_seller (seller_id),
    CONSTRAINT fk_oi_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_oi_prod
        FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_oi_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
) ENGINE=InnoDB;

-- ── 8. order_payments ──────────────────────────────────────────
CREATE TABLE order_payments (
    order_id            CHAR(32)        NOT NULL,
    payment_sequential  INT             NOT NULL,
    payment_type        VARCHAR(30)     NOT NULL,
    installments        INT             NOT NULL DEFAULT 1,
    payment_value       DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_op_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
) ENGINE=InnoDB;

-- ── 9. order_reviews ───────────────────────────────────────────
CREATE TABLE order_reviews (
    review_id               CHAR(32)    NOT NULL,
    order_id                CHAR(32)    NOT NULL,
    review_score            TINYINT     NOT NULL,
    review_comment_title    TEXT        NULL,
    review_comment_message  TEXT        NULL,
    review_creation_date    DATETIME    NULL,
    review_answer_timestamp DATETIME    NULL,
    PRIMARY KEY (review_id, order_id),
    INDEX idx_rev_order (order_id),
    CONSTRAINT fk_rev_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT chk_review_score
        CHECK (review_score BETWEEN 1 AND 5)
) ENGINE=InnoDB;

-- ── Read-only application user ─────────────────────────────────
-- Run as root / admin to create the RO user used by Streamlit.
-- Passwords should match .env values.
CREATE USER IF NOT EXISTS 'olist_ro'@'localhost'
    IDENTIFIED BY 'change_me_ro';
GRANT SELECT ON olist.* TO 'olist_ro'@'localhost';
FLUSH PRIVILEGES;
