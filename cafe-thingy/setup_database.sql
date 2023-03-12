CREATE TABLE "Categories" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "Products" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"size"	TEXT NOT NULL,
	"image_path"	TEXT NOT NULL,
	"price"	REAL NOT NULL,
	"category_id"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "Users" (
	"display_name"	TEXT NOT NULL,
	"username"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	"admin"	INTEGER NOT NULL DEFAULT 0 COLLATE BINARY,
	"id"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "Cart_Items" (
	"product_id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"product_quantity"	INTEGER NOT NULL,
	FOREIGN KEY("product_id") REFERENCES "Products"("id"),
	FOREIGN KEY("user_id") REFERENCES "Users"("id")
);