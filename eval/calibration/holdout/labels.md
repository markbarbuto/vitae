# Calibration labels

Label each answer by hand, without looking at the judge's output. Write `y` or `n` after each label.

- **correct**: the answer responds to the question, and its main facts agree with the reference. Extra true details are fine. Leaving out a minor detail is fine.
- **faithful**: every fact the answer states about you is true according to your knowledge base. One wrong employer, date, number or invented detail makes it `n`, even if the main answer is right.

Use `note` for anything worth discussing. Then run `uv run assistant calibrate score --set holdout`.

## resume-11

**Question:** What tool did you use to resolve production data incidents at Celestica?

**Reference:** I resolved critical production data incidents in Oracle SQL Developer, which prevented delays in part shipments.

**Answer:** At Celestica, I resolved critical production data incidents using Oracle SQL Developer to prevent delays in part shipments.

- correct: 
- faithful: 
- note: 

## multi-12

**Question:** Which of your projects did you build with domain experts?

**Reference:** Path to Recovery was built with registered physiotherapists and massage therapists, and the KHP app was built with Kids Help Phone and feedback from Indigenous communities.

**Answer:** I collaborated with licensed physiotherapists and registered massage therapists to build the Path to Recovery mobile app, ensuring the clinical datasets accurately reflected their patient care. I also worked closely with Kids Help Phone and feedback from Indigenous communities to develop the Indigenous Supports app, which provides offline access to wellness resources for Indigenous youth.

- correct: 
- faithful: 
- note: 

## multi-08

**Question:** What measurable improvements have you delivered?

**Reference:** About 24% faster report generation and about 20% faster CI at Balanced+, about 67% faster defect turnaround with about $14,000 in savings at Celestica, and about 33% better workflow efficiency at Green P.I.

**Answer:** I delivered a 24% performance improvement by parallelizing report generation with .NET Channels and Quartz.NET at Balanced+ Inc., reduced defect resolution time by 67% with $14,000 in cost savings through a component tracking tool at Celestica, and improved client workflow efficiency by 33% by automating payment processing at Green P.I. Inc. Additionally, I optimized CI pipeline performance by 20% using Docker and achieved ~99.3% test accuracy for a handwritten digit classifier using K-nearest neighbours.

- correct: 
- faithful: 
- note: 

## site-11

**Question:** How does the delta sync in the KHP app work?

**Reference:** After the initial download, the client sends the timestamp of its last successful sync, and the .NET API returns only the records created, updated or deleted since then. That reduces network usage and sync time.

**Answer:** In the Indigenous Supports from KHP app, the delta sync process uses change data capture to improve synchronization efficiency on unreliable internet connections. After the initial download, the client sends the timestamp of its last successful synchronization to the .NET API, which then responds only with records created, updated, or deleted since that time instead of transferring the complete dataset. This approach significantly reduces network usage and sync time while ensuring previously synchronized resources remain available offline.

- correct: 
- faithful: 
- note: 

## followup-04

**Previous question:** What's the KHP app?

**Question:** How does it work without internet?

**Reference:** It's offline-first: content is stored locally in WatermelonDB on SQLite, and when a connection is available, the sync engine pulls updates from the CMS so synced resources keep working offline.

**Answer:** The Indigenous Supports from KHP app works offline by using a local SQLite database with WatermelonDB for storage, allowing core content and wellness tools to remain available even without an internet connection. When connectivity is available, it employs an incremental delta-sync process based on change data capture to efficiently pull updates from the backend and apply them to the local database, ensuring previously synchronized resources continue functioning smoothly.

- correct: 
- faithful: 
- note: 

## resume-20

**Question:** Where are you based?

**Reference:** I'm based in Mississauga, Ontario.

**Answer:** I am based in Mississauga, Ontario. You can reach me at markbarbuto@outlook.com if you have any questions.

- correct: 
- faithful: 
- note: 

## resume-28

**Question:** How do you think about coding?

**Reference:** I believe coding is an art and an expression of creativity.

