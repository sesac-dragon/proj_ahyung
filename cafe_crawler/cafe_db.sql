CREATE TABLE tb_cafe (
  id INT NOT NULL AUTO_INCREMENT,
  logNo VARCHAR(255) NOT NULL UNIQUE,
  cafename VARCHAR(255),
  cafeaddress TEXT,
  latitude FLOAT,
  longitude FLOAT,
  blogtext LONGTEXT,
  blogdate DATETIME,
  PRIMARY KEY (id)
);

SELECT id, logNo, cafename
FROM tb_cafe
ORDER BY logNo ASC;

SELECT id, cafename, cafeaddress, latitude, longitude
FROM tb_cafe
WHERE cafename = '바늘이야기 연희점';