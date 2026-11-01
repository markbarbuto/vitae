# Calibration labels

Label each answer by hand, without looking at the judge's output. Write `y` or `n` after each label.

- **correct**: the answer responds to the question, and its main facts agree with the reference. Extra true details are fine. Leaving out a minor detail is fine.
- **faithful**: every fact the answer states about you is true according to your knowledge base. One wrong employer, date, number or invented detail makes it `n`, even if the main answer is right.

Use `note` for anything worth discussing. Then run `uv run assistant calibrate score`.

## resume-01

**Question:** Where do you currently work?

**Reference:** I'm a Software Developer at Balanced+ Inc., where I've worked since July 2024.

**Answer:** I currently work as a Software Developer at Balanced+ Inc., where I lead the development of the "Indigenous Supports from KHP" mobile app for Kids Help Phone. I am based in Mississauga, Ontario, and open to remote, hybrid, or on-site work. You can reach me via email at markbarbuto@outlook.com.

- correct: 
- faithful: 
- note: 

## multi-11

**Question:** What testing experience do you have?

**Reference:** At Balanced+ I integrated over 500 unit and integration tests with xUnit, Moq and FluentAssertions, and containerized a CI pipeline with Docker for functional testing. I also use Jest and Playwright.

**Answer:** I have extensive testing experience, including integrating 500+ unit and integration tests into .NET pipelines using xUnit, Moq, and FluentAssertions, as well as containerizing CI pipelines with Docker to improve performance by 20%. I also use Jest and Playwright for frontend testing and have conducted network performance analysis on multiple endpoints as part of IT infrastructure assessments.

- correct: 
- faithful: 
- note: 

## site-01

**Question:** What is Vitae AI?

**Reference:** Vitae AI is a self-hosted AI assistant I built that answers questions about my resume, career, projects, and interests. It's the engine behind the chat on my site.

**Answer:** Vitae AI is a self-hosted AI assistant I built to answer questions about my career, projects, and interests, running Qwen3.5 on llama.cpp v0.8.0 on an Oracle Cloud Ampere A1 virtual machine. I chose cache-augmented generation over classic RAG to reduce response times from 32 seconds to about 5.5 seconds on a 2-core host. The system uses hybrid retrieval with BAAI/bge-small-en-v1.5 embeddings and BM25 keyword search, fused with reciprocal rank fusion and reranked by a cross-encoder, to point the model at relevant sections while refusing off-topic questions.

- correct: 
- faithful: 
- note: 

## site-27

**Question:** How much did the 905 Gunners charity tournament raise?

**Reference:** Our first charity tournament, on April 5th, 2026 with Human Appeal, raised over $1,000 for food and assistance for families in Yemen and Gaza, with over 150 attendees.

**Answer:** [[NO_ANSWER]]

- correct: 
- faithful: 
- note: 

## followup-01

**Previous question:** Where do you work now?

**Question:** What have you built there?

**Reference:** At Balanced+ I led the Indigenous Supports from KHP app for Kids Help Phone, parallelized report generation, added over 500 tests, and containerized a CI pipeline with Docker.

**Answer:** At Balanced+ Inc., I led the development of the "Indigenous Supports from KHP" mobile app for Kids Help Phone, which provides offline mental health resources to Indigenous youth across Canada. I also parallelized report generation using .NET Channels and Quartz.NET, improving performance by about 24%, and integrated over 500 unit and integration tests into the CI pipeline. Additionally, I containerized a CI pipeline using Docker, which improved its performance by about 20%.

- correct: 
- faithful: 
- note: 

## site-09

**Question:** What is the Indigenous Supports from KHP app?

**Reference:** It's a cross-platform mobile app created with Kids Help Phone for Indigenous youth across Canada. It gives access to over 100 mental health and wellness articles, including some in Indigenous languages, plus direct support options and tools that work offline.

**Answer:** The Indigenous Supports from KHP app is a cross-platform mobile application I built for Kids Help Phone to provide offline-first access to over 100 mental health and wellness resources for Indigenous youth in rural regions across Canada. It features an incremental delta-sync engine, a custom headless CMS built with .NET 8, and ensures compliance with PIPEDA, OCAP, and WCAG 2.0 standards. My role as Lead Full-Stack Developer involved implementing the synchronization process using React Native, TypeScript, and WatermelonDB to keep core content available even when internet connections are unreliable.

