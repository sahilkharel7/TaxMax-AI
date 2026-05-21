# TaxMax AI User Manual

## 1. Overview

TaxMax AI is an AI-assisted tax preparation prototype for simple United States tax scenarios. It helps a user organize tax information, review extracted document fields, answer profile questions, view an estimated tax summary, and prepare a review package for a tax professional.

The app is intended for product demonstration and guided review. It is not a real tax filing product, does not e-file returns, and does not replace a qualified tax professional.

Production app URL:

https://taxmax-ai.vercel.app

## 2. What Users Can Do

Users can:

- Start a tax preparation session from uploaded documents or manual entry.
- Upload PDF, JPG, JPEG, or PNG tax forms.
- Review mocked extracted W-2 and 1098-T fields.
- Edit extracted values before confirming them.
- Enter personal, income, education, and credit information manually.
- Answer filing profile questions.
- View an estimated refund or amount owed.
- Review possible legal tax-saving opportunities and required follow-up facts.
- Review warnings, missing information, and next-step guidance.
- Ask the TaxMax Guide chatbot for help while using the app.
- Prepare a prototype review package for a tax professional.

Users cannot:

- File a real tax return.
- Submit information to the IRS or state tax agencies.
- Receive legal, tax, or financial advice.
- Depend on the estimate as a final refund or balance due.
- Use the app as a substitute for reviewing source documents.

## 3. Recommended Before Starting

Before using the app, users should gather the documents and information that apply to them:

- W-2 forms from employers.
- 1098-T forms for tuition or qualified education expenses.
- 1099 forms, such as 1099-INT, if applicable.
- Filing status information.
- Basic personal information.
- Education expense details.
- Information about possible credits, such as EITC, Child Tax Credit, Education Credit, or Saver's Credit.

The prototype works even if the user does not have every document, but the final review will flag missing or incomplete information.

## 4. Opening the App

1. Open the production URL:

   https://taxmax-ai.vercel.app

2. Confirm that the TaxMax AI home screen loads.

3. Review the header:

   - The TaxMax AI logo returns users to the first screen.
   - Trust indicators describe encrypted upload, user document control, and review before submission.
   - The API status pill shows whether the app is using connected backend services or mock mode.
   - On smaller screens, the Open guide button opens the TaxMax Guide chatbot.

## 5. Choosing a Start Method

The welcome screen offers two ways to begin.

### Option A: Start With Document Upload

Choose this if the user has tax forms available as PDF or image files.

Use this path when:

- The user has a W-2, 1098-T, or 1099 form.
- The user wants TaxMax AI to simulate document parsing.
- The user wants to review extracted fields instead of typing everything manually.

### Option B: Enter Manually

Choose this if the user does not have files ready or wants to type information directly.

Use this path when:

- The user only has numbers available.
- The user wants to test the flow without documents.
- The uploaded document flow is not relevant to the user's situation.

## 6. Document Upload Path

### 6.1 Uploading Files

On the upload screen, the user can drag files into the upload area or select browse.

Accepted file types:

- PDF
- JPG
- JPEG
- PNG

Displayed file size guidance:

- Up to 25 MB per file.

Supported document labels:

- W-2
- 1098-T
- 1099-INT
- Other

The app determines the document type from the file name. For example:

- A file name containing `w2` or `w-2` is treated as W-2.
- A file name containing `1098` is treated as 1098-T.
- A file name containing `1099` is treated as 1099-INT.
- Other names are labeled as Other.

### 6.2 Parsing Status

After upload, each document appears in the Uploaded documents list.

Possible statuses:

- Parsing: the file is being processed.
- Parsed: the file has been processed.
- Error: the file could not be processed.

In this prototype, parsing is simulated. W-2 and 1098-T review data is mocked.

### 6.3 Deleting Uploaded Files

To remove a document, select the delete icon next to the uploaded file.

Deleting a file also removes associated review data for that document.

### 6.4 Continuing to Review

The Continue to review button is disabled until at least one document reaches Parsed status.

