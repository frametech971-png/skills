<!-- jp-email-sequence v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-email-sequence（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-email-sequence
description: >-
  ウェルカム・育成・再エンゲージメント・購入後などのステップメール（メールシーケンス、ドリップ、ライフサイクルメール）を設計して文面まで作る。日本の受信者に送るときは特定電子メール法（オプトイン、同意記録の保存、配信停止、フッターの表示義務）を各メールに反映する。「新規会員向けのステップメールを作って」「休眠顧客の掘り起こしメールを3通」「メルマガのフッターに何を書けばいい？」「名刺交換した相手に案内メールを送っていい？」「配信停止した人に送っていいメールは？」と頼まれたときに使う。Keywords: email sequence, drip campaign, nurture, lifecycle email, welcome series, ステップメール, メルマガ, 特定電子メール法。名簿を買って送る一斉配信・同意の無い営業メールの作成は対象外（法的に送れない相手を示す）。SMS・LINE の配信、アプリ内オンボーディングは対象外。
license: MIT
metadata:
  version: "1.0.0"
  author: frametech
---

# Email Sequence Design（日本向け）

元: https://github.com/coreyhaines31/marketingskills@1efedbc（`skills/emails`、MIT、`LICENSE`）を改変。日本の受信者向けの法令（[references/japan-email-law.md](references/japan-email-law.md)）を追加。

**受信者が日本にいる、または日本語のメールを作るときは、設計の前に [references/japan-email-law.md](references/japan-email-law.md) を読む。** 送ってよい相手か（§1）を最初に確かめ、全メールにフッターの表示事項（§4）を入れ、再エンゲージメントには配信停止の選択肢（§3）を入れる。法的な結論は断定しない。

You are an expert in email marketing and automation. Your goal is to create email sequences that nurture relationships, drive action, and move people toward conversion.

## Reference Routing

Load the matching reference before drafting or auditing the relevant part of a sequence. Combine references when the request includes both flow design and individual email copy.

| User intent | Load | Covers |
|---|---|---|
| Build a welcome, lead nurture, re-engagement, or product onboarding flow | [sequence-templates.md](references/sequence-templates.md) | Sequence goals, timing, email order, and conversion actions |
| Identify missing lifecycle emails or audit onboarding, retention, billing, usage, win-back, or campaigns | [email-types.md](references/email-types.md) | Email purposes, triggers, audiences, and the lifecycle audit checklist |
| Write or edit individual emails within a sequence; improve CTA, personalization, or segmentation | [copy-guidelines.md](references/copy-guidelines.md) | Structure, tone, length, merge fields, dynamic content, and copy testing |

## Initial Assessment

**Check for product marketing context first:**
If the project has a product-marketing context file (for example `product-marketing.md`), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before creating a sequence, understand:

1. **Sequence Type**
   - Welcome/onboarding sequence
   - Lead nurture sequence
   - Re-engagement sequence
   - Post-purchase sequence
   - Event-based sequence
   - Educational sequence
   - Sales sequence

2. **Audience Context**
   - Who are they?
   - What triggered them into this sequence?
   - What do they already know/believe?
   - What's their current relationship with you?

3. **Goals**
   - Primary conversion goal
   - Relationship-building goals
   - Segmentation goals
   - What defines success?

---

## Core Principles

### 1. One Email, One Job
- Each email has one primary purpose
- One main CTA per email
- Don't try to do everything

### 2. Value Before Ask
- Lead with usefulness
- Build trust through content
- Earn the right to sell

### 3. Relevance Over Volume
- Fewer, better emails win
- Segment for relevance
- Quality > frequency

### 4. Clear Path Forward
- Every email moves them somewhere
- Links should do something useful
- Make next steps obvious

---

## Email Sequence Strategy

### Sequence Length
- Welcome: 3-7 emails
- Lead nurture: 5-10 emails
- Onboarding: 5-10 emails
- Re-engagement: 3-5 emails

Depends on:
- Sales cycle length
- Product complexity
- Relationship stage

### Timing/Delays
- Welcome email: Immediately
- Early sequence: 1-2 days apart
- Nurture: 2-4 days apart
- Long-term: Weekly or bi-weekly

Consider:
- B2B: Avoid weekends
- B2C: Test weekends
- Time zones: Send at local time

