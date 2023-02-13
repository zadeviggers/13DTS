# Run generate-emails.py first!!

import json

raw_emails = []

with open("emails.txt", "r") as f:
    raw_emails = f.read().split("\n")


validated_emails = []

for email in raw_emails:
    valid = True

    parts = email.split("@")

    if len(parts) != 2:
        valid = False
    else:
        domain = parts[1].split(".")

        if len(domain) < 2:
            valid = False

        # TODO: Add more checks in here

    if valid:
        validated_emails.append(email)

with open("validated-emails.txt", "w") as f:
    f.write("\n".join(validated_emails))
