"""
Annotation Guidelines for Research Dataset
==========================================

## 1. SENTIMENT ANNOTATION

Rate the OVERALL sentiment of the video content on a 5-point scale:

1 = VERY NEGATIVE
   - Strong criticism, hostility, or condemnation
   - Predominantly negative language
   - Examples: "This is a disaster", "Completely wrong", "Dangerous policy"

2 = NEGATIVE
   - Mild criticism or disapproval
   - More negative than positive
   - Examples: "Not ideal", "Has problems", "Could be better"

3 = NEUTRAL
   - Balanced presentation
   - Informational without strong opinion
   - Equal positive and negative points
   - Examples: "Here are the facts", "Some pros and cons"

4 = POSITIVE
   - Mild approval or support
   - More positive than negative
   - Examples: "Good approach", "Shows promise", "Generally beneficial"

5 = VERY POSITIVE
   - Strong endorsement or praise
   - Predominantly positive language
   - Examples: "Excellent solution", "Highly effective", "Game-changer"

6 = MIXED
   - Contains BOTH strongly positive AND strongly negative sentiment
   - Not just balanced - explicitly contradictory
   - Examples: "Great idea but terrible execution", "Love X but hate Y"

---

## 2. EMOTION ANNOTATION

Rate SIX emotions on 0-100 scale based on predominant emotional tone:

**JOY (0-100)**
- Happiness, excitement, celebration, optimism
- 0 = No joy present
- 50 = Moderate positivity
- 100 = Extreme enthusiasm/elation

**SADNESS (0-100)**
- Sorrow, disappointment, melancholy, grief
- 0 = No sadness
- 50 = Moderate concern/disappointment
- 100 = Deep sorrow/despair

**ANGER (0-100)**
- Frustration, outrage, hostility, indignation
- 0 = No anger
- 50 = Moderate frustration
- 100 = Extreme outrage/fury

**FEAR (0-100)**
- Worry, anxiety, alarm, dread
- 0 = No fear
- 50 = Moderate concern
- 100 = Panic/terror

**SURPRISE (0-100)**
- Shock, unexpectedness, revelation
- 0 = No surprise
- 50 = Moderate revelation
- 100 = Complete shock

**DISGUST (0-100)**
- Revulsion, contempt, disapproval
- 0 = No disgust
- 50 = Moderate disapproval
- 100 = Strong revulsion

**NOTE**: Multiple emotions can be high simultaneously (e.g., anger=80, fear=60)

---

## 3. CREDIBILITY ANNOTATION

Assess the credibility of claims based on:
- Factual accuracy
- Source citations
- Evidence presented
- Logical consistency

**HIGH CREDIBILITY**
- Cites reputable sources
- Presents verifiable facts
- Acknowledges limitations
- Balanced perspective
- Examples: Academic sources, verified data, expert interviews

**MEDIUM CREDIBILITY**
- Some evidence presented
- Mixed quality sources
- Some unverified claims
- Mostly reasonable arguments
- Examples: News reports, personal experience with some backing

**LOW CREDIBILITY**
- No sources cited
- Unverified claims
- Logical fallacies
- Cherry-picked evidence
- Examples: Anecdotal only, conspiracy theories, obvious bias

---

## 4. MISINFORMATION FLAG

Binary (YES/NO) - Does this video contain obvious false information?

**YES - Flag as misinformation if:**
- Makes demonstrably false factual claims
- Contradicts scientific consensus without evidence
- Spreads debunked conspiracy theories
- Misrepresents data or sources

**NO - Do not flag if:**
- Presents opinion (even if you disagree)
- Shows alternative viewpoints
- Acknowledges uncertainty
- Presents satire/comedy clearly

**WHEN IN DOUBT**: Check fact-checking sites (Snopes, PolitiFact, FactCheck.org)

---

## 5. ANNOTATION PROCESS

For each video:

1. **Read title and description** (30 seconds)
2. **Skim transcript** (2-3 minutes)
   - Look for key claims, tone, emotional language
   - Don't need to read every word
3. **Rate sentiment** (30 seconds)
4. **Rate emotions** (1 minute)
5. **Assess credibility** (1 minute)
   - Quick Google search if needed
6. **Flag misinformation** (30 seconds)

**Total time per video: ~5-7 minutes**

---

## 6. TIPS FOR CONSISTENCY

- Take breaks every 20 videos (avoid fatigue bias)
- Review your last 5 annotations before starting each session
- If uncertain, default to middle values (sentiment=3, emotions=50)
- Keep notes on difficult cases
- Re-annotate 20 random videos after finishing to check self-agreement

---

## 7. EDGE CASES

**Sarcasm/Satire:**
- Annotate the INTENDED message, not literal words
- If satirical but making serious point → annotate the point
- If pure comedy → sentiment=3 (neutral), low credibility

**Long videos (>30 min):**
- Sample 3 sections: beginning, middle, end
- Rate based on predominant sentiment across samples

**Multiple perspectives in one video:**
- Rate the CREATOR'S stance, not interviewees
- If truly balanced → sentiment=3, credibility=HIGH

**Missing transcript:**
- If auto-captions failed, watch 3-5 minutes manually
- If unwatchable, mark as "SKIP" and exclude from dataset
