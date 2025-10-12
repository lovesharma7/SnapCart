-- Insert Categories
INSERT INTO categories (category_name, description) VALUES
('Clothing', 'Shirts, pants, and apparel'),
('Footwear', 'Shoes, sneakers, and sandals'),
('Electronics', 'Gadgets and electronic devices'),
('Accessories', 'Watches, belts, and other accessories'),
('Sports', 'Sports equipment and gear');

-- Insert Sample Products (Clothing)
INSERT INTO products (product_name, description, price, category_id, color, size, stock_quantity, image_url) VALUES
('Classic Black Shirt', 'Premium cotton black shirt', 29.99, 1, 'Black', 'M', 50, '/static/images/black_shirt.jpg'),
('Classic Black Shirt', 'Premium cotton black shirt', 29.99, 1, 'Black', 'L', 50, '/static/images/black_shirt.jpg'),
('White Formal Shirt', 'Elegant white formal shirt', 34.99, 1, 'White', 'M', 40, '/static/images/white_shirt.jpg'),
('Blue Denim Shirt', 'Casual blue denim shirt', 39.99, 1, 'Blue', 'L', 35, '/static/images/blue_denim.jpg'),
('Red Polo Shirt', 'Sporty red polo shirt', 27.99, 1, 'Red', 'M', 45, '/static/images/red_polo.jpg'),

-- Pants
('Blue Denim Jeans', 'Classic fit blue jeans', 49.99, 1, 'Blue', '32', 60, '/static/images/blue_jeans.jpg'),
('Black Formal Pants', 'Slim fit black formal pants', 54.99, 1, 'Black', '32', 45, '/static/images/black_pants.jpg'),
('Khaki Chinos', 'Comfortable khaki chinos', 44.99, 1, 'Khaki', '34', 50, '/static/images/khaki_chinos.jpg'),
('Grey Joggers', 'Comfortable grey joggers', 39.99, 1, 'Grey', 'L', 55, '/static/images/grey_joggers.jpg'),
('Navy Blue Cargo Pants', 'Utility navy cargo pants', 52.99, 1, 'Navy', '34', 40, '/static/images/navy_cargo.jpg'),

-- Footwear
('White Sneakers', 'Classic white sneakers', 79.99, 2, 'White', '9', 70, '/static/images/white_sneakers.jpg'),
('Black Leather Shoes', 'Formal black leather shoes', 99.99, 2, 'Black', '10', 35, '/static/images/black_shoes.jpg'),
('Blue Running Shoes', 'Lightweight blue running shoes', 89.99, 2, 'Blue', '9', 45, '/static/images/blue_running.jpg'),
('Brown Boots', 'Rugged brown leather boots', 119.99, 2, 'Brown', '10', 30, '/static/images/brown_boots.jpg'),
('Grey Canvas Shoes', 'Casual grey canvas shoes', 59.99, 2, 'Grey', '9', 50, '/static/images/grey_canvas.jpg'),

-- Electronics
('Wireless Headphones', 'Bluetooth wireless headphones', 149.99, 3, 'Black', NULL, 100, '/static/images/headphones.jpg'),
('Smartwatch', 'Fitness tracking smartwatch', 199.99, 3, 'Black', NULL, 80, '/static/images/smartwatch.jpg'),
('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 3, 'Black', NULL, 120, '/static/images/mouse.jpg'),
('Portable Speaker', 'Bluetooth portable speaker', 79.99, 3, 'Blue', NULL, 90, '/static/images/speaker.jpg'),
('Tablet', '10-inch Android tablet', 299.99, 3, 'Silver', NULL, 60, '/static/images/tablet.jpg'),

-- Accessories
('Leather Belt', 'Classic brown leather belt', 24.99, 4, 'Brown', '34', 70, '/static/images/belt.jpg'),
('Black Watch', 'Elegant black wristwatch', 89.99, 4, 'Black', NULL, 50, '/static/images/watch.jpg'),
('Sunglasses', 'UV protection sunglasses', 39.99, 4, 'Black', NULL, 80, '/static/images/sunglasses.jpg'),
('Wallet', 'Leather bifold wallet', 34.99, 4, 'Brown', NULL, 90, '/static/images/wallet.jpg'),
('Backpack', 'Laptop backpack 15-inch', 59.99, 4, 'Black', NULL, 65, '/static/images/backpack.jpg'),

-- Sports
('Yoga Mat', 'Non-slip yoga mat', 29.99, 5, 'Purple', NULL, 100, '/static/images/yoga_mat.jpg'),
('Dumbbells Set', '5kg dumbbells pair', 49.99, 5, 'Black', NULL, 75, '/static/images/dumbbells.jpg'),
('Tennis Racket', 'Professional tennis racket', 119.99, 5, 'Blue', NULL, 40, '/static/images/racket.jpg'),
('Basketball', 'Official size basketball', 34.99, 5, 'Orange', NULL, 85, '/static/images/basketball.jpg'),
('Gym Bag', 'Large sports gym bag', 44.99, 5, 'Black', NULL, 70, '/static/images/gym_bag.jpg');

-- Insert Product Combinations for Virtual Basket (good outfit combos)
INSERT INTO product_combinations (product_id_1, product_id_2, product_id_3, compatibility_score) VALUES
-- Black shirt + Blue jeans + White sneakers
(1, 6, 11, 95),
-- White shirt + Black pants + Black shoes
(3, 7, 12, 98),
-- Blue denim shirt + Khaki chinos + Brown boots
(4, 8, 14, 90),
-- Black shirt + Black pants + Black shoes (formal)
(1, 7, 12, 97),
-- Red polo + Blue jeans + White sneakers (casual)
(5, 6, 11, 88),
-- White shirt + Navy cargo + Grey canvas
(3, 10, 15, 85),
-- Blue denim + Khaki chinos + Blue running shoes
(4, 8, 13, 87),
-- Black shirt + Grey joggers + Grey canvas
(1, 9, 15, 82);
