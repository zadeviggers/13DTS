CREATE TABLE "Users" (
    "ID" INTEGER NOT NULL UNIQUE,
    "Name" TEXT NOT NULL,
    "Teacher" INTEGER,
    PRIMARY KEY("ID" AUTOINCREMENT)
) STRICT;

CREATE TABLE "Images" (
    "ID" INTEGER NOT NULL UNIQUE,
    "Description" TEXT NOT NULL,
    "AssertSlug" TEXT NOT NULL,
    PRIMARY KEY("ID" AUTOINCREMENT)
) STRICT;

CREATE TABLE "Words" (
    "ID" INTEGER NOT NULL UNIQUE,
    "MaoriSpelling" TEXT NOT NULL,
    "EnglishSpelling" TEXT NOT NULL,
    "EnglishDefinition" TEXT NOT NULL,
    "YearLevelFirstEncountered" INTEGER NOT NULL,
    "ImageID" INTEGER NOT NULL,
    "CreatedBy" INTEGER NOT NULL,
    "CreatedAt" INTEGER NOT NULL,
    "LastModifiedBy" INTEGER NOT NULL,
    "LastModifiedAt" INTEGER NOT NULL,
    FOREIGN KEY("ImageID") REFERENCES "Images"("ID"),
    FOREIGN KEY("CreatedBy") REFERENCES "Users"("ID"),
    FOREIGN KEY("LastModifiedAt") REFERENCES "Users"("ID"),
    PRIMARY KEY("ID" AUTOINCREMENT)
) STRICT;