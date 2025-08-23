import random

from faker import Faker

fake = Faker()

# faker -r=1000 -s=',' name email ean8 vat


with open('out_fake.csv', 'wt') as f:
    for i in range(200_000):
        name = fake.name()

        if random.random() < 0.30:
            email = fake.email()
        else:
            email = ''

        if random.random() < 0.40:
            ref = fake.ean8()
        else:
            ref = ''

        if random.random() < 0.45:
            vat = fake.iban()
        else:
            vat = ''

        line = ",".join([name, email, ref, vat])
        f.write(f"{line}\n")