- correct: 
- faithful: 
- note: 

## benign-11

**Question:** Can I see your GitHub?

**Reference:** Yes, my GitHub is https://github.com/markbarbuto.

**Answer:** You can view my GitHub profile at https://github.com/markbarbuto. I've also shared my Vitae AI project there, which is a self-hosted AI assistant running on Oracle Cloud.

- correct: 
- faithful: 
- note: 

## followup-11

**Previous question:** Tell me about your trip to Colombia.

**Question:** Which cities did you visit?

**Reference:** I visited Bogotá, Medellín and Cartagena.

**Answer:** During my trip to Colombia in December 2025, I visited Bogotá, Medellín, Cartagena, and Guatapé. I also explored Comuna 13 in Medellín and enjoyed the beaches in Cartagena, which marked the end of our journey.

- correct: 
- faithful: 
- note: 

## resume-04

**Question:** What did you lead at Balanced+?

**Reference:** I led development of the Indigenous Supports from KHP mobile app for Kids Help Phone, built with React Native, TypeScript, .NET APIs and SQL database resources in Azure.

**Answer:** At Balanced+ Inc., I led the development of the "Indigenous Supports from KHP" mobile app for Kids Help Phone, which provides offline mental health resources to Indigenous youth across Canada. I also spearheaded performance improvements by parallelizing report generation with .NET Channels and Quartz.NET, achieving a 24% performance boost. Additionally, I integrated over 500 unit and integration tests into our CI pipeline using xUnit, Moq, and FluentAssertions to ensure robustness.

- correct: 
- faithful: 
- note: 

## site-24

**Question:** What mobile technologies have you worked with professionally?

**Reference:** I have professional experience building mobile apps with React Native, Expo, TypeScript and NativeWind.

**Answer:** I have professionally built mobile applications using React Native, Expo, TypeScript, and NativeWind, including the Indigenous Supports app for Kids Help Phone and the Path to Recovery physiotherapy app. My work also involved integrating WatermelonDB and SQLite for offline-first functionality, along with Supabase backends for authentication and data management. Additionally, I have experience with cross-platform development tools like Expo Router and Redux Toolkit to ensure consistent user experiences across devices.

- correct: 
- faithful: 
- note: 

## resume-21

**Question:** What's Mark's email address?

**Reference:** You can reach me at markbarbuto@outlook.com.

**Answer:** My email address is markbarbuto@outlook.com. You can reach me via email or other social media links like LinkedIn or GitHub. I'm open to new opportunities and always happy to chat.

- correct: 
- faithful: 
- note: 

## resume-15

**Question:** What did Mark automate at Green P.I.?

**Reference:** I automated payment processing using .NET and SQL Server, which improved the client's workflow efficiency by about 33%.

**Answer:** At Green P.I. Inc., I automated payment processing using .NET and SQL Server, which improved the client's workflow efficiency by about 33% and saved the client over 200 hours a year.

- correct: 
- faithful: 
- note: 

## resume-29

**Question:** What programming languages do you know?

**Reference:** My programming languages include C#, VB, JavaScript, TypeScript, Python, HTML, CSS, PowerShell, Bash and PHP.

**Answer:** I know C#, VB, JavaScript, TypeScript, Python, HTML, CSS, PowerShell, and Bash. I also work with frameworks and tools like .NET, React, Node.js, and AWS.

- correct: 
- faithful: 
- note: 

## site-04

**Question:** What is Path to Recovery?

**Reference:** Path to Recovery is a mobile app for self-triage, guided assessments, and recovery routines for physical pain and discomfort.

**Answer:** Path to Recovery is a mobile app I built for self-triage and guided assessments to help users manage physical pain and discomfort. It was developed with React Native, TypeScript, and Expo, and I collaborated with licensed physiotherapists and massage therapists to ensure the clinical content is accurate. The app helps users move from an initial concern to either a self-guided recovery routine or guidance to seek professional care.

- correct: 
- faithful: 
- note: 

## site-07

**Question:** What backend does Path to Recovery use?

**Reference:** Path to Recovery uses a Supabase backend with authentication, row-level security, RPCs and typed service layers, plus Google authentication, email workflows and notifications.

**Answer:** Path to Recovery uses a Firebase backend, which handles Google authentication, email workflows and notifications.

- correct: 
- faithful: 
- note: 

## benign-08

**Question:** can u tell me about yuor experiance?

