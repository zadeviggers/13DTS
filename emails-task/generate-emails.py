import random

domain_first_parts = ["google", "wc", "gmail",
                      "outlook", "hotmail", "viggers", "whs", "govt", "dinopoloclub"]

top_level_domains = ["com", "net", "co.nz", "school.nz", "nz"]

email_joiners = ["-", "@"]

emails = []


for i in range(69420):
    domain = f"{random.choice(domain_first_parts)}.{random.choice(top_level_domains)}"

    name = "".join([chr(random.randint(97, 122))
                   for _ in range(random.randint(3, 20))])

    joiner = random.choice(email_joiners)

    email = f"{name}{joiner}{domain}"

    emails.append(email)

with open("emails.txt", "w") as f:
    f.write("\n".join(emails))
