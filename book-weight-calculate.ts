// Constant of how heavy a page is
const gramsPerSquareMM = 0.0000801667;

// Function to ask the user for  a number
function promptContinuouslyForValidInt(prompt: string): number {
  // Loop until we get a valid input
  let success = false;
  let value = 0;

  while (!success) {
    // Prompt the user to enter a number
    const input = window.prompt(prompt);
    // Validate that they entered something
    if (!input) {
      console.info("Enter a number");
      continue;
    }
    // Try/catch in case parsing the number fails
    try {
      const res = Number.parseInt(input);
      // Make sure it's a real number
      if (!Number.isNaN(res)) {
        // Make the number of pages available to other code outside the loop
        value = res;
        // Exit the loop
        success = true;
      } else console.warn("Number pls");
    } catch {
      console.log("Enter a valid number pls");
    }
  }
  return value;
}

// Get the page count
const pageCount = promptContinuouslyForValidInt("How many pages in your book?");

// Get page dimensions
const pageWidth = promptContinuouslyForValidInt("How wide is your book in mm?");
const pageHeight = promptContinuouslyForValidInt(
  "How tall is your book in mm?"
);

const pageArea = pageWidth * pageHeight;

const pageWeight = pageArea * gramsPerSquareMM;

// Calculate the book weight
const weight = pageCount * pageWeight;

// Output the weight to the user
console.log(`You book weighs ${weight / 1000}kg`);