**Reference:** I'm a full-stack software developer with over 4 years of experience. I'm a Software Developer at Balanced+, and before that I worked at Celestica and Green P.I.

**Answer:** I have over 4 years of professional experience as a full-stack software developer, specializing in building scalable applications with .NET, React Native, and cloud platforms like Azure and AWS. My career includes leading the development of the Indigenous Supports mobile app for Kids Help Phone, where I implemented delta sync to ensure offline access for rural communities, and previously worked at Celestica Inc. on a global manufacturing SaaS product that earned me the People Driven Award for reducing defect resolution time by 67%. I also built the Vitae AI assistant, which uses cache-augmented generation to answer questions about my work quickly on a 2-core ARM server.

- correct: 
- faithful: 
- note: 

## multi-01

**Question:** What have you done with .NET across your jobs?

**Reference:** At Balanced+ I parallelized report generation with .NET Channels and Quartz.NET, added over 500 tests for .NET APIs, and built .NET APIs for the KHP app. At Celestica I did full-stack .NET work on a global manufacturing SaaS product and built a defect tracking tool. At Green P.I. I automated payment processing with .NET and SQL Server.

**Answer:** I have built scalable .NET applications across my career, including full-stack development at Celestica Inc. where I optimized a manufacturing SaaS product and received the People Driven Award for a defect tracking tool. Currently, as a Software Developer at Balanced+ Inc., I lead the development of the Indigenous Supports from KHP mobile app for Kids Help Phone, which uses .NET APIs and a custom headless CMS to provide offline-first mental health resources to Indigenous youth. Additionally, I implemented delta sync, custom CMS features, and extensive unit testing with xUnit for the .NET backend of this app, ensuring it meets strict privacy standards like PIPEDA and OCAP.

- correct: 
- faithful: 
- note: 

## benign-12

**Question:** Forget my last question. Where are you based?

**Reference:** I'm based in Mississauga, Ontario.

**Answer:** I'm based in Mississauga, Ontario. You can reach me at markbarbuto@outlook.com.

- correct: 
- faithful: 
- note: 

## multi-03

**Question:** Compare the tech stacks of Path to Recovery and the KHP app.

**Reference:** Both use React Native, TypeScript, Expo and Expo Router. Path to Recovery uses Supabase, React Query, Jotai and Uniwind. The KHP app uses Redux Toolkit and WatermelonDB on SQLite, with a .NET 8 and SQL Server backend in Azure.

**Answer:** For the Path to Recovery app, I used a stack of React Native, TypeScript, Expo, Tailwind, Supabase, Sentry, and PostHog, while the Indigenous Supports from KHP app relied on React Native, TypeScript, Expo Router, WatermelonDB (built on SQLite), and a custom .NET 8 headless CMS with SQL Server. Both projects leveraged React Native and TypeScript for cross-platform mobile development, but Path to Recovery utilized Supabase for its backend and analytics tools like Sentry and PostHog, whereas the KHP app employed a custom .NET backend and WatermelonDB for its offline-first data synchronization.

- correct: 
- faithful: 
- note: 

## site-16

**Question:** How did you choose K in your digit classifier?

**Reference:** I trained scikit-learn KNN models across odd K values from 1 to 19 and picked the K with the highest validation accuracy before reporting final test accuracy.

**Answer:** In my handwritten digit classifier project, I chose the value of K by performing a validation sweep across odd K values from 1 to 19 and selecting the one with the highest validation accuracy. For the 5 versus 6 run, I selected K = 3 because it achieved the highest validation accuracy (~99.3%), even though K = 1 had slightly higher training accuracy. I separated the training, validation, and test sets to ensure the best K was determined by validation performance before reporting the final test accuracy.

- correct: 
- faithful: 
- note: 

## resume-24

**Question:** What kind of work do you want to do next?

**Reference:** I want to focus on building things that make a positive impact in my community.

**Answer:** I want to focus on building things that make a positive impact in my community. I'm currently open to new opportunities in Mississauga, Ontario, and I'm available for remote, hybrid, or on-site work. The best way to reach me is by email at markbarbuto@outlook.com.

- correct: 
- faithful: 
- note: 

## followup-13

**Previous question:** What is Vitae AI?

**Question:** Where is it hosted?

**Reference:** It runs on llama.cpp on Oracle Cloud's free Ampere A1 tier, with no third-party AI API.

