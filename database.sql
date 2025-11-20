-- Create database
CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT,
    image_url VARCHAR(255),
    stock INT DEFAULT 0,
    color VARCHAR(50),
    size VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_category (category_id),
    INDEX idx_color (color),
    INDEX idx_name (name)
);

-- Cart table
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id)
);

-- Orders table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Order items table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
-- Modify Orders table to add payment fields
ALTER TABLE orders
  ADD COLUMN payment_id INT NULL,
  ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid';
-- Payments table
CREATE TABLE IF NOT EXISTS payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'INR',
  status VARCHAR(20) NOT NULL DEFAULT 'created',   -- created|processing|success|failed|pending|refunded
  method VARCHAR(30) DEFAULT NULL,                 -- card|upi|netbanking
  provider_txn_id VARCHAR(64) DEFAULT NULL,        -- mock txn reference
  meta_json JSON DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  INDEX idx_payments_order (order_id),
  INDEX idx_payments_status (status)
);
-- Payment events table
CREATE TABLE IF NOT EXISTS payment_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  payment_id INT NOT NULL,
  event_type VARCHAR(40) NOT NULL,
  payload_json JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
);



-- Insert Categories
INSERT INTO categories (name, description) VALUES
('Clothing', 'Men and Women fashion clothing'),
('Footwear', 'Shoes, sneakers, and sandals'),
('Electronics', 'Gadgets and electronic devices'),
('Accessories', 'Fashion accessories and more');

-- Insert Sample Products - Clothing
INSERT INTO products (name, description, price, category_id, image_url, stock, color, size) VALUES
-- White Shirts
('Classic White Shirt', 'Premium cotton white formal shirt', 1299.00, 1, 'https://m.media-amazon.com/images/I/61GtS6IrR7L._SX569_.jpg', 50, 'white', 'M'),
('Casual White Shirt', 'Comfortable white cotton casual shirt', 999.00, 1, 'https://m.media-amazon.com/images/I/71xA2DZQKEL._SY741_.jpg', 45, 'white', 'L'),
('Premium White Linen Shirt', 'Elegant white linen shirt for summer', 1599.00, 1, 'https://m.media-amazon.com/images/I/61idJrfaIRL._SX569_.jpg', 30, 'white', 'M'),

-- Black Shirts
('Black Formal Shirt', 'Sleek black formal shirt', 1399.00, 1, 'https://m.media-amazon.com/images/I/71jbGpe67QL._SX569_.jpg', 40, 'black', 'L'),
('Black Casual Shirt', 'Stylish black casual shirt', 1099.00, 1, 'https://m.media-amazon.com/images/I/51UWpA9iEuL._SY679_.jpg', 55, 'black', 'M'),

-- Blue Shirts
('Navy Blue Shirt', 'Classic navy blue formal shirt', 1249.00, 1, 'https://images-static.nykaa.com/media/catalog/product/b/5/b5e3bcbA24BFS525N8-R_1.jpg', 48, 'blue', 'L'),
('Light Blue Casual Shirt', 'Fresh light blue casual shirt', 1149.00, 1, 'https://m.media-amazon.com/images/I/61ci87YcjxL._SX679_.jpg', 42, 'blue', 'M'),

-- Black Pants
('Black Formal Trousers', 'Premium black formal trousers', 1799.00, 1, 'https://images-static.nykaa.com/media/catalog/product/7/a/7abe001AAPETAA00124080_1.jpg', 35, 'black', '32'),
('Black Chinos', 'Comfortable black chino pants', 1499.00, 1, 'https://images-static.nykaa.com/media/catalog/product/3/5/35ea131SS24SQINFLATEDBLK_1.jpg', 40, 'black', '34'),
('Black Jeans', 'Stylish black denim jeans', 1999.00, 1, 'https://m.media-amazon.com/images/I/71dyVevOHjL._SY741_.jpg', 50, 'black', '32'),

-- Blue Pants/Jeans
('Blue Jeans', 'Classic blue denim jeans', 1899.00, 1, 'https://m.media-amazon.com/images/I/81WzIbilc9L._SY741_.jpg', 60, 'blue', '32'),
('Navy Blue Chinos', 'Elegant navy blue chinos', 1599.00, 1, 'https://m.media-amazon.com/images/I/51glHYpZwiL._SY741_.jpg', 45, 'blue', '34'),
('Light Blue Jeans', 'Trendy light blue jeans', 1799.00, 1, 'https://m.media-amazon.com/images/I/61CorLcBn4L._SY741_.jpg', 38, 'blue', '32'),

