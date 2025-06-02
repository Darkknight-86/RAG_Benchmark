Prompt Engineering for the RAG:

Format:
1. Explicitly separate context and question

    - Example: Use clear separators so the model knows what is background and what it should respond to.
    - Prompt:
        - Context:
            <insert retrieved passages here>

        - Question:
            <insert user question here>


2. Use instruction-based phrasing

    -  Example: Guide the model explicitly.
    - Prompt:
        - Answer the question based on the context provided. If the answer cannot be found in the context, say "Not found in context."

        - Context:
            <retrieved text>

        - Question:
            <question>


3. Control hallucination

    - Example: Explicitly instruct the model not to invent answers:
    - Prompt: Using only the information in the context, respond to the question     below. Do not include any outside knowledge or assumptions.


4. Maintain consistency

    - Example: Use a consistent template for all prompts — this helps reduce unpredictable output especially when used across many queries in production.


5. Include metadata tags

    - Example: If your context includes source titles, timestamps, or scores, format them like:

        - [Document Title: AI Research Overview]
            "Transformer models have revolutionized NLP..."

        - [Document Title: Recent ML Advances]
            "RAG combines retrieval and generation..."

        - Question: How does RAG work?


6. Overall Prompt Example:
You are an assistant that answers questions based only on the provided context. Do not use any external knowledge.

Context:
RAG (Retrieval-Augmented Generation) is a method where a retriever first pulls relevant documents from a knowledge base, and then a generator uses those documents to generate an answer. This helps reduce hallucinations and improve factual accuracy.

Question:
What is the role of the retriever in RAG?

Answer:
The retriever in RAG pulls relevant documents from a knowledge base to provide context for the generator.


Our Prompts:

Possible Example prompts

1. Using the methods and findings described in the paper “Prestige in Numbers” by Echenique and Olabisi, explain how MBA program rankings can be derived from student test score submissions and application behaviors, rather than expert opinions or self-reported school data. Why is this approach considered more resistant to manipulation, and how do the ‘m-measure’ and ‘tournament’ methods operationalize this ranking strategy?

2. 	
- Instruction: 
    Using only the information in the context provided, respond to the question below. Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say “Not found in context.”
- Context:
    - [Document Title: Prestige in Numbers – How Test Scores and Choices Reveal School Rankings]
        “This paper introduces a novel revealed-preference approach to ranking colleges and professional schools based on applicants’ choices and standardized test scores… Our methodology leverages the decentralized beliefs of potential students, as revealed through their application decisions… we implement two ranking methods: one based on monotone functions of test scores across schools, and another using score-adjusted tournaments between school pairs…”
	- [Document Title: Prestige in Numbers – How Test Scores and Choices Reveal School Rankings]
        “Unlike traditional rankings based on institutional data or expert surveys (such as USNWR), our method uses GMAT score reports and the schools students send them to, making the rankings resistant to manipulation. The ‘m-measure’ ranks schools based on how application frequency changes with score; the ‘tournament’ method scores schools based on head-to-head comparisons in candidate preferences.”
	- Question:
        Explain how the m-measure and tournament methods use test score data to produce school rankings. Why are these methods considered less susceptible to manipulation than traditional expert-based rankings?