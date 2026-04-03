import random
f = lambda: f"+7{random.randint(9000000000,9999999999)}"
with open("free_data/free_phones.txt",'w') as fp: [fp.write(f"{f()}\n") for _ in range(5000)]
print("✅ 5k номеров!")