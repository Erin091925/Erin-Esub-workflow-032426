
Technical Specification — FDA 510(k) Review Studio v3.0
“Regulatory Command Center: Nordic WOW — Pantone Edition”
Document Version: 3.0
Date: Tuesday, March 24, 2026
Timezone Context: Asia/Taipei
Deployment Target: Hugging Face Spaces (Streamlit, single container)
Supported LLM Providers: Gemini API, OpenAI API, Anthropic API, Grok API
Primary Goal: Deliver an agentic, human-in-the-loop workspace that accelerates FDA-style 510(k) reviews. Version 3.0 preserves all legacy multi-document ingestion, OCR, and WOW AI features while introducing a groundbreaking 4-Step Intelligent Review Generation Pipeline. This pipeline features automated FDA database searching, guidance-driven instruction generation, submission reorganization, and comprehensive final report synthesis. Furthermore, v3.0 introduces a highly granular LLM Settings Matrix and a refined "Nordic WOW" UI featuring 10 curated Pantone color palettes.
1. Executive Summary
The FDA 510(k) Review Studio v3.0 represents a paradigm shift in regulatory technology. Building upon the robust document ingestion and multi-agent orchestration of v2.7, this major release introduces a dedicated, sequential 4-Step Intelligent Review Generation Pipeline. This new workflow is specifically designed to mirror the cognitive process of a lead FDA reviewer, transforming raw device descriptions, guidance documents, and submission summaries into a finalized, audit-ready 3000–4000 word review report.
To ensure absolute reviewer control, v3.0 introduces a comprehensive Settings Matrix, allowing users to independently configure the LLM provider, specific model, and system prompt for every single feature within the application.
Visually, the application has been upgraded to the "Nordic WOW - Pantone Edition." The UI retains its minimalist, high-legibility architectural surfaces but replaces the previous painter styles with 10 meticulously selected Pantone color palettes, offering a sophisticated, accessible, and visually stunning environment that supports both English and Traditional Chinese (zh-TW) localizations.
2. Design Goals and Non-Goals
2.1 Primary Goals
Preserve Core Functionality: Maintain 100% feature parity with v2.7, including multi-PDF ingestion, LLM OCR, agents.yaml orchestration, and the 5 WOW AI modules.
Implement the 4-Step Review Pipeline:
Device Info to FDA Intelligence Summary (2000–3000 words).
Guidance to Review Instructions with checklists and 3 tables (2000–3000 words).
Submission Summary Reorganization based on generated instructions.
Final Comprehensive Review Report generation (3000–4000 words).
Granular LLM Control: Provide a dedicated settings interface where users can modify prompts and select models for each distinct LLM feature independently.
Nordic WOW Pantone UI: Implement a dual-theme (Light/Dark), dual-language (English/Traditional Chinese) interface with 10 distinct Pantone-based styling options.
Human-in-the-Loop Editing: Ensure every generated artifact in the new pipeline is presented in a dual-pane (Markdown/Text) editor, allowing manual modification before proceeding to the next step, complete with document download capabilities.
2.2 Non-Goals
No Automated Submissions: The system generates review artifacts for human reviewers; it does not interface with the FDA eSTAR system for automated submission.
No Code Generation: This specification outlines the architecture and functional requirements without providing executable Python or Streamlit code.
No Persistent Cloud Database: To maintain strict data privacy, the baseline deployment relies entirely on ephemeral session state. All data is purged upon session termination unless explicitly downloaded by the user.
3. System Architecture Overview
The application is structured as a modular, single-container Streamlit application, divided into six logical layers.
3.1 UI/UX Layer (Nordic WOW Pantone Edition)
Architectural Surfaces: Matte cards, subtle borders, and strong typographic hierarchy designed to reduce cognitive load during extensive reading sessions.
Global Controls: Light/Dark theme toggle, English/Traditional Chinese localization toggle, and the 10-style Pantone color palette selector.
Dual-View Editors: Every major text artifact utilizes a split-view component featuring a raw text editor on one side and a rendered Markdown view on the other.
3.2 Ingestion & Extraction Layer (Legacy Retained)
Multi-file drag-and-drop upload.
File queue selection with per-file trimming overrides.
Advanced OCR Matrix (Python Pack OCR and Gemini Multimodal LLM OCR) with consolidated Markdown assembly and stable traceability anchors.
3.3 The 4-Step Intelligent Review Pipeline Layer (NEW)
A sequential state machine guiding the user through Device Context, Guidance Analysis, Submission Reorganization, and Final Report Synthesis.
Integrated web-search capabilities for real-time FDA database querying.
Strict word-count targeting and structural enforcement (e.g., mandatory tables and checklists).
3.4 Orchestration & Intelligence Layer (Legacy Retained)
agents.yaml orchestration for custom, sequential agent execution.
Dynamic Skill Execution for ad-hoc analytical frameworks.
3.5 WOW AI Module Suite (Legacy Retained)
Five specialized modules: Evidence Mapper, Consistency Guardian, Regulatory Risk Radar, RTA Gatekeeper, and Labeling & Claims Inspector.
3.6 Configuration & Observability Layer (UPDATED)
Granular Settings Matrix: A new centralized hub for mapping specific LLMs and prompts to specific application features.
Dashboards: Mission Control, Timeline/DAG, Logs, and Regulatory Intelligence Board.
4. Nordic Architecture WOW UI/UX Specification
4.1 The Pantone Color System
The previous "painter accents" have been replaced by a highly curated selection of 10 Pantone color palettes. These colors are applied sparingly to primary buttons, active tabs, chart highlights, and focus borders, ensuring the background surfaces remain neutral (white/off-white in Light mode, deep charcoal in Dark mode).
The 10 selectable Pantone styles are:
Classic Blue (Pantone 19-4052): Instills calm, confidence, and connection.
Peach Fuzz (Pantone 13-1023): Warm, tactile, and modern.
Very Peri (Pantone 17-3938): Dynamic periwinkle blue with a violet-red undertone.
Illuminating & Ultimate Gray (Pantone 13-0647 & 17-5104): A marriage of strength and optimism.
Living Coral (Pantone 16-1546): Vibrant, yet mellow and engaging.
Ultra Violet (Pantone 18-3838): Inventive, imaginative, and forward-thinking.
Greenery (Pantone 15-0343): Refreshing, revitalizing, and symbolic of new beginnings.
Marsala (Pantone 18-1438): Robust, earthy, and sophisticated.
Emerald (Pantone 17-5641): Lively, radiant, and lush.
Tangerine Tango (Pantone 17-1463): Spirited, magnetic, and high-visibility.
4.2 Global Personalization Controls
Theme Toggle: Instantly switches between Light and Dark modes. The system dynamically adjusts the contrast ratios of the selected Pantone accent to ensure WCAG 2.1 AA compliance in both modes.
Language Toggle: Switches all static UI elements, tooltips, and placeholder text between English and Traditional Chinese (zh-TW). Note: This does not translate the user's uploaded documents or the LLM outputs unless explicitly requested in the LLM prompt settings.
State Preservation: Switching themes, languages, or Pantone styles triggers a UI re-render but must not destroy the Streamlit session state. All text buffers, uploaded files, and generated artifacts remain intact.
4.3 Dual-View Editor Component
For every step in the new 4-Step Pipeline, the user is presented with a Dual-View Editor:
Left Pane (Edit Mode): A raw text/markdown textarea where the user can manually type, delete, or paste content.
Right Pane (Preview Mode): A live-rendered Markdown view that supports tables, checklists, bolding, and syntax highlighting.
Action Bar: Located below the editor, containing buttons to "Save Changes," "Download as .md," "Download as .txt," and "Proceed to Next Step."
5. Granular LLM Settings & Configuration Engine
To provide ultimate flexibility, v3.0 introduces a dedicated "Settings & Configuration" tab. This replaces hardcoded prompts and global model selections with a highly granular matrix.
5.1 The Configuration Matrix
The UI presents a data table or a series of expandable accordions for every distinct AI feature in the application.
Configurable Features Include:
Pipeline Step 1: FDA Intelligence Search & Summary
Pipeline Step 2: Guidance Review Instructions
Pipeline Step 3: Submission Reorganization
Pipeline Step 4: Final Comprehensive Review
OCR Matrix: LLM Multimodal Extraction
WOW AI 1: Evidence Mapper
WOW AI 2: Consistency Guardian
WOW AI 3: Regulatory Risk Radar
WOW AI 4: RTA Gatekeeper
WOW AI 5: Labeling & Claims Inspector
5.2 Per-Feature Controls
For each feature listed above, the user can configure:
Provider Dropdown: Select from OpenAI, Gemini, Anthropic, or Grok.
Model Dropdown: Dynamically populates based on the selected provider (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
System Prompt Textarea: A large, editable text box containing the default system instructions. Users can rewrite this entirely.
Temperature Slider: Range 0.0 to 1.0.
Max Tokens Input: Integer value to cap the output length.
5.3 Configuration Persistence
Users can download their entire Configuration Matrix as a settings.json or settings.yaml file.
Users can upload a previously saved settings file to instantly restore their preferred models and prompts across the entire application.
6. The 4-Step Intelligent Review Generation Pipeline
This is the flagship addition to v3.0. It is a sequential workspace designed to take a reviewer from initial device familiarization to a finalized, comprehensive review report.
6.1 Step 1: Device Context & FDA Intelligence Search
Objective: Establish a foundational understanding of the medical device by combining user-provided information with real-time FDA database intelligence, resulting in a 2000–3000 word comprehensive summary.
Workflow:
Input: The user pastes medical device information (e.g., intended use, device description, technological characteristics) into a text area. Supported formats are plain text and Markdown.
Agent Action (Search & Synthesize):
The designated LLM (configured in Settings) analyzes the pasted text to extract key identifiers (e.g., proposed product codes, regulation numbers, predicate device names).
The agent utilizes a web-search tool (or queries the embedded datasets) to find related FDA information, such as predicate 510(k) summaries, relevant classification databases, and known MAUDE adverse events related to the product code.
The agent synthesizes the pasted input and the search results.
Output Generation: The agent generates a comprehensive summary in Markdown.
Constraint: The output must be strictly between 2000 and 3000 words.
Content: Must include sections on Device Description, Intended Use, Technological Characteristics, Predicate Device Comparison, and a summary of FDA Database Findings (Recalls, Adverse Events for the product code).
User Interaction:
The result is displayed in the Dual-View Editor.
The user can manually edit the text, correct any hallucinations, or add notes.
The user can download the artifact as a .md or .txt file.
The user clicks "Commit and Proceed to Step 2."
6.2 Step 2: Guidance-Driven Review Instruction Generation
Objective: Translate dense FDA guidance documents into an actionable, structured review instruction manual tailored to the specific device, complete with checklists and data tables.
Workflow:
Input: The user provides the relevant FDA 510(k) review guidance document. This can be pasted as text/markdown or uploaded as a PDF (which is instantly processed by the background OCR matrix).
Agent Action (Instruction Formulation):
The LLM reads the guidance document.
It cross-references the guidance with the Device Summary generated in Step 1 (passed as context).
It formulates a step-by-step instruction guide for reviewing this specific type of submission.
Output Generation: The agent generates the review instructions in Markdown.
Constraint: The output must be strictly between 2000 and 3000 words.
Mandatory Elements:
A comprehensive Reviewer Checklist (using Markdown [ ] syntax) covering administrative, performance, and labeling requirements.
Exactly Three (3) Markdown Tables:
Table 1: Recommended Performance Testing (Columns: Test Type, Standard/Method, Acceptance Criteria, Reviewer Notes).
Table 2: Biocompatibility Endpoints (Columns: Tissue Contact Category, Required Endpoints, Justification for Omission).
Table 3: Labeling & IFU Requirements (Columns: Requirement Description, Guidance Reference, Location in Submission).
User Interaction:
Displayed in the Dual-View Editor.
The user can modify the checklist, adjust table columns, or refine the instructions.
The user can download the artifact.
The user clicks "Commit and Proceed to Step 3."
6.3 Step 3: Submission Summary Reorganization
Objective: Take the sponsor's raw, often disorganized 510(k) submission summary and restructure it so that it perfectly aligns with the review instructions and checklists generated in Step 2.
Workflow:
Input: The user pastes the sponsor's 510(k) submission summary (text or markdown).
Agent Action (Restructuring):
The LLM ingests the raw submission summary.
It loads the Review Instructions, Checklist, and Tables from Step 2 into its context window.
It maps the information from the sponsor's summary directly into the structure dictated by the Step 2 instructions. It fills out the tables where data is available and checks off checklist items that are addressed in the summary.
Output Generation: The agent generates the reorganized submission summary in Markdown.
Content: The output highlights gaps (e.g., "Sponsor did not provide data for Biocompatibility Endpoint X") and organizes the narrative to flow logically for the reviewer.
User Interaction:
Displayed in the Dual-View Editor.
The user can manually tweak the reorganized data, add reviewer comments, or fix mapping errors.
The user can download the artifact.
The user clicks "Commit and Proceed to Step 4."
6.4 Step 4: Final Comprehensive Review Report
Objective: Synthesize all previous steps and any final reviewer instructions into a massive, audit-ready, comprehensive 510(k) review report.
Workflow:
Input:
Automatic Context: The system automatically compiles the outputs of Step 1 (Device Summary), Step 2 (Instructions/Tables), and Step 3 (Reorganized Submission).
User Input: The user provides additional, optional instructions for the final report (e.g., "Focus heavily on the cybersecurity deficiencies," or "Format this according to the 2026 eSTAR review template").
Agent Action (Synthesis & Expansion):
The LLM processes the massive context payload.
It drafts a formal regulatory review report, adopting an authoritative, objective, and highly structured tone.
Output Generation: The agent generates the final report in Markdown.
Constraint: The output must be strictly between 3000 and 4000 words.
Content: Includes Executive Summary, Device Description, Predicate Comparison, Performance Testing Review (incorporating the tables from Step 2 and data from Step 3), Labeling Review, Deficiencies/Requests for Additional Information (AI), and a Final Recommendation.
User Interaction:
Displayed in the Dual-View Editor.
The user performs the final manual review and editing.
The user can download the final document as .md or .txt.
7. Legacy Core Systems (Retained & Integrated)
While the 4-Step Pipeline is the primary new feature, the robust infrastructure of v2.7 remains fully operational and supports the new pipeline.
7.1 Multi-Document Ingestion & Trimming
Users can still upload massive PDF appendices.
The File Queue UI allows for selecting specific files, overriding trim ranges (e.g., pages 1-5, 15-20), and preparing them for OCR.
Trimmed byte streams are held in volatile memory to ensure data security.
7.2 OCR Matrix
Python Pack OCR: Fast, local text extraction using PyPDF2 and Tesseract.
LLM OCR: Renders PDF pages to images and uses multimodal LLMs (e.g., Gemini) to extract text and reconstruct complex tables.
Outputs from the OCR matrix can be seamlessly injected into Step 1 or Step 3 of the new Intelligent Review Pipeline.
7.3 Agent Orchestration (agents.yaml)
For users who prefer custom workflows outside the 4-Step Pipeline, the agents.yaml orchestration remains.
Users can define custom agents, chain them sequentially, and pass outputs between them.
The YAML editor includes validation, standardization, and diff-view capabilities.
7.4 WOW AI Module Suite
The 5 WOW AI modules can be triggered at any time, analyzing the artifacts generated in the 4-Step Pipeline:
Evidence Mapper: Maps claims in the Final Report (Step 4) back to the raw OCR anchors.
Consistency Guardian: Checks for conflicting values between the Reorganized Submission (Step 3) and the Final Report (Step 4).
Regulatory Risk Radar: Scores the device based on the FDA Intelligence Summary (Step 1).
RTA Gatekeeper: Runs a Refuse-to-Accept heuristic against the Reorganized Submission (Step 3).
Labeling & Claims Inspector: Evaluates the labeling table generated in Step 2 against the sponsor's claims.
7.5 Embedded Datasets & Search
The system retains embedded DataFrames for 510(k), MDR/ADR, GUDID, and Recalls.
The rapidfuzz fuzzy search engine allows manual querying, which supplements the automated web-search performed in Step 1 of the new pipeline.
8. Dashboards and Observability
8.1 Mission Control Dashboard
Visualizes the state machine of the 4-Step Pipeline (e.g., Step 1: Complete, Step 2: Pending).
Displays provider telemetry (API call counts, latency, token usage).
Monitors Streamlit session memory footprint to prevent Out-Of-Memory (OOM) errors on Hugging Face Spaces.
8.2 Timeline / DAG (Directed Acyclic Graph)
A visual node-based graph showing the lineage of documents.
Example flow: Raw Device Info -> Step 1 Summary -> Step 2 Instructions -> Step 3 Reorganization -> Step 4 Final Report.
Clicking any node retrieves the exact Markdown artifact generated at that point in time.
8.3 Logs Board
Structured, filterable event logs.
Timestamps localized to Asia/Taipei.
Strict redaction protocols ensure no API keys or sensitive PHI/PII are written to the logs.
9. Security, Privacy, and API Key Handling
9.1 API Key Management
Environment Secrets: The system prioritizes keys stored in Hugging Face Secrets (e.g., OPENAI_API_KEY). If detected, the UI hides key input fields and displays "Managed by System."
Session Keys: If environment keys are absent, users must input keys via password-masked fields. These are stored strictly in Streamlit's ephemeral session_state.
9.2 The "Total Purge" Protocol
A highly visible "Danger Zone" button allows the user to execute a Total Purge.
This action instantly deletes all uploaded PDFs, OCR buffers, generated Markdown artifacts (Steps 1-4), session API keys, and logs.
The UI resets to its default state, preserving only the user's chosen Pantone theme and language preferences.
10. Error Handling and Reliability Contracts
10.1 Preflight Checks
Before executing any step in the 4-Step Pipeline, the system performs strict preflight checks:
Input Validation: Ensures the user has actually pasted text or uploaded a document.
Context Validation: For Step 3, ensures Step 2 has been completed and the artifact exists in session state.
Token Estimation: Calculates the approximate token count of the combined inputs. If it exceeds the selected model's context window, the execution is blocked, and the user is prompted to select a model with a larger context window or trim the input.
10.2 Word Count Enforcement
The LLM prompts for Steps 1, 2, and 4 include strict instructions regarding word counts (e.g., 2000-3000 words, 3000-4000 words).
If the generated output falls significantly short of the target, the system will display a warning chip in the UI (e.g., "Warning: Output is only 1200 words. Consider adjusting the prompt or selecting a more capable model").
11. Deployment Specification
11.1 Hugging Face Spaces Configuration
Framework: Streamlit.
Hardware: Minimum 16GB RAM recommended due to the heavy context windows required for the 4-Step Pipeline and LLM OCR.
Dependencies: requirements.txt for Python libraries (including rapidfuzz, PyPDF2, provider SDKs). packages.txt for system-level dependencies (poppler-utils, tesseract-ocr).
11.2 State Management Architecture
Because Streamlit reruns the entire script upon any UI interaction (like changing a Pantone color), all text buffers, pipeline artifacts, and configuration settings must be stored in st.session_state.
Callbacks must be used for all buttons to ensure state is updated before the script reruns, preventing data loss during theme switching.
12. Acceptance Criteria (Definition of Done)
UI/UX: The Nordic WOW interface renders correctly. The Light/Dark toggle and English/zh-TW toggle work flawlessly. All 10 Pantone color palettes apply correctly to accents without altering the neutral background surfaces. Changing themes does not clear text editors.
Settings Matrix: The user can select different LLM providers, models, and edit system prompts for Step 1, Step 2, Step 3, Step 4, and all WOW AI modules independently. Settings can be downloaded and uploaded.
Pipeline Step 1: User can paste device info. The agent successfully searches FDA context and generates a 2000-3000 word summary. The Dual-View editor allows modification and download.
Pipeline Step 2: User can provide guidance text/PDF. The agent generates 2000-3000 word instructions containing a checklist and exactly 3 formatted Markdown tables. The Dual-View editor allows modification and download.
Pipeline Step 3: User can paste a submission summary. The agent successfully reorganizes it based on Step 2's output. The Dual-View editor allows modification and download.
Pipeline Step 4: User can provide optional instructions. The agent synthesizes Steps 1-3 into a final 3000-4000 word comprehensive review report. The Dual-View editor allows modification and download.
Legacy Integration: Multi-PDF upload, OCR, agents.yaml, and WOW AI modules function exactly as they did in v2.7, accessible alongside the new pipeline.
Security: Total Purge successfully clears all session data. API keys are never logged.
Appendix — 20 Comprehensive Follow-up Questions
Regarding the FDA Intelligence Search in Step 1, should the agent utilize a live web-search API (like Tavily or Google Custom Search), or should it strictly query the embedded static datasets (510k, MDR, GUDID) to prevent hallucinated web results?
If a live web-search API is used, how should we handle API key provisioning for the search tool (environment variable vs. user session input)?
For the 2000-3000 word requirement in Step 1, if the user pastes very brief device information (e.g., 50 words), should the system reject the input, or should the LLM aggressively expand based on the product code?
In Step 2, the specification requires exactly 3 tables. If the provided guidance document does not contain relevant information for one of the tables (e.g., no biocompatibility requirements), should the LLM generate an empty table with a "Not Applicable" note, or omit the table entirely despite the strict instruction?
How should the system handle PDF guidance documents in Step 2 that exceed the token limit of the selected LLM even after OCR? Should we implement an automatic chunking and summarization step prior to instruction generation?
For Step 3 (Submission Reorganization), if the sponsor's summary completely fails to address an item in the Step 2 checklist, should the LLM automatically generate a "Deficiency Draft" for that specific item?
In Step 4, generating a cohesive 3000-4000 word document in a single LLM pass can sometimes lead to repetition or degradation of logic. Should we architect Step 4 to generate the report section-by-section iteratively?
Regarding the Granular LLM Settings Matrix, should we provide a "Reset to FDA Defaults" button that restores highly optimized, pre-engineered prompts for the 4-Step Pipeline?
If a user selects a model with a small context window (e.g., an older open-source model) for Step 4, how should the UI gracefully handle the inevitable context_length_exceeded error?
For the Pantone UI, should the 10 color palettes also dictate the syntax highlighting colors within the Markdown preview pane, or should syntax highlighting remain standardized for readability?
When switching between English and Traditional Chinese (zh-TW), should the system also append a translation instruction to the LLM System Prompts, forcing the generated artifacts to be output in the selected language?
In the Dual-View Editor, if a user makes manual edits in the raw text pane, how frequently should the Markdown preview pane re-render to balance responsiveness with Streamlit's rerun performance?
Should the downloaded Markdown files include YAML frontmatter containing metadata about the generation process (e.g., timestamp, model used, prompt version) for auditability?
For the Total Purge function, should we implement a "Soft Purge" that clears documents but retains the LLM Settings Matrix, and a "Hard Purge" that wipes absolutely everything?
How should the system handle concurrent execution if a user clicks "Proceed to Step 2" while the OCR matrix is still processing a background PDF upload?
Should the Timeline/DAG dashboard allow users to "rollback" the state of the application to a previous node (e.g., reverting Step 3 to a previous generation attempt)?
In Step 1, when synthesizing FDA database findings, should the LLM be forced to provide explicit citations (e.g., [MAUDE Report #12345]) linking back to the specific dataset rows?
If the user modifies the Markdown tables in Step 2 manually, does the system need to parse those manual edits back into a structured JSON format before passing them as context to Step 3, or is raw Markdown context sufficient for the LLM?
Should the application include an auto-save feature that periodically writes the session_state text buffers to the browser's localStorage (via a custom Streamlit component) to prevent data loss if the user accidentally refreshes the page?
For Hugging Face Spaces deployment, what is the acceptable timeout threshold for Step 4 generation, considering that producing 4000 words via an API like GPT-4o or Claude 3.5 Sonnet may take upwards of 60-90 seconds?
