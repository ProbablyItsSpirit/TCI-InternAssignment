Decide to do Task 2 because I found it more interesting and also has LLM orchestration and backend automation.
One day to build this, short on time.

For AI I am going to use Gemini 1.5 either Locally/or with API.
And for simple UI streamlit ofc.

I'll work on mock data first. 
Generated Mock data like this: 

| invoice_no | client_name | amount | due_date | contact_email | follow_up_count | payment_link |
|---|---|---|---|---|---|---|
| INV-2026-001 | Some Name | AMT | DD-MM-YYYY | xyz@example.com | 1 | https://paymentlink.com/INV-2026-001 |

Replacing gemini api key with open weight llama through Nvidia
Added a basic email model structure for llm
Also a prompts file for the agents. Starting with get_email_prompt which will generate a mail to people who are overdue.

email_agent so it can make follow up mails.

Creating escalation agent and then removing the need of using utils.. When a seperatable structure like this is followed, the app becomes easy to edit and modular and get more customization.

Created proper llm service for it's guide
Trying llama3.3 first