CREATE TABLE
	"Users" (
		"ID" INTEGER NOT NULL UNIQUE,
		"Username" TEXT NOT NULL,
		"PasswordHash" TEXT NOT NULL,
		"Teacher" INTEGER,
		PRIMARY KEY ("ID" AUTOINCREMENT)
	) STRICT;

CREATE TABLE
	"Categories" (
		"ID" INTEGER NOT NULL UNIQUE,
		"EnglishName" TEXT NOT NULL,
		PRIMARY KEY ("ID" AUTOINCREMENT)
	) STRICT;

CREATE TABLE
	"Words" (
		"ID" INTEGER NOT NULL UNIQUE,
		"MaoriSpelling" TEXT NOT NULL,
		"EnglishSpelling" TEXT NOT NULL,
		"EnglishDefinition" TEXT NOT NULL,
		"YearLevelFirstEncountered" INTEGER NOT NULL,
		"ImageFilename" TEXT,
		"CreatedBy" INTEGER NOT NULL,
		"CreatedAt" INTEGER NOT NULL,
		"LastModifiedBy" INTEGER,
		"LastModifiedAt" INTEGER,
		"CategoryID" INTEGER NOT NULL,
		PRIMARY KEY ("ID" AUTOINCREMENT),
		FOREIGN KEY ("CategoryID") REFERENCES "Categories" ("ID"),
		FOREIGN KEY ("CreatedBy") REFERENCES "Users" ("ID"),
		FOREIGN KEY ("ImageID") REFERENCES "Images" ("ID"),
		FOREIGN KEY ("LastModifiedAt") REFERENCES "Users" ("ID")
	) STRICT;