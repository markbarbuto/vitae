---
source: portfolio/src/data/projects.ts
visibility: public
generated: true
---

# Projects

## Vitae AI (2026)

Self-Hosted AI. My role: Designer & Engineer.

A self-hosted AI assistant that answers questions about my resume, career, projects, and interests. It's the engine behind the chat at the top of this page.

Vitae AI is a self-hosted assistant that answers questions about my resume, career, projects, and interests in plain language. My first design was classic retrieval-augmented generation (RAG), but benchmarking it on a 2-core ARM server showed a 32-second wait before the first word. So I redesigned it around cache-augmented generation. The whole knowledge base is processed once and kept in the model's cache, so each question only adds a few dozen tokens. Hybrid search (embeddings plus keyword scoring, with a reranker) still runs on every question. It points the model at the most relevant sections, refuses off-topic questions without calling the model, and records which sources were used. The model runs on llama.cpp on Oracle Cloud's free Ampere A1 tier, with no third-party AI API.

Highlights:
- Cache-augmented generation: the whole knowledge base stays in the model's cache, so answers start in seconds on 2 CPU cores
- Hybrid retrieval (embeddings + BM25 + reranking) for focus hints, refusals, and sources
- Self-hosted Qwen3.5 on llama.cpp, running on Oracle Cloud's free Ampere A1 tier
- Jailbreak and off-topic guards, and an evaluation suite that scores faithfulness and refusals

Stack: Python, FastAPI, llama.cpp, Qwen3.5, Oracle Cloud.

- Source code: https://github.com/markbarbuto/vitae
- Status: coming soon

## Path to Recovery (2026)

Mobile App. My role: Software Engineer, Designer, Co-owner.

A physiotherapy-adjacent mobile app for self-triage, guided assessments, and recovery routines for physical pain and discomfort.

Path to Recovery is a mobile app for self-triage, guided assessments, and recovery routines for physical pain and discomfort. It helps users move from an initial concern to a clearer next step, whether that is a scheduled self-guided routine or guidance to seek professional care.

The project came from personal and peer conversations about the barriers that can make physiotherapy hard to access, including cost, anxiety, uncertainty, and delays in getting practical guidance for common injuries. The clinical datasets within the app are curated by registered physiotherapists and massage therapists, with an emphasis on translating what they actually do with patients into a clear app experience.

I was the sole developer on the app and worked with subject matter experts to turn assessment flows, recovery logic, and exercise guidance into concrete product behavior. The app is built with Expo Router and a Supabase backend, including support for Google authentication, email workflows, notifications, and typed service layers.

A major lesson from the project was learning how to use AI-assisted development tools effectively without losing ownership of the implementation. I used tools and workflows such as Codex, Claude Design, Skills, subagents, and MCP to accelerate parts of the build, while still guiding the architecture, business logic, and code decisions.

Highlights:
- Personalized onboarding and guided assessments with branching questions and tailored outcomes
- Self-guided recovery routines with active sessions, scheduling, and progress tracking
- Clinician-informed injury and recovery exercise datasets developed with registered PTs and RMTs
- Supabase backend with authentication, row-level security, RPCs, and typed service layers
- Support for cross-platform, dark mode, and internationalization

Stack: Expo, React Native, TypeScript, Expo Router, Supabase, React Query, Jotai, Uniwind, i18n.

- Source code: private
- Status: coming soon

## Indigenous Supports from KHP (2026)

Mobile App. My role: Lead Full-Stack Developer.

An offline-first app built for Kids Help Phone providing offline-first access to wellness resources for Indigenous youth in rural regions across Canada.

Indigenous Supports from KHP is a cross-platform mobile app created with Kids Help Phone for Indigenous youth across Canada. It provides access to over 100 mental health and wellness articles, including selected content in Indigenous languages, alongside direct support options and tools that can be used offline.

The app was built — in close collaboration with Kids Help Phone and feedback from Indigenous communities — in response to the limited availability of mental health and wellness resources in rural and remote communities, where internet access may be slow, intermittent, or unavailable. Its offline-first design keeps core content and personal wellness tools available on the device instead of requiring a continuous connection.

View the Kids Help Phone launch post on Instagram: https://www.instagram.com/p/DZdDxibEf-N/