Once a document is parsed:

1. Select Continue to review.
2. Review the extracted document fields.

## 7. Parsed Document Review

The parsed review screen shows extracted fields from supported uploaded documents.

For a W-2, the prototype may show fields such as:

- Employer name
- Employer EIN
- Wages, tips, and compensation
- Federal income tax withheld
- Social Security wages
- Medicare wages

For a 1098-T, the prototype may show fields such as:

- School
- Tuition payments
- Scholarships or grants

### 7.1 Reviewing Each Field

Users should compare every displayed value against the original document.

For each field, the user can:

- Select Edit to correct the value.
- Select Save to apply the correction.
- Select Cancel to discard an edit.
- Select Mark as correct to confirm the field.

### 7.2 Required Confirmation

The app tracks how many extracted fields have been confirmed.

The Confirm and continue button is disabled until every extracted field is confirmed.

This is intentional. The user should not move forward with document data until every field has been reviewed.

## 8. Manual Entry Path

The manual entry screen lets users type information directly instead of uploading tax documents.

### 8.1 Personal Information

Users can enter:

- First name
- Last name
- Social Security Number
- Date of birth
- Email
- Address
- City
- State
- ZIP code

The app labels first name and last name as required. Other fields help the final review determine whether the personal information section is complete.

### 8.2 Filing Status

Users select one filing status:

- Single
- Married filing jointly
- Married filing separately
- Head of household
- Qualifying surviving spouse

If a filing status is selected during manual entry, it carries into the profile step unless the profile already has a filing status.

### 8.3 Income

Users can enter:

- W-2 wages from Box 1.
- Federal income tax withheld from Box 2.

The summary estimate uses these values when no reviewed W-2 upload is available.

### 8.4 Education

Users can enter:

- Qualified education expenses.
- Whether they were a student during the year.

Education information affects the education credit review shown later.

### 8.5 Credits Checklist

Users can check possible credits:

- Earned Income Tax Credit (EITC)
- Child Tax Credit
- Education credit (AOTC / LLC)
- Saver's Credit

Checking a credit does not prove eligibility. It only tells the final review that the item needs review.

### 8.6 Continuing

Select Continue to move to the tax profile questions.

## 9. Tax Profile Questions

The profile screen collects filing context that affects the summary and final review.

### 9.1 Filing Status

Users select or confirm one filing status:

- Single
- Married filing jointly
- Married filing separately
- Head of household
- Qualifying surviving spouse

### 9.2 Yes or No Questions

Users answer:

- Can someone else claim you as a dependent?
- Were you a student this year?
- Did you receive a 1098-T?
- Did you have more than one job?
- Did you receive any 1099 forms?

### 9.3 Required Answers

The See summary button is disabled until:

- A filing status is selected.
- Every yes/no question is answered.

## 10. Estimated Summary

The summary screen gives a quick estimate based on the information entered or reviewed.

### 10.1 Main Estimate

The main card shows either:

- Estimated refund
- Estimated amount owed

The estimate uses:

- Total income
- Federal tax withheld
- Standard deduction
- Estimated taxable income

The calculation is simplified for prototype purposes. It should not be treated as a final tax result.

### 10.2 Education Credit Review

The app checks whether education credits may apply.

Education credit may appear as May apply when:

- Tuition or education expenses are present.
- The user answered that they were a student.
- The user did not say someone else can claim them as a dependent.

If those conditions are not met, the app may show Not applicable.

### 10.3 Agent Insights

The Agent insights section may show:

- Findings
- Warnings
- Missing information
- Next questions

If backend services are unavailable or mock mode is enabled, the app can still show the rest of the summary.

Possible insight statuses include:

- Reviewing
- Offline
- More info needed
- Review required
- Looks reasonable

### 10.4 Savings Opportunities

The Savings opportunities section is designed around the app's main goal: helping a user identify legal ways to reduce tax, increase a possible refund, or avoid missing deductions and credits.

The section may show opportunities such as:

