CREATE TABLE IF NOT EXISTS video_summary (
  video_id VARCHAR(20) PRIMARY KEY,
  summary TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO video_summary (video_id, summary) VALUES ('abc123', 'This is a sample video summary.');
INSERT INTO video_summary (video_id, summary) VALUES ('def456', 'Another sample video summary for testing.');
