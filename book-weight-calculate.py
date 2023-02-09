# Constant of how heavy a page is
gramsPerSquareMM = 0.0000801667

# Function to ask the user for  a number


def promptContinuouslyForValidInt(
    prompt: str,
    maxValue: int = 15000,
    minValue: int = 1
) -> int:
    # Loop until we get a valid input
    success = False
    value = 0

    while (not success):
        # Prompt the user to enter a number
        inputtedValue = input(prompt+" ")
        # Validate that they entered something
        if len(inputtedValue) == 0:
            print("Enter a number")
            continue

        # Try/catch in case parsing the number fails
        try:
            res = int(inputtedValue)
            # Make sure it's a real number
            if (res < minValue):
                print(f"Number greater than {minValue} please")
                continue

            if (res > maxValue):
                print(f"Number less than {maxValue} please")
                continue

            # Make the number of pages available to other code outside the loop
            value = res
            # Exit the loop
            success = True
        except Exception as err:
            print(f"Something went wrong parsing your number: {err}")

    return value


# Get page dimensions
pageWidth = promptContinuouslyForValidInt(
    "How wide is your book in mm?",
    maxValue=1000
)
pageHeight = promptContinuouslyForValidInt(
    "How tall is your book in mm?",
    maxValue=1000
)

# Get the page count
pageCount = promptContinuouslyForValidInt("How many pages in your book?")

# Calculate the area of the page in mm²
pageArea = pageWidth * pageHeight

# Calculate the weight of a single page
pageWeight = pageArea * gramsPerSquareMM

# Calculate the book weight
weight = pageCount * pageWeight

# Output the weight to the user
print(f"You book weighs {weight / 1000}kg")