- Itemized deduction review.
- Student loan interest deduction review.
- Self-employment expense review.
- Retirement contribution review.
- HSA contribution review.
- Education credit review.
- Dependent and child-related credit review.
- Earned Income Tax Credit review.
- Filing status review.
- State tax review.
- Missing document confirmation.

Each opportunity can include:

- Impact level.
- Risk level.
- Why it may matter.
- Facts the user still needs to confirm.
- Documents the user should gather.
- Suggested next step.
- Source references when available.

Important: an opportunity is not a final eligibility decision. The user should treat it as a review checklist item and confirm the facts with source documents or a qualified tax professional.

### 10.5 Moving to Final Review

Select Go to final review after reading the estimate and insights.

## 11. Final Review

The final review screen gives a section-by-section readiness check.

Sections include:

- Personal info
- Income
- Education
- Credits
- Documents

Each section can show a status such as:

- Complete
- Needs review
- Missing information
- Not applicable
- None selected
- No documents

### 11.1 Review Warnings

The Review warnings card can show local and backend-generated issues.

Examples:

- No income information found.
- The user indicated a 1098-T, but it is not fully reviewed.
- The user indicated a 1099 form, but none was uploaded.
- Backend agent service is offline.
- Additional missing information from the analysis service.

Users should address warnings by going back to the relevant step and correcting or adding information.

### 11.2 Preparing the Review Package

When ready, select Prepare review package.

After selection:

- The button changes to Review package ready.
- A confirmation message appears.

The review package is a prototype state only. It does not download a file, submit a return, or send data to a tax professional.

## 12. Using the TaxMax Guide Chatbot

The TaxMax Guide chatbot is available throughout the app.

On desktop:

- The chatbot appears as a sidebar.

On smaller screens:

- Select Open guide in the header.
- Select Hide guide or close the panel to dismiss it.

### 12.1 What to Ask

Users can ask questions such as:

- What is a W-2?
- Where do I find Box 1?
- Do I need a 1098-T?
- Can someone claim me as a dependent?
- Why do I need to review extracted data?
- What documents should I upload?
- How can I reduce my taxable income?
- What deductions or credits should I review?
- Are there legal ways to increase my refund?

### 12.2 Context-Aware Help

The chatbot receives the current step and scenario context when backend mode is active. This lets it respond based on what the user has already entered.

If backend services are unavailable, the chatbot uses offline replies and shows an offline notice.

### 12.3 Chatbot Limits

The chatbot can explain terms, guide the user through the app, and route savings-related questions to the tax optimization review when backend mode is active.

It should not be used as:

- Legal advice.
- Tax advice.
- A final eligibility decision.
- A guaranteed refund or savings estimate.
- A substitute for a qualified tax professional.

## 13. Navigation

The app uses a stepper after the welcome screen.

Users can:

- Move forward using the primary button on each screen.
- Go backward using Back.
- Select stepper items to revisit earlier parts of the flow.

When going back, users can edit prior answers. The summary and final review update based on the current session data.

## 14. Best Practices for Users

Users should:

- Use real source documents when reviewing uploaded data.
- Confirm every extracted value only after checking the original form.
- Enter dollar amounts carefully.
- Answer profile questions honestly.
- Treat warnings as items to investigate.
- Review anything marked Needs review or Missing information.
- Ask the chatbot for help understanding app steps or tax terms.
- Review every savings opportunity before the final review step.
- Gather the documents listed under each savings opportunity.
- Consult a qualified tax professional before making filing decisions.

Users should not:

- Treat the estimate as a final refund or balance due.
- Assume a checked credit means they qualify.
- Assume a savings opportunity means the user definitely qualifies.
- Ignore missing 1099, W-2, or 1098-T warnings.
- Use the app for actual tax filing.
- Enter sensitive information into a prototype unless they understand the privacy and prototype limitations.

## 15. Common Scenarios

### Scenario: User Has a W-2

1. Select Start with document upload.
2. Upload a W-2 file.
3. Wait for Parsed status.
4. Select Continue to review.
5. Confirm every W-2 field.
6. Answer profile questions.
7. Review the estimate.
8. Complete final review.
9. Prepare the review package.

