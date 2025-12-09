-- posts 테이블에 password 컬럼 추가
ALTER TABLE posts
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 게시글 비밀번호 (해시)';

-- comments 테이블에 password 컬럼 추가
ALTER TABLE comments
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 댓글 비밀번호 (해시)';

-- files 테이블에 password 컬럼 추가
ALTER TABLE files
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 파일 비밀번호 (해시)';

-- 확인
SHOW COLUMNS FROM posts WHERE Field = 'password';
SHOW COLUMNS FROM comments WHERE Field = 'password';
SHOW COLUMNS FROM files WHERE Field = 'password';
