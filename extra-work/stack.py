def make_stack():
    return []


def check_empty(stack):
    return len(stack) == 0


def push(stack, item):
    stack.append(item)


def peek(stack):
    if check_empty(stack):
        return None
    return stack[-1]


def pop(stack):
    if check_empty(stack):
        return None
    return stack.pop()


res = None
while res is None:
    temp = input("Input a list of numbers separated by commas: ")
    try:
        temp2 = []
        for item in temp.split(","):
            temp2.append(float(item))
        res = temp2
    except Exception as e:
        print("Bad input")
stack = make_stack()

for item in res:
    push(stack, item)

print(stack)