Its main features include a browsable content library, My Wellness Bundle — a guided safety-plan questionnaire, direct access to Kids Help Phone support — calling, texting, or online messaging, and the Resources Around Me module — nearby and virtual support services across Canada.

The mobile application was built with React Native, TypeScript, Expo Router and WatermelonDB (built on top of SQLite). When an internet connection is available, its synchronization engine pulls updates from the content management system and applies them to the local database, allowing previously synchronized resources to continue working offline.

Since data privacy, anonymonity and accessibility are key considerations for Kids Help Phone, the app adheres to strict data protection standards and privacy regulations, including compliance with PIPEDA, OCAP, WCAG 2.0, and other applicable laws.

The supporting backend is a custom headless CMS built with .NET 8 and SQL Server, hosted in Azure using Azure App Services with deployment slots.

To make synchronization more efficient and reliable, I implemented an incremental delta-sync process based on change data capture. After the initial download, the client sends the timestamp of its last successful synchronization. The .NET API responds only with records created, updated, or deleted since that time instead of repeatedly transferring the complete dataset. This reduces network usage and synchronization time, which is important especiialy internet connection is unreliable.

Highlights:
- Anonymous, offline-first access to over 100 wellness articles, locally available safety plan, and direct support options
- Incremental delta sync using created, updated, and deleted change sets
- React Native, Expo Router, and Redux Toolkit for cross-platform mobile development
- WatermelonDB and SQLite storage with local encryption of sensitive data
- .NET 8, Azure Functions, and SQL Server backend hosted in Azure
- Developed with Kids Help Phone and feedback from Indigenous communities

Stack: React Native, TypeScript, Expo, Expo Router, Redux Toolkit, i18next, WatermelonDB, SQLite, NativeWind, Gluestack UI, Azure, Application Insights, .NET 8, Entity Framework Core, SQL Server, Azure Devops, Fastlane.

- View on the App Store: https://apps.apple.com/ca/app/indigenous-supports-from-khp/id6760955357
- Source code: private

## Handwritten Digit Classifier (2021)

Machine Learning. My role: Developer.

A Python K-nearest neighbours classifier for binary handwritten digit recognition on MNIST, with validation-driven K selection and accuracy plots.

Handwritten Digit Classifier is a project written with Python and machine learning libraries that uses K-nearest neighbours to classify pairs of handwritten digits from the MNIST dataset. KNN works by comparing a new input against labeled examples, finding the closest training samples, and assigning the class that appears most often among those neighbours.

Choosing the value of K is important because it controls how sensitive the classifier is to nearby examples. A small K can react strongly to noise or unusual samples, while a large K can smooth over useful local patterns. An even value of K can introduce unpredictable results due to voting ties. This project treats K as a value to optimize with validation data instead of hard-coding it.

The implementation includes a preprocessing step that builds reduced train, validation, and test sets for any two digits from 0 to 9. It then trains scikit-learn KNN models across odd K values from 1 to 19, compares training and validation accuracy, and selects the best K using validation performance before reporting final test accuracy.

A key takeaway from this project was the importance of separating training, validation, and test sets. The training set is used to fit the model, the validation set helps tune K for the highest accuracy during development, and the test set provides a final check of how well the classifier performs against new data.

On the accuracy graphs, the best value of K is the point where validation accuracy is highest, not necessarily where training accuracy is highest. In the  5 versus 6 run, K = 3 was selected because it had the highest validation accuracy (~99.3%), even though K = 1 had slightly higher training accuracy. In the 4 versus 7 run, K = 9 was selected because it had the highest validation accuracy (~99.7%).

Highlights:
- Binary classification of handwirtten MNIST digit pairs using K-nearest neighbours
- Validation sweep across odd K values from 1 to 19
- Best-K selection using validation accuracy before final test evaluation
- Accuracy visualizations for training and validation accuracy
- Reached ~99.3% test accuracy for 5 versus 6, and ~99.7% for 4 versus 7

Stack: Python, Jupyter Notebook, NumPy, scikit-learn, Matplotlib, MNIST, KNN.

- Source code: https://github.com/markbarbuto/KNN-Digit-Classifier