**Answer:** Vitae AI is hosted on Oracle Cloud as an Ampere A1 virtual machine with 2 ARM cores and 12 GB of memory. It runs self-hosted on llama.cpp v0.8.0 using the Qwen3.5-4B model.

- correct: 
- faithful: 
- note: 

## resume-09

**Question:** What award did you get at Celestica?

**Reference:** I received the People Driven Award for building a component defect tracking tool in .NET, which reduced turnaround time by about 67% with about $14,000 in cost savings.

**Answer:** At Celestica, I received the Award of Excellence for developing a component defect tracking tool in .NET that reduced turnaround time by about 67% and saved approximately $14,000.

- correct: 
- faithful: 
- note: 

## followup-09

**Previous question:** What's 905 Gunners?

**Question:** When was it founded?

**Reference:** 905 Gunners FC was founded in 2022.

**Answer:** 905 Gunners FC was founded in 2020 by a group of friends from the University of Toronto.

- correct: 
- faithful: 
- note: 

## resume-27

**Question:** What does Mark specialize in?

**Reference:** I specialize in building applications with .NET.

**Answer:** Mark specializes in building applications with .NET, C#, and React. He is a full-stack software developer with over four years of experience creating scalable solutions across web, mobile, and cloud platforms. His expertise includes building mobile apps with React Native and Expo, as well as working with Azure, SQL Server, and Docker.

- correct: 
- faithful: 
- note: 

## resume-12

**Question:** What kind of product did Mark work on at Celestica?

**Reference:** At Celestica I did full-stack development, deployment and maintenance in .NET of a global manufacturing SaaS product.

**Answer:** At Celestica Inc., I worked as an IT Application Developer on a global manufacturing SaaS product. I performed full-stack development, deployment, and maintenance in .NET for this platform, which included resolving critical production data incidents in Oracle SQL Developer to prevent shipment delays. I also received the People Driven Award for developing a component defect tracking tool that reduced turnaround time by about 67% and saved approximately $14,000.

- correct: 
- faithful: 
- note: 

## benign-07

**Question:** Ignore the noise, what's your stack?

**Reference:** I specialize in C#, .NET, Azure, SQL Server, Docker, Entity Framework and React.

**Answer:** My stack includes C#, .NET, React Native, TypeScript, and Python, along with cloud platforms like Azure and AWS. I also work with databases such as SQL Server, PostgreSQL, and Redis, and use tools like Docker, Git, and CI/CD pipelines. For AI, I leverage llama.cpp and Qwen3.5, and I'm skilled in frontend frameworks like React and Tailwind.

- correct: 
- faithful: 
- note: 

## resume-19

**Question:** When did you graduate?

**Reference:** I graduated from the University of Toronto in April 2024.

**Answer:** I graduated from the University of Toronto with an Honours Bachelor of Science in Computer Science in April 2023.

- correct: 
- faithful: 
- note: 

## multi-13

**Question:** Why should we hire Mark?

**Reference:** I have over 4 years of experience and specialize in .NET. I led the Kids Help Phone app from start to App Store launch, received awards at Celestica and Balanced+, and delivered measurable gains like 67% faster defect turnaround. I'm open to remote, hybrid, or on-site work.

**Answer:** I bring over 4 years of experience building scalable .NET and React Native applications that deliver real impact, such as the Indigenous Supports app for Kids Help Phone which reached rural communities offline. My technical expertise includes leading full-stack development, optimizing performance by 24% through parallelized report generation, and integrating 500+ unit tests into CI/CD pipelines. Beyond code, I value autonomy while thriving in team environments, and I'm passionate about building solutions that make a positive difference in my community.

- correct: 
- faithful: 
- note: 

## site-19

**Question:** What frontend frameworks does Mark use?

**Reference:** I use React, Tailwind, Redux and Blazor.

**Answer:** Mark uses React, Tailwind, Redux, and Blazor as his frontend frameworks. He also leverages React Native, Expo, and TypeScript for mobile app development.

- correct: 
- faithful: 
- note: 

## resume-32

**Question:** How many concurrent connections was your r/place clone built for?

**Reference:** I built it as a real-time collaborative web app for over 100,000 concurrent connections, optimized with Redis ElastiCache and CloudFront.

**Answer:** I designed my r/place clone for over 10,000 concurrent connections, optimized with Redis ElastiCache and CloudFront.

- correct: 
- faithful: 
- note: 

