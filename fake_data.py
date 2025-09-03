import random

from faker import Faker

fake = Faker()

# faker -r=1000 -s=',' name email ean8 vat


with open('out_fake.csv', 'wt') as f:
    for i in range(500_000):
        if random.random() < 0.85:
            name = fake.name()
        else:
            name = ''

        if random.random() < 0.85:
            email = fake.email()
        else:
            email = ''

        if random.random() < 0.05:
            ref = fake.ean8()
        else:
            ref = ''

        if random.random() < 0.10:
            vat = fake.iban()
        else:
            vat = ''

        if not any([name, email, ref, vat]):
            continue

        line = ",".join([name, email, ref, vat])
        f.write(f"{line}\n")