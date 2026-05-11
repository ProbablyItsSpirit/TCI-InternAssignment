## Would suggest you to read Decision Log for better explainations 
## V1 Basic Prompt

### Goal
- That it generate simple payment reminder emails.

### Prompt
- Write a follow up email for overdue payment.

### Problems Observed
- Emails sounded robotic
- No escalation behavior
- Repetitive structure
- Generic subjects
- No personalization
- Weak business realism

### Decision
- Move to structured context driven prompts.

## V2 Context-Awarness 

### Changes added
- Client name
- Invoice number
- Amount due
- Due date
- Days overdue
- Payment link

### Resulted
- Better personalization
- More realistic outputs
- Improved contextual awareness

### Problems noticed
- Tone still too similar across stages (same for stage 1 and 4)
- Some repetitive language patterns

## V3 Tone Escalation Fixed

### Improvements Added
- Separate tone rules for each escalation stage.\
- Escalate tone appropriately based on stage.


### Stage Behaviors
| Stage | Tone |
|---|---|
| Stage 1 | Warm and friendly |
| Stage 2 | Polite but firm |
| Stage 3 | Formal and serious |
| Stage 4 | Stern and urgent |


### Results
- More stronger business sounding
- Clear escalation differentiation
- Noticed some hallucinations and placeholders


## V4 Structured JSON Outputs

### Improvements Added
- Prevent parsing inconsistencies.
- Strict JSON-only responses

- Return ONLY raw JSON
- Do NOT wrap output in markdown.

### Example
```json
{
	"subject": "...",
	"body": "...",
	"tone": "...",
	"stage": "..."
}
```

### Results seen
- Reliable downstream processing
- Easier audit logging
- Cleaner UI integration

## V5 Hallucination Fixed

### Problem
- Placeholder names like [Your Name]
- Occasional fabricated details

### Improvement
- Never use placeholders.
- Always sign off as:
	Finance Collections Team
    (Talk in third person)

### Results
- More professional outputs
- Reduced hallucinated placeholders
- Cleaner business communication

## V6 Enterprise Realism

### Improvements Added
- Subject urgency escalation
- Professional greetings
- Natural business phrasing
- Call-to-action rules

### Example CTA Rules (Not like a threat)
- Request response within 48 hours.
- Demand immediate action to avoid escalation.

### Results
- Human sounding finance communication
- Stronger production readiness