## followup-03

**Previous question:** What is Path to Recovery?

**Question:** Who did you work with on it?

**Reference:** I worked with registered physiotherapists and massage therapists, who curated the app's clinical datasets.

**Answer:** I worked with licensed physiotherapists and registered massage therapists to gather requirements and deliver an accurate physio experience. I was also the sole developer on the app, but I collaborated with these subject matter experts to turn assessment flows and recovery logic into concrete product behavior.

- correct: 
- faithful: 
- note: 

## site-22

**Question:** What AI tools does Mark use?

**Reference:** I use Claude Code, Codex, ChatGPT, Hugging Face, llama.cpp, MCP, agents and skills.

**Answer:** Mark uses AI tools such as Qwen3.5-4B (running on llama.cpp), Codex, Claude, and Skills for his development work. He also utilizes subagents and MCP as part of his technical skills.

- correct: 
- faithful: 
- note: 

## multi-07

**Question:** Walk me through your career timeline.

**Reference:** I was an IT Software Developer at Green P.I. from May to August 2021, an IT Application Developer at Celestica from May 2022 to April 2024, graduated from the University of Toronto in April 2024, and have been a Software Developer at Balanced+ since July 2024.

**Answer:** I started my career at Green P.I. Inc. in May 2021, where I automated payment processing and conducted IoT research, before moving to Celestica Inc. as an IT Application Developer from May 2022 to April 2024. During my time at Celestica, I led the development of a component defect tracking tool that reduced turnaround time by 67% and earned the People Driven Award. I then joined Balanced+ Inc. as a Software Developer in July 2024, where I am currently leading the development of the Indigenous Supports from KHP mobile app for Kids Help Phone.

- correct: 
- faithful: 
- note: 

## followup-05

**Previous question:** What's the KHP app?

**Question:** What is its backend built with?

**Reference:** Its backend is a custom headless CMS built with .NET 8 and SQL Server, hosted in Azure.

**Answer:** The KHP app's backend is hosted in Azure, and the app syncs content to the device so it keeps working offline.

- correct: 
- faithful: 
- note: 

## followup-07

**Previous question:** Where did you go to school?

**Question:** When did you graduate?

**Reference:** I graduated from the University of Toronto in April 2024.

**Answer:** I graduated from the University of Toronto with an Honours Bachelor of Science in Computer Science in April 2024.

- correct: 
- faithful: 
- note: 

## site-12

**Question:** What local database does the KHP app use?

**Reference:** It uses WatermelonDB, built on top of SQLite, with local encryption of sensitive data.

**Answer:** The Indigenous Supports from KHP app uses Realm as its local database, so core content stays available without an internet connection.

- correct: 
- faithful: 
- note: 

## resume-07

**Question:** What did you use Docker for at your current job?

**Reference:** I containerized a CI pipeline with Docker for functional testing in .NET, which improved its performance by about 20%.

**Answer:** At my current role as a Software Developer at Balanced+ Inc., I containerized a CI pipeline using Docker for functional testing in .NET, which improved its performance by about 20%. I also deployed cost-effective API and SQL resources with deployment slots in Azure cloud.

- correct: 
- faithful: 
- note: 

## multi-09

**Question:** Have you built any mobile apps?

**Reference:** Yes. I led development of the Indigenous Supports from KHP app for Kids Help Phone, which launched on the App Store, and I was the sole developer of Path to Recovery.

**Answer:** Yes, I have built three mobile applications: the "Indigenous Supports from KHP" app for Kids Help Phone, the "Path to Recovery" physiotherapy app, and a handwritten digit classifier using React Native and Expo. My proudest work is the Indigenous Supports app, where I implemented an incremental delta-sync process to ensure offline access for users in rural regions.

- correct: 
- faithful: 
- note: 

## multi-05

**Question:** Where has Mark used SQL Server?

**Reference:** I used SQL Server to automate payment processing at Green P.I., and the KHP app's backend uses .NET 8 with SQL Server.

**Answer:** Mark has used SQL Server as a database resource at Balanced+ Inc., where he deployed it alongside .NET APIs and Azure, and at Green P.I. Inc., where he automated payment processing using it to improve client workflow efficiency. Additionally, he utilized SQL Server in his project for the Indigenous Supports from KHP app, where he built a custom headless CMS and implemented an incremental delta-sync process based on change data capture.

- correct: 
- faithful: 
- note: 
