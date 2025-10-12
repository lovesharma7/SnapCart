-- Create Database
CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories Table
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Products Table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT,
    color VARCHAR(30),
    size VARCHAR(20),
    stock_quantity INT DEFAULT 0,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Cart Table
CREATE TABLE cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Cart Items Table
CREATE TABLE cart_items (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES cart(cart_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Virtual Basket Table (stores user's virtual basket requests)
CREATE TABLE virtual_basket (
    basket_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Virtual Basket Items Table
CREATE TABLE virtual_basket_items (
    basket_item_id INT AUTO_INCREMENT PRIMARY KEY,
    basket_id INT,
    item_description VARCHAR(255),
    category_id INT,
    color VARCHAR(30),
    FOREIGN KEY (basket_id) REFERENCES virtual_basket(basket_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Product Combinations Table (for recommendations)
CREATE TABLE product_combinations (
    combination_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id_1 INT,
    product_id_2 INT,
    product_id_3 INT,
    compatibility_score INT DEFAULT 0,
    FOREIGN KEY (product_id_1) REFERENCES products(product_id),
    FOREIGN KEY (product_id_2) REFERENCES products(product_id),
    FOREIGN KEY (product_id_3) REFERENCES products(product_id)
);
