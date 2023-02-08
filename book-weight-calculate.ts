// Constant of how heavy a page is
const gramsPerSquareMM = 0.0000801667;

// Function to ask the user for  a number
function promptContinuouslyForValidPositiveInt(prompt: string): number {
  // Loop until we get a valid input
  let success = false;
  let value = 0;

  while (!success) {
    // Prompt the user to enter a number
    const input = window.prompt(prompt);
    // Validate that they entered something
    if (!input) {
      console.warn("Enter a number");
      continue;
    }
    // Try/catch in case parsing the number fails
    try {
      const res = Number.parseInt(input);
      // Make sure it's a real number
      if (!Number.isNaN(res)) {
        if (res < 0) {
          console.warn("Number greater than zero please");
          continue;
        }
        // Make the number of pages available to other code outside the loop
        value = res;
        // Exit the loop
        success = true;
      } else console.warn("Number please");
    } catch {
      console.warn("Enter a valid number please");
    }
  }
  return value;
}

// Get page dimensions
const pageWidth = promptContinuouslyForValidPositiveInt(
  "How wide is your book in mm?"
);
const pageHeight = promptContinuouslyForValidPositiveInt(
  "How tall is your book in mm?"
);

// Get the page count
const pageCount = promptContinuouslyForValidPositiveInt(
  "How many pages in your book?"
);

// Calculate the area of the page in mm²
const pageArea = pageWidth * pageHeight;

// Calculate the weight of a single page
const pageWeight = pageArea * gramsPerSquareMM;

// Calculate the book weight
const weight = pageCount * pageWeight;

// Output the weight to the user
console.log(`You book weighs ${weight / 1000}kg`);