-- Jackets
('Black Leather Jacket', 'Premium black leather jacket', 4999.00, 1, 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400', 20, 'black', 'L'),
('Denim Jacket', 'Classic blue denim jacket', 2499.00, 1, 'https://images-static.nykaa.com/media/catalog/product/3/5/355f557WIN23_JKDENIMP02_M_PLN_NBU_1.jpg', 25, 'blue', 'M'),
('Grey Blazer', 'Formal grey blazer', 3999.00, 1, 'https://m.media-amazon.com/images/I/61HUlsaAVIL._SY741_.jpg', 18, 'grey', 'L');

-- Insert Sample Products - Footwear
INSERT INTO products (name, description, price, category_id, image_url, stock, color, size) VALUES
-- Sneakers
('White Sneakers', 'Classic white sports sneakers', 2499.00, 2, 'https://m.media-amazon.com/images/I/61HDoHAa+WL._SY575_.jpg', 50, 'white', '9'),
('Black Sneakers', 'Stylish black casual sneakers', 2699.00, 2, 'https://images-static.nykaa.com/media/catalog/product/6/1/614b50eJADIAA00029251_1.jpg', 45, 'black', '9'),
('Blue Running Shoes', 'Professional blue running shoes', 3299.00, 2, 'https://images-static.nykaa.com/media/catalog/product/9/3/93627a1ASICS00028394_1.jpg', 40, 'blue', '10'),
('Grey Sports Sneakers', 'Comfortable grey sports shoes', 2899.00, 2, 'https://images-static.nykaa.com/media/catalog/product/2/7/273d914ASICS00046569_1.jpg', 35, 'grey', '9'),

-- Formal Shoes
('Black Formal Shoes', 'Premium black leather formal shoes', 3499.00, 2, 'https://m.media-amazon.com/images/I/61CLFQf6RkL._SY575_.jpg', 30, 'black', '9'),
('Brown Formal Shoes', 'Classic brown leather shoes', 3299.00, 2, 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=400', 28, 'brown', '10'),

-- Casual Shoes
('White Canvas Shoes', 'Comfortable white canvas shoes', 1799.00, 2, 'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=400', 55, 'white', '9'),
('Brown Loafers', 'Casual brown loafers', 2199.00, 2, 'https://m.media-amazon.com/images/I/51+u+TSFJXL._SX575_.jpg', 32, 'brown', '9');

-- Insert Sample Products - Electronics
INSERT INTO products (name, description, price, category_id, image_url, stock, color, size) VALUES
('Wireless Earbuds', 'Premium wireless earbuds with noise cancellation', 3999.00, 3, 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400', 100, 'black', NULL),
('Smart Watch', 'Fitness tracking smart watch', 8999.00, 3, 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=400', 75, 'black', NULL),
('Bluetooth Speaker', 'Portable bluetooth speaker', 2999.00, 3, 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400', 60, 'blue', NULL),
('Laptop Bag', 'Professional laptop backpack', 1999.00, 3, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400', 80, 'black', NULL),
('USB-C Hub', 'Multi-port USB-C hub', 1499.00, 3, 'https://m.media-amazon.com/images/I/61B4vVPIQiL._SX450_.jpg', 120, 'grey', NULL);

-- Insert Sample Products - Accessories
INSERT INTO products (name, description, price, category_id, image_url, stock, color, size) VALUES
('Black Leather Belt', 'Genuine leather formal belt', 899.00, 4, 'https://m.media-amazon.com/images/I/71aplh5AFZL._SX679_.jpg', 70, 'black', NULL),
('Brown Leather Belt', 'Casual brown leather belt', 799.00, 4, 'https://m.media-amazon.com/images/I/812n5ySqagL._SY741_.jpg', 65, 'brown', NULL),
('Silver Watch', 'Elegant silver wrist watch', 4999.00, 4, 'https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400', 40, 'silver', NULL),
('Sunglasses', 'Stylish UV protection sunglasses', 1299.00, 4, 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400', 90, 'black', NULL),
('Leather Wallet', 'Premium leather wallet', 1499.00, 4, 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=400', 100, 'brown', NULL),
('Backpack', 'Casual canvas backpack', 1999.00, 4, 'https://m.media-amazon.com/images/I/715vso7qFEL._SL1500_.jpg', 55, 'black', NULL);


-- Wishlist table
CREATE TABLE IF NOT EXISTS wishlists (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY user_product_unique (user_id, product_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
