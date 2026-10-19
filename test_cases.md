Finora Personal Finance Agent — Test Cases

1. Purpose

This document describes the manual test cases for the Finora Personal Finance Agent application. Each test must be performed, and the actual result must be recorded.

2. Test Cases

Test ID| Test Name| Test Procedure| Expected Result| Status
TC-01| Application Startup| Run "streamlit run app.py".| The application opens without errors.| Not Tested
TC-02| Google Login| Click Continue with Google and complete authentication.| The user logs in successfully.| Not Tested
TC-03| Login Protection| Open the app while signed out.| The login screen appears.| Not Tested
TC-04| Dashboard Display| Open the dashboard.| Dashboard metrics and sections display correctly.| Not Tested
TC-05| Add Income| Add a valid income transaction.| The transaction appears and totals update.| Not Tested
TC-06| Add Expense| Add a valid expense transaction.| The expense appears and the balance updates correctly.| Not Tested
TC-07| Invalid Amount| Enter an invalid transaction amount.| Invalid input is rejected or a validation message appears.| Not Tested
TC-08| Edit Transaction| Edit an existing transaction.| The updated transaction and totals display correctly.| Not Tested
TC-09| Monthly Budget| Set a monthly budget.| The budget is displayed correctly.| Not Tested
TC-10| Date/Month Filter| Select a different month.| Transactions and metrics reflect the selected period.| Not Tested
TC-11| Charts| Open the dashboard charts.| Charts render without errors and reflect available data.| Not Tested
TC-12| AI Insights| Generate AI insights.| Insight text appears and is readable.| Not Tested
TC-13| AI Error Handling| Test AI insights without a configured API key.| A clear error or setup message appears instead of an app crash.| Not Tested
TC-14| AI Chat| Ask a question in the AI chat.| A relevant response appears when the AI service is configured.| Not Tested
TC-15| CSV Export| Export transaction data.| A CSV file downloads with the expected data.| Not Tested
TC-16| Empty State| Open the app without transactions, if possible.| The app handles empty data without crashing.| Not Tested
TC-17| Logout| Click Log out.| The user returns to the login screen.| Not Tested
TC-18| Secrets Security| Check files before uploading to GitHub.| API keys and OAuth client secrets are not committed.| Not Tested
TC-19| Deployment| Open the deployed application URL.| The deployed app loads and its configured features work.| Not Tested

3. Test Status

- Pass: The actual result matches the expected result.
- Fail: The feature does not work as expected.
- Not Tested: The test has not been performed.

Update each status after running the test. Do not mark a test as Pass without checking it.

4. Test Summary

- Total tests performed: ______
- Passed: ______
- Failed: ______
- Not tested: ______
- Known issues: ______
- Tester: ______
- Test date: ______

5. How to Run the Application

Install the dependencies:

pip install -r requirements.txt

Start the application:

streamlit run app.py

Configure the required Google OAuth credentials and Gemini API key using Streamlit secrets or environment variables, as supported by the application. Never commit real credentials to GitHub.

6. Notes

These are planned manual test cases, not verified test results. Some tests require Google authentication, an AI API key, or features that may not yet be implemented.

If the app stores transactions only in session state, data persistence across sessions or users needs separate testing and implementation.
