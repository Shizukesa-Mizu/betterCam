window.setTimeout(() => {
  var comment = "Good teacher";
  var level = 0;

  if (document.querySelectorAll('input[type="radio"]').length !== 0) {
    var radioButtons = document.querySelectorAll('input[type="radio"]');
    // Select the radio button at index 'level'
    radioButtons.item(level).click();
    location.reload();
  }

  if (
    document.querySelectorAll('button[type="submit"]')[1].value === "finish"
  ) {
    document.querySelector(".form-control").value = comment;
    document.querySelectorAll(".btn")[2].click();
    location.reload();
  }
}, 2000);

// Qalam Nust Feedback Forms AutoFiller Injection Script
// Developed by a Mechanic from ME11 SMME NUST

// Radio rating scale:
// 0 = Excellent
// 1 = Very Good
// 2 = Good
// 3 = Average
// 4 = Poor

var indexArray = [0, 1];
// indexArray to randomly select rating index to fill the form

var comment = "...";
// Default comment for autofilling and submission

function getRandom(list) {
  return list[Math.floor(Math.random() * list.length)];
}

var index = getRandom(indexArray);

function selectRadio() {
  var radios = document.querySelectorAll("input[type=radio]");
  radios[index].click();
  console.log(`Clicked Radio ${index}`);
}

function fillComment() {
  var textArea = document.querySelector("textarea");
  textArea.value = comment;
  var submitButton = document.querySelector("button[value=finish]");
  submitButton.click();
  history.back();
}

setInterval(function () {
  try {
    selectRadio();
  } catch {
    console.log(`Can't find Radio ${index}`);
    try {
      fillComment();
    } catch {
      console.log(`Can't find TextArea`);
      window.close();
    }
  }
}, 4000);

/**
 * Function to introduce a delay.
 * @param {number} ms - Milliseconds to wait.
 */
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function surveySelect() {
  const surveyLinks = document.querySelectorAll("a.md-list-addon-element");

  if (surveyLinks.length > 0) {
    // Click the first link in the list
    surveyLinks[0].click();
    await delay(3000);
    var confirmation = document.querySelector(
      'button[type="submit"][value="start"]',
    );
    confirmation.click();
  } else {
    console.log("No survey links found on the page.");
  }
}
async function autoFillSurvey() {
  const totalRows = 15;
  const targetColumnIndex = 3; // We want the 3rd radio button
  const comment = "lovely teacher";

  await delay(1000);
  const firstRadio = document.querySelector(
    'input[type="radio"].o_survey_form_choice_item',
  );

  if (!firstRadio) {
    console.error("no initial radio button to start calculation. Aborting.");
    return;
  }

  // --- 1. Calculate Base Values ---
  const baseNamePart = firstRadio.name.split("_")[0];
  const firstRowId = parseInt(firstRadio.getAttribute("data-row-id"));
  const firstColumnValue = parseInt(firstRadio.value);
  const targetColumnValue = firstColumnValue + (targetColumnIndex - 1); // For the 3rd column

  console.log(`Column ID: ${targetColumnValue}`);

  // --- 2. Iterate, Click, and Delay ---
  let selectedCount = 0;

  for (let i = 0; i < totalRows; i++) {
    const currentRowId = firstRowId + i;
    const targetRadioName = `${baseNamePart}_${currentRowId}`;
    const targetRadioSelector = `input[type="radio"][name="${targetRadioName}"][value="${targetColumnValue}"]`;

    const targetRadio = document.querySelector(targetRadioSelector);

    if (targetRadio) {
      // Simulate a mouse click event
      targetRadio.click();
      await delay(100);
      targetRadio.click();
      selectedCount++;
      console.log(`Row ID ${i + 1} (ID: ${currentRowId}).`);

      // Introduce a random delay between 500ms and 1500ms
      const randomDelay = Math.floor(Math.random() * 500) + 500;
      await delay(randomDelay);
    } else {
      console.warn(`Could not find radio button for Row ${i + 1}. Skipping.`);
    }
  }

  // --- 3. Final Confirmation ---
  if (selectedCount === totalRows) {
    var textArea = document.querySelector("textarea");
    textArea.value = comment;
    await delay(200);
    var submitButton = document.querySelector("button[value=finish]");
    submitButton.click();
    await delay(500);
    history.back();
  } else {
    console.log(`Failure`);
  }
}
surveySelect();
// Execute the main function
autoFillSurvey();
