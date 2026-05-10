### Why I selected Task 2
Decided to do Task 2 because I found it more interesting and also has LLM orchestration and backend automation.
I've one day to build this, short on time.

### Phase 1
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
Added email_agent so it can make follow up mails.

Creating escalation agent and then removing the need of using utils.. When a seperatable structure like this is followed, the app becomes easy to edit and modular and get more customization.

Created proper llm service for it's guide

Trying llama3.3 first

Amazing till now this is what it generated:

---

**Client:** Priya Sharma - INV-2026-002

**Subject:**
Overdue Payment Notification for INV-2026-002

**Body:**
Dear Priya Sharma, this is a follow-up on your overdue payment of ₹78000 for Invoice INV-2026-002. The payment was due on 28-04-2026 and is now 12 days overdue. To avoid further action, please settle the amount immediately using the payment link: https://pay.company.com/INV-2026-002. We appreciate your prompt attention to this matter.

**Tone:** Stage 2
</div>

---
But this still requires a little prompt update for it's tone. And it kinda sounds like very robotic or ai generated.