### Scenario: User Has Tuition Information

1. Upload a 1098-T or enter education expenses manually.
2. Answer Yes to student status if applicable.
3. Answer whether a 1098-T was received.
4. Review the education credit section in the summary.
5. Check final review warnings for missing education details.

### Scenario: User Has No Documents Ready

1. Select Enter manually.
2. Fill in personal information.
3. Select filing status.
4. Enter wages, withholding, and education details if available.
5. Check credits that may apply.
6. Continue to profile questions.
7. Review the summary and final warnings.

### Scenario: User Indicates a 1099 Was Received

1. Answer Yes to Did you receive any 1099 forms?
2. Upload the relevant 1099 form if available.
3. If no 1099 is uploaded, the final review may warn that a 1099 form was indicated but not uploaded.

## 16. Troubleshooting

### The Continue Button Is Disabled on Upload

At least one uploaded document must show Parsed before continuing.

Wait for parsing to finish, or upload another supported file.

### The Confirm and Continue Button Is Disabled

Every extracted field must be confirmed.

Review each field and select Mark as correct, or edit and save the value.

### The See Summary Button Is Disabled

The profile step requires:

- One filing status.
- Answers to all yes/no questions.

Complete all questions to continue.

### The Chatbot Says It Is Using Offline Replies

The backend service is unavailable or mock mode is active.

The app can still be used, but chatbot answers may be generic.

### The Final Review Shows Missing Information

Go back to the relevant screen and add or correct the missing data.

Examples:

- Missing income: add W-2 wages manually or upload and confirm a W-2.
- Missing education information: upload and confirm a 1098-T or enter education expenses.
- Missing personal info: complete name, date of birth, and state fields.

### The Estimate Looks Wrong

Check:

- W-2 wages.
- Federal withholding.
- Filing status.
- Education expenses.
- Confirmed uploaded values.

Remember that the prototype uses simplified estimate logic and is not a final tax calculation.

## 17. Privacy and Data Handling Notes

The app describes encrypted upload and user document control in the interface. In the current prototype:

- Uploaded file handling and document parsing are simulated in the frontend.
- Extracted document values are mocked for demo purposes.
- Manual entry data is kept in the current browser session state.
- Refreshing the page may clear session progress.

Users should avoid entering real sensitive information into the prototype unless they understand how the deployed environment is configured and what data is being processed.

## 18. Prototype Limitations

TaxMax AI currently has these limitations:

- No e-filing.
- No IRS submission.
- No state filing workflow.
- Mocked document parsing.
- Simplified tax estimate.
- Limited document recognition.
- Savings opportunities are review prompts, not final eligibility decisions.
- Chatbot responses may be deterministic or offline depending on backend availability.
- Review package is only an in-app prototype state.

## 19. Glossary

W-2:

A wage and tax statement issued by an employer. It reports wages and taxes withheld.

1098-T:

A tuition statement issued by eligible education institutions. It may help review education credits.

1099:

A family of forms used to report non-wage income, such as interest, dividends, or contractor income.

Filing status:

The tax category used to determine standard deduction and tax treatment, such as Single or Married filing jointly.

Federal withholding:

Income tax withheld from paychecks and sent to the federal government.

Standard deduction:

A fixed deduction amount that reduces taxable income.

Taxable income:

Income after deductions. The prototype estimates this using a simplified formula.

Review package:

The prototype's final prepared state for sharing information with a qualified tax professional. It is not an e-filed return.

## 20. Final User Guidance

Use TaxMax AI as an organizing and review assistant. The safest workflow is:

1. Gather documents.
2. Upload or enter information.
3. Confirm every extracted or typed value.
4. Answer profile questions carefully.
5. Review warnings and missing information.
6. Prepare the review package only after the checklist looks complete.
7. Consult a qualified tax professional before filing anything.

TaxMax AI helps users move through the preparation process, but the user and their tax professional remain responsible for the final return.
