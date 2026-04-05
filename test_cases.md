# NewsGenie — Test Cases
**Course End Project — Applied Generative AI Specialisation**

---

## TC-01 to TC-04: News Routing Tests

### TC-01 — Technology News
**Input:** `"What are the latest technology news stories today?"`
**Expected:** `query_type=news`, `news_category=technology`, ≥1 article returned
**Pass if:** Routing = `news`, response contains headlines

### TC-02 — Finance News
**Input:** `"Show me top finance and business headlines"`
**Expected:** `query_type=news`, `news_category=finance`, ≥1 article returned
**Pass if:** Routing = `news`, response contains business/finance headlines

### TC-03 — Sports News
**Input:** `"What are today's top sports stories?"`
**Expected:** `query_type=news`, `news_category=sports`, ≥1 article returned
**Pass if:** Routing = `news`, response contains sports headlines

### TC-04 — Health News
**Input:** `"Latest news in health and medicine"`
**Expected:** `query_type=news`, `news_category=health`, ≥1 article returned
**Pass if:** Routing = `news`, response contains health headlines

---

## TC-05 to TC-09: Chat Routing Tests

### TC-05 — Factual Chat
**Input:** `"What is machine learning?"`
**Expected:** `query_type=chat`, LLM provides a clear definition
**Pass if:** Routing = `chat`, response is a coherent explanation (>50 chars)

### TC-06 — Conceptual Chat
**Input:** `"Explain the difference between AI and deep learning"`
**Expected:** `query_type=chat`, LLM explains both concepts
**Pass if:** Routing = `chat`, response mentions both AI and deep learning

### TC-07 — Product Info Chat
**Input:** `"What is ChatGPT and who made it?"`
**Expected:** `query_type=chat`, mentions OpenAI and GPT
**Pass if:** Routing = `chat`, response mentions OpenAI

### TC-08 — Opinion/Recommendation Chat
**Input:** `"Which news categories are most important to follow?"`
**Expected:** `query_type=chat`, LLM gives a helpful recommendation
**Pass if:** Routing = `chat`, has a non-empty response

### TC-09 — Science Explanation Chat
**Input:** `"How does quantum computing work?"`
**Expected:** `query_type=chat`, clear scientific explanation
**Pass if:** Routing = `chat`, response is educational

---

## TC-10 to TC-13: Web Search Routing Tests

### TC-10 — Current Events Search
**Input:** `"What is the latest news about OpenAI?"`
**Expected:** `query_type=search` or `news`, current information returned
**Pass if:** Has a non-empty response with relevant content

### TC-11 — Live Data Search
**Input:** `"Search for recent developments in electric vehicles"`
**Expected:** `query_type=search`, web results synthesised into answer
**Pass if:** Routing = `search`, response contains EV-related content

### TC-12 — Person/Organisation Search
**Input:** `"Who is the current CEO of Microsoft?"`
**Expected:** `query_type=search`, returns Satya Nadella
**Pass if:** Routing = `search`, response contains relevant name

### TC-13 — Technology Search
**Input:** `"What are the latest large language models released in 2024?"`
**Expected:** `query_type=search`, lists recent LLM releases
**Pass if:** Has a response mentioning LLMs

---

## TC-14 to TC-17: Science & General News Tests

### TC-14 — Science News
**Input:** `"What's happening in science and space exploration today?"`
**Expected:** `query_type=news`, `news_category=science`
**Pass if:** Routing = `news`, response contains science/space content

### TC-15 — General Headlines
**Input:** `"Give me the top general news headlines"`
**Expected:** `query_type=news`, `news_category=general`
**Pass if:** Routing = `news`, ≥1 headline in response

### TC-16 — Category-specific with query word
**Input:** `"Tell me about the latest AI technology breakthroughs"`
**Expected:** `query_type=news`, `news_category=technology`
**Pass if:** Routing = `news`, response has AI/tech content

### TC-17 — Mixed intent
**Input:** `"What is blockchain and what is the latest blockchain news?"`
**Expected:** Either `news` or `chat` type — both acceptable
**Pass if:** Has a non-empty response with blockchain content

---

## TC-18 to TC-22: Multi-Turn Memory Tests

