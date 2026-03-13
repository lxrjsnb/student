-- 为users表添加score字段
ALTER TABLE users ADD COLUMN score INT DEFAULT 0;

-- 更新现有用户的分数为0
UPDATE users SET score = 0 WHERE score IS NULL;