### Subject Line Strategy
- Clear > Clever
- Specific > Vague
- Benefit or curiosity-driven
- 40-60 characters ideal
- Test emoji (they're polarizing)

**Patterns that work:**
- Question: "Still struggling with X?"
- How-to: "How to [achieve outcome] in [timeframe]"
- Number: "3 ways to [benefit]"
- Direct: "[First name], your [thing] is ready"
- Story tease: "The mistake I made with [topic]"

### Preview Text
- Extends the subject line
- ~90-140 characters
- Don't repeat subject line
- Complete the thought or add intrigue

---

## Sequence Types Overview

### Welcome Sequence (Post-Signup)
**Length**: 5-7 emails over 12-14 days
**Goal**: Activate, build trust, convert

Key emails:
1. Welcome + deliver promised value (immediate)
2. Quick win (day 1-2)
3. Story/Why (day 3-4)
4. Social proof (day 5-6)
5. Overcome objection (day 7-8)
6. Core feature highlight (day 9-11)
7. Conversion (day 12-14)

### Lead Nurture Sequence (Pre-Sale)
**Length**: 6-8 emails over 2-3 weeks
**Goal**: Build trust, demonstrate expertise, convert

Key emails:
1. Deliver lead magnet + intro (immediate)
2. Expand on topic (day 2-3)
3. Problem deep-dive (day 4-5)
4. Solution framework (day 6-8)
5. Case study (day 9-11)
6. Differentiation (day 12-14)
7. Objection handler (day 15-18)
8. Direct offer (day 19-21)

### Re-Engagement Sequence
**Length**: 3-4 emails over 2 weeks
**Trigger**: 30-60 days of inactivity
**Goal**: Win back or clean list

Key emails:
1. Check-in (genuine concern)
2. Value reminder (what's new)
3. Incentive (special offer)
4. Last chance (stay or unsubscribe)

### Onboarding Sequence (Product Users)
**Length**: 5-7 emails over 14 days
**Goal**: Activate, drive to aha moment, upgrade
**Note**: Coordinate with in-app onboarding—email supports, doesn't duplicate

Key emails:
1. Welcome + first step (immediate)
2. Getting started help (day 1)
3. Feature highlight (day 2-3)
4. Success story (day 4-5)
5. Check-in (day 7)
6. Advanced tip (day 10-12)
7. Upgrade/expand (day 14+)

**For detailed templates**: See [references/sequence-templates.md](references/sequence-templates.md)

---

## Email Types by Category

### Onboarding Emails
- New users series
- New customers series
- Key onboarding step reminders
- New user invites

### Retention Emails
- Upgrade to paid
- Upgrade to higher plan
- Ask for review
- Proactive support offers
- Product usage reports
- NPS survey
- Referral program

### Billing Emails
- Switch to annual
- Failed payment recovery
- Cancellation survey
- Upcoming renewal reminders

### Usage Emails
- Daily/weekly/monthly summaries
- Key event notifications
- Milestone celebrations

### Win-Back Emails
- Expired trials
- Cancelled customers

### Campaign Emails
- Monthly roundup / newsletter
- Seasonal promotions
- Product updates
- Industry news roundup
- Pricing updates

**For detailed email type reference**: See [references/email-types.md](references/email-types.md)

---

## Email Copy Guidelines

### Structure
1. **Hook**: First line grabs attention
2. **Context**: Why this matters to them
3. **Value**: The useful content
4. **CTA**: What to do next
5. **Sign-off**: Human, warm close

### Formatting
- Short paragraphs (1-3 sentences)
- White space between sections
- Bullet points for scanability
- Bold for emphasis (sparingly)
- Mobile-first (most read on phone)

### Tone
- Conversational, not formal
- First-person (I/we) and second-person (you)
- Active voice
- Read it out loud. Does it sound like a person?

### No AI Tells

Subscribers learn to recognize generated email fast, and they stop reading. Write from the specific thing you want them to know or do.

Never write these:
- **Contrast reveals**: "It's not X, it's Y." "Not because X. Because Y." State Y directly, with the reason.
- **Negation lists**: "No X, no Y, no Z." Say what does happen. One plain absence ("No card required") is fine.
- **Trailing pile-ons**: a full claim, then a comma and more restating clauses. End the sentence at the claim.
- **Self-answered questions and colon reveals**: "The result? 3x faster." "The best part: it learns." FAQ questions and a question in the reader's own voice are fine.
- **Stock phrases**: "Say goodbye to," "X, reimagined," "Unlock the power of," "Take it to the next level," "Here's the thing."
- **Em dashes** in subject lines and preview text, and at most one or two in a long email.

Email-specific tells:
- **Subject-line bait**: fake "Re:" or "Fwd:", "You won't believe...", "🔥 Big news." The subject should hold up if it's the only line they read.
- **Stock openers**: "I hope this email finds you well," "Just checking in," "Great news!" Open with the reason you're writing.
- **Sign-off filler**: "Feel free to reach out if you have any questions." Ask for one specific action, or end.


### Length
- 50-125 words for transactional
- 150-300 words for educational
- 300-500 words for story-driven

### CTA Guidelines
- Buttons for primary actions
- Links for secondary actions
- One clear primary CTA per email
- Button text: Action + outcome

**For detailed copy, personalization, and testing guidelines**: See [references/copy-guidelines.md](references/copy-guidelines.md)

---

## Output Format

### Sequence Overview
```
Sequence Name: [Name]
Trigger: [What starts the sequence]
Goal: [Primary conversion goal]
Length: [Number of emails]
Timing: [Delay between emails]
Exit Conditions: [When they leave the sequence]
```

### For Each Email
```
Email [#]: [Name/Purpose]
Send: [Timing]
Subject: [Subject line]
Preview: [Preview text]
Body: [Full copy]
CTA: [Button text] → [Link destination]
Segment/Conditions: [If applicable]
```

### Metrics Plan
What to measure and benchmarks

---

## Task-Specific Questions

1. What triggers entry to this sequence?
2. What's the primary goal/conversion action?
3. What do they already know about you?
4. What other emails are they receiving?
5. What's your current email performance?

---

## Tool Integrations

For implementation, see the [tools registry](https://github.com/coreyhaines31/marketingskills/blob/main/tools/REGISTRY.md). Key email tools:

| Tool | Best For | MCP | Guide |
|------|----------|:---:|-------|
| **Customer.io** | Behavior-based automation | - | [customer-io.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/customer-io.md) |
| **Mailchimp** | SMB email marketing | ✓ | [mailchimp.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/mailchimp.md) |
| **Nitrosend** | AI-native email (sequences via prompts) | ✓ | [nitrosend.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/nitrosend.md) |
| **Resend** | Developer-friendly transactional | ✓ | [resend.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/resend.md) |
| **SendGrid** | Transactional email at scale | - | [sendgrid.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/sendgrid.md) |
| **Kit** | Creator/newsletter focused | - | [kit.md](https://github.com/coreyhaines31/marketingskills/blob/main/tools/integrations/kit.md) |

---

## Out of scope

- 同意の無い相手への営業メール（cold email）・名簿を買っての一斉配信: 日本の受信者には送れない相手が多い（japan-email-law.md §1）。送れる相手の条件を示すにとどめる
- アプリ内のオンボーディング、SMS・LINE の配信

=== FILE: references/copy-guidelines.md ===
# Email Copy Guidelines

## Contents
- Structure
- Formatting
- Tone
- Length
- CTA Buttons vs. Links
- Personalization (merge fields, dynamic content, triggered emails)
- Segmentation Strategies (by behavior, by stage, by profile)
- Testing and Optimization (what to test, how to test, metrics to track)

## Structure

1. **Hook**: First line grabs attention
2. **Context**: Why this matters to them
3. **Value**: The useful content
4. **CTA**: What to do next
5. **Sign-off**: Human, warm close

## Formatting

- Short paragraphs (1-3 sentences)
- White space between sections
- Bullet points for scanability
- Bold for emphasis (sparingly)
- Mobile-first (most read on phone)

## Tone

- Conversational, not formal
- First-person (I/we) and second-person (you)
- Active voice
- Match your brand but lean friendly
- Read it out loud—does it sound human?

## Length

- Shorter is usually better
- 50-125 words for transactional
- 150-300 words for educational
- 300-500 words for story-driven
- If it's long, it better be good

## CTA Buttons vs. Links

- Buttons: Primary actions, high-visibility
- Links: Secondary actions, in-text
- One clear primary CTA per email
- Button text: Action + outcome

---

## Personalization

### Merge Fields
- First name (fallback to "there" or "friend")
- Company name (B2B)
- Relevant data (usage, plan, etc.)

### Dynamic Content
- Based on segment
- Based on behavior
- Based on stage

### Triggered Emails
- Action-based sends
- More relevant than time-based
- Examples: Feature used, milestone hit, inactivity

---

## Segmentation Strategies

### By Behavior
- Openers vs. non-openers
- Clickers vs. non-clickers
- Active vs. inactive

### By Stage
- Trial vs. paid
- New vs. long-term
- Engaged vs. at-risk

### By Profile
- Industry/role (B2B)
- Use case / goal
- Company size

---

## Testing and Optimization

### What to Test
- Subject lines (highest impact)
- Send times
- Email length
- CTA placement and copy
- Personalization level
- Sequence timing

### How to Test
- A/B test one variable at a time
- Sufficient sample size
- Statistical significance
- Document learnings

### Metrics to Track
- Open rate (benchmark: 20-40%)
- Click rate (benchmark: 2-5%)
- Unsubscribe rate (keep under 0.5%)
- Conversion rate (specific to sequence goal)
- Revenue per email (if applicable)

=== FILE: references/email-types.md ===
# Email Types Reference

A comprehensive guide to lifecycle and campaign emails. Use this as an audit checklist and implementation reference.

## Contents
- Onboarding Emails (new users series, new customers series, key onboarding step reminder, new user invite)
- Retention Emails (upgrade to paid, upgrade to higher plan, ask for review, offer support proactively, product usage report, NPS survey, referral program)
- Billing Emails (switch to annual, failed payment recovery, cancellation survey, upcoming renewal reminder)
- Usage Emails (daily/weekly/monthly summary, key event or milestone notifications)
- Win-Back Emails (expired trials, cancelled customers)
- Campaign Emails (monthly roundup/newsletter, seasonal promotions, product updates, industry news roundup, pricing update)
- Email Audit Checklist (onboarding, retention, billing, usage, win-back, campaigns)

## Onboarding Emails

### New Users Series
**Trigger**: User signs up (free or trial)
**Goal**: Activate user, drive to aha moment
**Typical sequence**: 5-7 emails over 14 days

- Email 1: Welcome + single next step (immediate)
- Email 2: Quick win / getting started (day 1)
- Email 3: Key feature highlight (day 3)
- Email 4: Success story / social proof (day 5)
- Email 5: Check-in + offer help (day 7)
- Email 6: Advanced tip (day 10)
- Email 7: Upgrade prompt or next milestone (day 14)

**Key metrics**: Activation rate, feature adoption

---

### New Customers Series
**Trigger**: User converts to paid
**Goal**: Reinforce purchase decision, drive adoption, reduce early churn
**Typical sequence**: 3-5 emails over 14 days

- Email 1: Thank you + what's next (immediate)
- Email 2: Getting full value — setup checklist (day 2)
- Email 3: Pro tips for paid features (day 5)
- Email 4: Success story from similar customer (day 7)
- Email 5: Check-in + introduce support resources (day 14)

**Key point**: Different from new user series—they've committed. Focus on reinforcement and expansion, not conversion.

---

### Key Onboarding Step Reminder
**Trigger**: User hasn't completed critical setup step after X time
**Goal**: Nudge completion of high-value action
**Format**: Single email or 2-3 email mini-sequence

**Example triggers**:
- Hasn't connected integration after 48 hours
- Hasn't invited team member after 3 days
- Hasn't completed profile after 24 hours

**Copy approach**:
- Remind them what they started
- Explain why this step matters
- Make it easy (direct link to complete)
- Offer help if stuck

---

### New User Invite
**Trigger**: Existing user invites teammate
**Goal**: Activate the invited user
**Recipient**: The person being invited

- Email 1: You've been invited (immediate)
- Email 2: Reminder if not accepted (day 2)
- Email 3: Final reminder (day 5)

**Copy approach**:
- Personalize with inviter's name
- Explain what they're joining
- Single CTA to accept invite
- Social proof optional

---

## Retention Emails

### Upgrade to Paid
**Trigger**: Free user shows engagement, or trial ending
**Goal**: Convert free to paid
**Typical sequence**: 3-5 emails

**Trigger options**:
- Time-based (trial day 10, 12, 14)
- Behavior-based (hit usage limit, used premium feature)
- Engagement-based (highly active free user)

**Sequence structure**:
- Value summary: What they've accomplished
- Feature comparison: What they're missing
- Social proof: Who else upgraded
- Urgency: Trial ending, limited offer
- Final: Last chance + easy path

---

### Upgrade to Higher Plan
**Trigger**: User approaching plan limits or using features available on higher tier
**Goal**: Upsell to next tier
**Format**: Single email or 2-3 email sequence

**Trigger examples**:
- 80% of seat limit reached
- 90% of storage/usage limit
- Tried to use higher-tier feature
- Power user behavior patterns

**Copy approach**:
- Acknowledge their growth (positive framing)
- Show what next tier unlocks
- Quantify value vs. cost
- Easy upgrade path

---

### Ask for Review
**Trigger**: Customer milestone (30/60/90 days, key achievement, support resolution)
**Goal**: Generate social proof on G2, Capterra, app stores
**Format**: Single email

**Best timing**:
- After positive support interaction
- After achieving measurable result
- After renewal
- NOT after billing issues or bugs

**Copy approach**:
- Thank them for being a customer
- Mention specific value/milestone if possible
- Explain why reviews matter (help others decide)
- Direct link to review platform
- Keep it short—this is an ask

---

### Offer Support Proactively
**Trigger**: Signs of struggle (drop in usage, failed actions, error encounters)
**Goal**: Save at-risk user, improve experience
**Format**: Single email

**Trigger examples**:
- Usage dropped significantly week-over-week
- Multiple failed attempts at action
- Viewed help docs repeatedly
- Stuck at same onboarding step

**Copy approach**:
- Genuine concern tone
- Specific: "I noticed you..." (if data allows)
- Offer direct help (not just link to docs)
- Personal from support or CSM
- No sales pitch—pure help

---

### Product Usage Report
**Trigger**: Time-based (weekly, monthly, quarterly)
**Goal**: Demonstrate value, drive engagement, reduce churn
**Format**: Single email, recurring

**What to include**:
- Key metrics/activity summary
- Comparison to previous period
- Achievements/milestones
- Suggestions for improvement
- Light CTA to explore more

**Examples**:
- "You saved X hours this month"
- "Your team completed X projects"
- "You're in the top X% of users"

**Key point**: Make them feel good and remind them of value delivered.

---

### NPS Survey
**Trigger**: Time-based (quarterly) or event-based (post-milestone)
**Goal**: Measure satisfaction, identify promoters and detractors
**Format**: Single email

**Best practices**:
- Keep it simple: Just the NPS question initially
- Follow-up form for "why" based on score
- Personal sender (CEO, founder, CSM)
- Tell them how you'll use feedback

**Follow-up based on score**:
- Promoters (9-10): Thank + ask for review/referral
- Passives (7-8): Ask what would make it a 10
- Detractors (0-6): Personal outreach to understand issues

---

### Referral Program
**Trigger**: Customer milestone, promoter NPS score, or campaign
**Goal**: Generate referrals
**Format**: Single email or periodic reminders

**Good timing**:
- After positive NPS response
- After customer achieves result
- After renewal
- Seasonal campaigns

**Copy approach**:
- Remind them of their success
- Explain the referral offer clearly
- Make sharing easy (unique link)
- Show what's in it for them AND referee

---

## Billing Emails

### Switch to Annual
**Trigger**: Monthly subscriber at renewal time or campaign
**Goal**: Convert monthly to annual (improve LTV, reduce churn)
**Format**: Single email or 2-email sequence

**Value proposition**:
- Calculate exact savings
- Additional benefits (if any)
- Lock in current price messaging
- Easy one-click switch

**Best timing**:
- Around monthly renewal date
- End of year / new year
- After 3-6 months of loyalty
- Price increase announcement (lock in old rate)

---

### Failed Payment Recovery
**Trigger**: Payment fails
**Goal**: Recover revenue, retain customer
**Typical sequence**: 3-4 emails over 7-14 days

**Sequence structure**:
- Email 1 (Day 0): Friendly notice, update payment link
- Email 2 (Day 3): Reminder, service may be interrupted
- Email 3 (Day 7): Urgent, account will be suspended
- Email 4 (Day 10-14): Final notice, what they'll lose

**Copy approach**:
- Assume it's an accident (card expired, etc.)
- Clear, direct, no guilt
- Single CTA to update payment
- Explain what happens if not resolved

**Key metrics**: Recovery rate, time to recovery

---

### Cancellation Survey
**Trigger**: User cancels subscription
**Goal**: Learn why, opportunity to save
**Format**: Single email (immediate)

**Options**:
- In-app survey at cancellation (better completion)
- Follow-up email if they skip in-app
- Personal outreach for high-value accounts

**Questions to ask**:
- Primary reason for cancelling
- What could we have done better
- Would anything change your mind
- Can we help with transition

**Winback opportunity**: Based on reason, offer targeted save (discount, pause, downgrade, training).

---

### Upcoming Renewal Reminder
**Trigger**: X days before renewal (14 or 30 days typical)
**Goal**: No surprise charges, opportunity to expand
**Format**: Single email

**What to include**:
- Renewal date and amount
- What's included in renewal
- How to update payment/plan
- Changes to pricing/features (if any)
- Optional: Upsell opportunity

**Required for**: Annual subscriptions, high-value contracts

---

## Usage Emails

### Daily/Weekly/Monthly Summary
**Trigger**: Time-based
**Goal**: Drive engagement, demonstrate value
**Format**: Single email, recurring

**Content by frequency**:
- **Daily**: Notifications, quick stats (for high-engagement products)
- **Weekly**: Activity summary, highlights, suggestions
- **Monthly**: Comprehensive report, achievements, ROI if calculable

**Structure**:
- Key metrics at a glance
- Notable achievements
- Activity breakdown
- Suggestions / what to try next
- CTA to dive deeper

**Personalization**: Must be relevant to their actual usage. Empty reports are worse than no report.

---

### Key Event or Milestone Notifications
**Trigger**: Specific achievement or event
**Goal**: Celebrate, drive continued engagement
**Format**: Single email per event

**Milestone examples**:
- First [action] completed
- 10th/100th [thing] created
- Goal achieved
- Team collaboration milestone
- Usage streak

**Copy approach**:
- Celebration tone
- Specific achievement
- Context (compared to others, compared to before)
- What's next / next milestone

---

## Win-Back Emails

### Expired Trials
**Trigger**: Trial ended without conversion
**Goal**: Convert or re-engage
**Typical sequence**: 3-4 emails over 30 days

**Sequence structure**:
- Email 1 (Day 1 post-expiry): Trial ended, here's what you're missing
- Email 2 (Day 7): What held you back? (gather feedback)
- Email 3 (Day 14): Incentive offer (discount, extended trial)
- Email 4 (Day 30): Final reach-out, door is open

**Segmentation**: Different approach based on trial engagement level:
- High engagement: Focus on removing friction to convert
- Low engagement: Offer fresh start, more onboarding help
- No engagement: Ask what happened, offer demo/call

---

### Cancelled Customers
**Trigger**: Time after cancellation (30, 60, 90 days)
**Goal**: Win back churned customers
**Typical sequence**: 2-3 emails spread over 90 days

**Sequence structure**:
- Email 1 (Day 30): What's new since you left
- Email 2 (Day 60): We've addressed [common reason]
- Email 3 (Day 90): Special offer to return

**Copy approach**:
- No guilt, no desperation
- Genuine updates and improvements
- Personalize based on cancellation reason if known
- Make return easy

**Key point**: They're more likely to return if their reason was addressed.

---

## Campaign Emails

### Monthly Roundup / Newsletter
**Trigger**: Time-based (monthly)
**Goal**: Engagement, brand presence, content distribution
**Format**: Single email, recurring

**Content mix**:
- Product updates and tips
- Customer stories
- Educational content
- Company news
- Industry insights

**Best practices**:
- Consistent send day/time
- Scannable format
- Mix of content types
- One primary CTA focus
- Unsubscribe is okay—keeps list healthy

---

### Seasonal Promotions
**Trigger**: Calendar events (Black Friday, New Year, etc.)
**Goal**: Drive conversions with timely offer
**Format**: Campaign burst (2-4 emails)

**Common opportunities**:
- New Year (fresh start, annual planning)
- End of fiscal year (budget spending)
- Black Friday / Cyber Monday
- Industry-specific seasons
- Back to school / work

**Sequence structure**:
- Announcement: Offer reveal
- Reminder: Midway through promotion
- Last chance: Final hours

---

### Product Updates
**Trigger**: New feature release
**Goal**: Adoption, engagement, demonstrate momentum
**Format**: Single email per major release

**What to include**:
- What's new (clear and simple)
- Why it matters (benefit, not just feature)
- How to use it (direct link)
- Who asked for it (community acknowledgment)

**Segmentation**: Consider targeting based on relevance:
- Users who would benefit most
- Users who requested feature
- Power users first (for beta feel)

---

### Industry News Roundup
**Trigger**: Time-based (weekly or monthly)
**Goal**: Thought leadership, engagement, brand value
**Format**: Curated newsletter

**Content**:
- Curated news and links
- Your take / commentary
- What it means for readers
- How your product helps

**Best for**: B2B products where customers care about industry trends.

---

### Pricing Update
**Trigger**: Price change announcement
**Goal**: Transparent communication, minimize churn
**Format**: Single email (or sequence for major changes)

**Timeline**:
- Announce 30-60 days before change
- Reminder 14 days before
- Final notice 7 days before

**Copy approach**:
- Clear, direct, transparent
- Explain the why (value delivered, costs increased)
- Grandfather if possible (lock in old rate)
- Give options (annual lock-in, downgrade)

**Important**: Honesty and advance notice build trust even when price increases.

---

## Email Audit Checklist

Use this to audit your current email program:

### Onboarding
- [ ] New users series
- [ ] New customers series
- [ ] Key onboarding step reminders
- [ ] New user invite sequence

### Retention
- [ ] Upgrade to paid sequence
- [ ] Upgrade to higher plan triggers
- [ ] Ask for review (timed properly)
- [ ] Proactive support outreach
- [ ] Product usage reports
- [ ] NPS survey
- [ ] Referral program emails

### Billing
- [ ] Switch to annual campaign
- [ ] Failed payment recovery sequence
- [ ] Cancellation survey
- [ ] Upcoming renewal reminders

### Usage
- [ ] Daily/weekly/monthly summaries
- [ ] Key event notifications
- [ ] Milestone celebrations

### Win-Back
- [ ] Expired trial sequence
- [ ] Cancelled customer sequence

### Campaigns
- [ ] Monthly roundup / newsletter
- [ ] Seasonal promotion calendar
- [ ] Product update announcements
- [ ] Pricing update communications

=== FILE: references/japan-email-law.md ===
# 日本の受信者に送る広告・宣伝メールのルール（特定電子メール法）

日本の受信者に、営利目的の団体・個人事業者が広告・宣伝を含むメール（メルマガ、キャンペーン、休眠顧客の掘り起こし、営業メールなど）を送る設計をするときに読む。シーケンスの各メールの本文・フッター・送信リストの条件に反映させる。

**確認日 2026-10-12。90日を過ぎたら §5 の条文を読み直す。** 法的な結論は断定せず、条文と該当しうる点を示し、「最終判断は社内の法務担当者が行う」と添える。

## 1. 送ってよい相手（法第3条第1項）

広告・宣伝メールは、次の相手**だけ**に送れる。

1. あらかじめ受信に同意した人（オプトイン）
2. 書面（名刺など）で自分のメールアドレスを通知してきた人
3. 広告・宣伝する事業と取引関係にある人（既存の顧客など）
4. 自分のメールアドレスをインターネットで公表している団体・営業中の個人。ただし、アドレスと一緒に「広告・宣伝メールお断り」の旨を公表している場合は除く（施行規則第3条）

- **購入・譲受した名簿、Web から集めたアドレスへの一斉配信は、上のどれにも当たらなければ送れない。** 「海外では cold email が普通」という前提を日本の受信者に当てはめない
- 同意を取るときは、何の・誰からのメールが届くのかが分かる画面にする

## 2. 同意の記録（法第3条第2項、施行規則第4条）

- 1 の人については、同意を受けたことを示す記録を保存する（同意を受けた時期・方法、フォームの定型の文言など）
- 保存期間: その人に**最後に送信した日から1か月**。措置命令を受けた場合は**1年**
- シーケンスを設計するときは、配信ツールに「同意日時・取得元（フォーム名・ページ）」の項目を持たせる

## 3. 配信停止（法第3条第3項、施行規則第5条・第6条）

- 受信を拒否された相手には、その意思に反して広告・宣伝メールを送ってはならない（一部の種類だけ拒否されたら、その種類を止める）
- 例外: 注文・契約の確認や履行の通知など、**取引に関する連絡が主のメールに広告が付随するだけ**なら、拒否した人にも送れる（施行規則第6条第1号）。広告が主になったら例外ではない
- 再エンゲージメント（休眠顧客の掘り起こし）の最後のメールは「配信を続けるか、停止するか」を選べるようにし、停止を選んだ人のリストからは外す

## 4. メールに必ず表示する事項（法第4条、施行規則第7条・第9条）

すべての広告・宣伝メールのフッターに入れる:

| 表示する事項 | 根拠 |
|---|---|
| 送信者（送信に責任を持つ者）の氏名または名称 | 法第4条第1号 |
| 配信停止の通知を受けるメールアドレスまたは URL | 法第4条第2号 |
| 配信停止ができる旨（上のアドレス・URL の直前か直後に） | 施行規則第9条第1号・第7条 |
| 送信者の住所 | 施行規則第9条第2号 |
| 苦情・問い合わせを受け付ける電話番号、メールアドレスまたは URL | 施行規則第9条第3号 |

フッターの例（シーケンスの各メールに付ける）:

```text
――――――――――
配信元: 株式会社サンプル（〒100-0001 東京都千代田区千代田1-1）
このメールは、当社サービスにご登録いただいた方にお送りしています。
配信の停止はこちら: https://example.com/unsubscribe
お問い合わせ: support@example.com ／ 03-0000-0000（平日10〜18時）
```

## 4-2. 訴求の書き方（景品表示法）

- 「本日まで」「残り3名」「上位5%のユーザー」「通常価格◯円→◯円」のような期限・数量・順位・比較価格は、**事実のときだけ**書く。事実でない期限や、実際に販売実績の無い「通常価格」との比較は、有利誤認（景品表示法第5条第2号）になりうる
- 偽の「Re:」「Fwd:」の件名で返信や転送を装わない（受信者をだます件名は使わない。元のスキルの規則と同じ）
- 出典: e-Gov 法令検索「不当景品類及び不当表示防止法」: https://laws.e-gov.go.jp/law/337AC0000000134

## 5. 違反したとき（法第7条・第34条・第37条）

- 総務大臣・内閣総理大臣（消費者庁）が措置命令を出すことができ、命令に違反すると**1年以下の拘禁刑または100万円以下の罰金**、法人は**3,000万円以下の罰金**
- 送信者情報を偽った送信（法第5条）も同じ罰則

## 6. 出典（確認日 2026-10-12）

- e-Gov 法令検索「特定電子メールの送信の適正化等に関する法律」（平成14年法律第26号）: https://laws.e-gov.go.jp/law/414AC0100000026
- e-Gov 法令検索「特定電子メールの送信の適正化等に関する法律施行規則」（平成14年総務省令第66号）: https://laws.e-gov.go.jp/law/414M60000008066

=== FILE: references/sequence-templates.md ===
# Email Sequence Templates

Detailed templates for common email sequences.

## Contents
- Welcome Sequence (Post-Signup)
- Lead Nurture Sequence (Pre-Sale)
- Re-Engagement Sequence
- Onboarding Sequence (Product Users)

## Welcome Sequence (Post-Signup)

**Email 1: Welcome (Immediate)**
- Subject: Welcome to [Product]. Here's your first step
- Deliver what was promised (lead magnet, access, etc.)
- Single next action
- Set expectations for future emails

**Email 2: Quick Win (Day 1-2)**
- Subject: Get your first [result] in 10 minutes
- Enable small success
- Build confidence
- Link to helpful resource

**Email 3: Story/Why (Day 3-4)**
- Subject: Why we built [Product]
- Origin story or mission
- Connect emotionally
- Show you understand their problem

**Email 4: Social Proof (Day 5-6)**
- Subject: How [Customer] achieved [Result]
- Case study or testimonial
- Relatable to their situation
- Soft CTA to explore

**Email 5: Overcome Objection (Day 7-8)**
- Subject: "I don't have time for X." Sound familiar?
- Address common hesitation
- Reframe the obstacle
- Show easy path forward

**Email 6: Core Feature (Day 9-11)**
- Subject: Have you tried [Feature] yet?
- Highlight underused capability
- Show clear benefit
- Direct CTA to try it

**Email 7: Conversion (Day 12-14)**
- Subject: Ready to [upgrade/buy/commit]?
- Summarize value
- Clear offer
- Urgency if appropriate
- Risk reversal (guarantee, trial)

---

## Lead Nurture Sequence (Pre-Sale)

**Email 1: Deliver + Introduce (Immediate)**
- Deliver the lead magnet
- Brief intro to who you are
- Preview what's coming

**Email 2: Expand on Topic (Day 2-3)**
- Related insight to lead magnet
- Establish expertise
- Light CTA to content

**Email 3: Problem Deep-Dive (Day 4-5)**
- Articulate their problem deeply
- Show you understand
- Hint at solution

**Email 4: Solution Framework (Day 6-8)**
- Your approach/methodology
- Educational, not salesy
- Builds toward your product

**Email 5: Case Study (Day 9-11)**
- Real results from real customer
- Specific and relatable
- Soft CTA

**Email 6: Differentiation (Day 12-14)**
- Why your approach is different
- Address alternatives
- Build preference

**Email 7: Objection Handler (Day 15-18)**
- Common concern addressed
- FAQ or myth-busting
- Reduce friction

**Email 8: Direct Offer (Day 19-21)**
- Clear pitch
- Strong value proposition
- Specific CTA
- Urgency if available

---

## Re-Engagement Sequence

**Email 1: Check-In (Day 30-60 of inactivity)**
- Subject: Is everything okay, [Name]?
- Genuine concern
- Ask what happened
- Easy win to re-engage

**Email 2: Value Reminder (Day 2-3 after)**
- Subject: Remember when you [achieved X]?
- Remind of past value
- What's new since they left
- Quick CTA

**Email 3: Incentive (Day 5-7 after)**
- Subject: We miss you. Here's something special
- Offer if appropriate
- Limited time
- Clear CTA

**Email 4: Last Chance (Day 10-14 after)**
- Subject: Should we stop emailing you?
- Honest and direct
- One-click to stay or go
- Clean the list if no response

---

## Onboarding Sequence (Product Users)

Coordinate with in-app onboarding. Email supports, doesn't duplicate.

**Email 1: Welcome + First Step (Immediate)**
- Confirm signup
- One critical action
- Link directly to that action

**Email 2: Getting Started Help (Day 1)**
- If they haven't completed step 1
- Quick tip or video
- Support option

**Email 3: Feature Highlight (Day 2-3)**
- Key feature they should know
- Specific use case
- In-app link

**Email 4: Success Story (Day 4-5)**
- Customer who succeeded
- Relatable journey
- Motivational

**Email 5: Check-In (Day 7)**
- How's it going?
- Ask for feedback
- Offer help

**Email 6: Advanced Tip (Day 10-12)**
- Power feature
- For engaged users
- Level-up content

**Email 7: Upgrade/Expand (Day 14+)**
- For trial users: conversion push
- For free users: upgrade prompt
- For paid: expansion opportunity

=== FILE: LICENSE ===
MIT License

Copyright (c) 2025 Corey Haines

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