### TC-18 — Basic follow-up
**Turn 1:** `"What are the latest technology news?"`
**Turn 2:** `"Which of those stories do you think is most important?"`
**Expected on Turn 2:** Agent references news from Turn 1 (memory active)
**Pass if:** Turn 2 response is contextually relevant to Turn 1

### TC-19 — Memory with topic continuation
**Turn 1:** `"Tell me about health news today"`
**Turn 2:** `"What medical conditions were mentioned?"`
**Expected:** Turn 2 references health articles from Turn 1
**Pass if:** Turn 2 response is relevant to health content

### TC-20 — Multi-turn general chat
**Turn 1:** `"What is artificial intelligence?"`
**Turn 2:** `"How is it used in healthcare?"`
**Turn 3:** `"Summarise our conversation in one sentence"`
**Expected:** Turn 3 correctly summarises both previous exchanges
**Pass if:** Turn 3 mentions AI and healthcare

### TC-21 — Category switch memory
**Turn 1:** `"Show me finance news"`
**Turn 2:** `"Now show me sports news"`
**Turn 3:** `"Which topic had more interesting stories?"`
**Expected:** Turn 3 references both finance and sports topics
**Pass if:** Turn 3 response mentions both categories

### TC-22 — Follow-up on chat answer
**Turn 1:** `"Explain machine learning in simple terms"`
**Turn 2:** `"Give me a real-world example of what you described"`
**Expected:** Turn 2 builds on the ML explanation from Turn 1
**Pass if:** Turn 2 gives an ML-related example

---

## TC-23 to TC-26: Fallback & Error Handling Tests

### TC-23 — No NewsAPI key (DuckDuckGo fallback)
**Setup:** Remove or blank `NEWSAPI_KEY` in `.env`
**Input:** `"What are the latest finance news?"`
**Expected:** System uses DuckDuckGo fallback, still returns articles
**Pass if:** Response contains news articles (source will be DuckDuckGo)

### TC-24 — Ambiguous query
**Input:** `"news"`
**Expected:** Router classifies as `news`, `general` category
**Pass if:** Routing = `news`, returns general headlines (no crash)

### TC-25 — Very short query
**Input:** `"AI"`
**Expected:** Router classifies correctly (likely `news` or `search`)
**Pass if:** Non-empty response, no exception thrown

### TC-26 — Non-English keywords
**Input:** `"technology nachrichten" (German for technology news)`
**Expected:** System attempts to fetch tech news or asks for clarification
**Pass if:** No crash, returns some response

---

## TC-27 to TC-30: Streamlit UI Tests

### TC-27 — Category selector + news fetch
**Action:** Select "Sports" in sidebar dropdown, click "Today's Sports News" button
**Expected:** Chat shows sports headlines with route badge showing `news`
**Pass if:** Streamlit displays articles with source names

### TC-28 — Chat input via text box
**Action:** Type `"What is inflation?"` in chat input
**Expected:** Route badge = `chat`, LLM explains inflation
**Pass if:** Response visible in chat with correct route badge

### TC-29 — Test Cases page runs all 10 tests
**Action:** Navigate to 🧪 Test Cases page, click "Run All Test Cases"
**Expected:** Progress bar completes, results table shows ≥8/10 PASS
**Pass if:** Green rows ≥ 80% of total

### TC-30 — Clear chat resets conversation
**Action:** Send 3 messages, then click "🗑️ Clear Chat"
**Expected:** Chat history is emptied, only welcome message remains
**Pass if:** Chat area shows only the welcome message

---

## Quick Grading Checklist

- [ ] TC-01: Technology news fetched and displayed
- [ ] TC-02: Finance news fetched and displayed
- [ ] TC-03: Sports news fetched and displayed
- [ ] TC-05: Chat query answered correctly
- [ ] TC-10: Web search returns current information
- [ ] TC-18: Multi-turn memory — follow-up is contextually aware
- [ ] TC-23: DuckDuckGo fallback works without NewsAPI key
- [ ] TC-27: Streamlit category selector drives news results
- [ ] TC-29: ≥ 80% test cases pass in automated runner

**Pass criteria:** ≥ 24/30 test cases passing
