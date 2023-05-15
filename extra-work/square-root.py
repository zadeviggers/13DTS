res = None
while res is None:
    temp = input("Input a number: ")
    try:
        temp = float(temp)
        res = temp
    except Exception as e:
        print("Get gud")

print(f"Square root is {res ** 2}")