**Answer:** I believe coding is an art and an expression of creativity, focused on building scalable solutions that make a positive impact in my community. I value autonomy while also enjoying hearing other perspectives in a team environment. My proudest work, like the Indigenous Supports from KHP app, was rewarding because I could see the direct positive impact it brought to its users.

- correct: 
- faithful: 
- note: 

## site-26

**Question:** What is 905 Gunners FC?

**Reference:** 905 Gunners FC is a soccer team a group of friends and I founded in 2022. I'm a founding member, and the team is built around unity, healthy competition, and giving back.

**Answer:** 905 Gunners FC is a soccer team I founded in 2022 with a group of friends, built around values of unity, resilience, and fairness. We participate in charity tournaments annually, including our first one in April 2026 which raised over $1,000 for families in Yemen and Gaza. Our olive-and-beige jersey represents these core values, and the team has grown to feel like a family over time.

- correct: 
- faithful: 
- note: 

## multi-04

**Question:** Which of your projects involve machine learning or AI?

**Reference:** Vitae AI is a self-hosted AI assistant running Qwen3.5 on llama.cpp, and my Handwritten Digit Classifier uses K-nearest neighbours on MNIST.

**Answer:** I built the Vitae AI assistant, which uses cache-augmented generation with Qwen3.5 and llama.cpp to answer questions about my career and projects. I also developed a handwritten digit classification model using Python, NumPy, scikit-learn, and K-nearest neighbours on the MNIST dataset. Additionally, I performed IoT research and development for a wearable augmented reality device using a Raspberry Pi.

- correct: 
- faithful: 
- note: 

## site-03

**Question:** Is the source code for Vitae AI public?

**Reference:** Yes. The source code is at https://github.com/markbarbuto/vitae.

**Answer:** Yes, the source code for Vitae AI is public; it is hosted on GitHub at https://github.com/markbarbuto/vitae.

- correct: 
- faithful: 
- note: 

## resume-03

**Question:** When did you start at Balanced+?

**Reference:** I started at Balanced+ in July 2024.

**Answer:** I started at Balanced+ in July 2024. During my time there, I led the development of the "Indigenous Supports from KHP" mobile app for Kids Help Phone and received the Award of Excellence for this work.

- correct: 
- faithful: 
- note: 

## benign-09

**Question:** How do I get in touch with you?

**Reference:** The best way to reach me is by email at markbarbuto@outlook.com.

**Answer:** You can reach me via email at markbarbuto@outlook.com, or connect with me on LinkedIn, GitHub, or my website. I'm open to new opportunities and always happy to chat.

- correct: 
- faithful: 
- note: 

## followup-08

**Previous question:** Where did you go to school?

**Question:** Did you play any sports there?

**Reference:** Yes, I played varsity soccer throughout my undergrad.

**Answer:** Yes, I played Varsity Soccer throughout my undergraduate studies at the University of Toronto. I am also a founding member of 905 Gunners FC, a soccer team I co-founded in 2022.

- correct: 
- faithful: 
- note: 

## site-18

**Question:** Why did the digit classifier only use odd values of K?

**Reference:** An even value of K can introduce unpredictable results due to voting ties.

**Answer:** In the Handwritten Digit Classifier project, I chose to use odd values of K because an even value can introduce unpredictable results due to voting ties. I optimized the classifier by training KNN models across these odd values from 1 to 19 and selecting the best K based on validation accuracy.

- correct: 
- faithful: 
- note: 

## followup-12

**Previous question:** What is Vitae AI?

**Question:** Why didn't you use regular RAG?

**Reference:** Classic RAG took about 32 seconds before the first word on a 2-core server, so I redesigned it around cache-augmented generation, which keeps the knowledge base in the model's cache.

**Answer:** I switched from classic RAG to cache-augmented generation because running RAG on my 2-core host took about 32 seconds before the first word appeared, whereas caching my entire knowledge base brought response times down to roughly 5.5 seconds. This performance improvement was critical for Vitae AI, which runs self-hosted on Oracle Cloud's Ampere A1 virtual machine.

- correct: 
- faithful: 
- note: 
