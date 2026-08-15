-- ============================================================
-- AuthenChain: AI & Blockchain-Based Counterfeit Skincare
-- Product Verification System — MySQL Schema
-- ============================================================
CREATE DATABASE IF NOT EXISTS authenchain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE authenchain_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    username VARCHAR(80) UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('manufacturer', 'consumer', 'admin') NOT NULL DEFAULT 'consumer',
    phone VARCHAR(30),
    company_name VARCHAR(150),
    profile_image VARCHAR(255) DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    manufacturer_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    brand VARCHAR(150) NOT NULL,
    batch_number VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) DEFAULT 'Skincare',
    ingredients TEXT,
    description TEXT,
    skin_type VARCHAR(150),
    benefits TEXT,
    usage_instructions TEXT,
    warnings TEXT,
    country_of_origin VARCHAR(100),
    price FLOAT DEFAULT 0,
    manufacturing_date DATE,
    expiry_date DATE,
    image_path VARCHAR(255),
    gallery_images TEXT,
    status ENUM('active', 'recalled', 'expired') DEFAULT 'active',
    scan_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manufacturer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_products_batch (batch_number),
    INDEX idx_products_manufacturer (manufacturer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS qrcodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL UNIQUE,
    qr_data VARCHAR(255) NOT NULL UNIQUE,
    qr_image_path VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS blockchain_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    block_index INT NOT NULL,
    product_id INT NOT NULL,
    manufacturer_id INT NOT NULL,
    verification_status VARCHAR(30) DEFAULT 'registered',
    data_hash VARCHAR(255) NOT NULL,
    previous_hash VARCHAR(255) NOT NULL,
    block_hash VARCHAR(255) NOT NULL,
    nonce INT DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (manufacturer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_block_index (block_index),
    INDEX idx_block_product (product_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS verification_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    consumer_id INT,
    scan_method ENUM('qr', 'image', 'camera') DEFAULT 'qr',
    result ENUM('genuine', 'suspicious', 'counterfeit') NOT NULL,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    confidence_score FLOAT DEFAULT 0,
    ip_address VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (consumer_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_verification_product (product_id),
    INDEX idx_verification_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    verification_id INT NOT NULL,
    match_score FLOAT DEFAULT 0,
    similarity_score FLOAT DEFAULT 0,
    authenticity_confidence FLOAT DEFAULT 0,
    anomalies_detected TEXT,
    final_decision VARCHAR(30),
    explanation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (verification_id) REFERENCES verification_history(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    generated_by INT,
    report_type VARCHAR(50) NOT NULL,
    report_format VARCHAR(10) DEFAULT 'csv',
    parameters TEXT,
    file_path VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_product_favorite (user_id, product_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    notif_type ENUM('info', 'success', 'warning', 'danger') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user (user_id)
) ENGINE=InnoDB;
