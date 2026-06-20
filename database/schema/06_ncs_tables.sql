-- =====================================================================
-- 06_ncs_tables.sql
-- 子系統：NCS 通知與溝通 Notification and Communication Subsystem
-- 相依：01_aas_tables.sql users、03_sas_tables.sql applications
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT NULL,
    category VARCHAR(50) NULL,
    related_type VARCHAR(50) NULL,
    related_id INT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME NULL,
    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS announcements (
    announcement_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    body TEXT NULL,
    created_by INT NULL,
    target_role VARCHAR(30) NULL,
    is_global TINYINT(1) NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'PUBLISHED',
    published_at DATETIME NULL,
    expires_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL,
    CONSTRAINT fk_announcements_created_by
        FOREIGN KEY (created_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS application_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    sender_id INT NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_application_messages_application
        FOREIGN KEY (application_id) REFERENCES applications(application_id),
    CONSTRAINT fk_application_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS issue_reports (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    attachment_name VARCHAR(255) NULL,
    attachment_url VARCHAR(500) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL,
    CONSTRAINT fk_issue_reports_reporter
        FOREIGN KEY (reporter_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS issue_replies (
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    replier_id INT NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_issue_replies_issue
        FOREIGN KEY (issue_id) REFERENCES issue_reports(issue_id),
    CONSTRAINT fk_issue_replies_replier
        FOREIGN KEY (replier_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    title VARCHAR(200) NOT NULL,
    body TEXT NULL,
    source VARCHAR(100) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_logs (
    email_log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    to_email VARCHAR(255) NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DISABLED',
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_email_logs_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;