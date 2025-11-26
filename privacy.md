# LifeContext Privacy Policy

**Last Updated / 最后更新**: 2025-11-25

---

## English Version

### 1. Introduction

LifeContext ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how our browser extension collects, uses, stores, and protects your information when you use LifeContext.

### 2. Data Collection

LifeContext collects the following types of data to provide its core functionality:

#### 2.1 Browsing Data
- **Page Titles**: The title of web pages you visit
- **URLs**: The web addresses of pages you visit
- **Page Content**: Text content extracted from web pages you browse
- **Screenshots** (Optional): Screenshots you choose to capture and upload

#### 2.2 User Preferences and Settings
- **Language Preferences**: Your preferred language settings
- **Timezone**: Your timezone preference
- **URL Blacklist**: Domains you choose to exclude from data collection
- **Extension Settings**: Your configuration preferences for the extension

#### 2.3 Interaction Data
- **Chat Conversations**: Conversations you have with the AI assistant
- **Generated Content**: AI-generated tips, todos, activities, and daily feeds
- **User Actions**: Your interactions with generated content (e.g., completing todos, dismissing tips)

### 3. How We Use Your Data

#### 3.1 Core Functionality
- **Content Analysis**: We use third-party Large Language Model (LLM) APIs to analyze your browsing content and generate insights, summaries, and recommendations
- **Vector Storage**: We use third-party Embedding APIs to convert your browsing content into vector representations, which are stored locally in your vector database for semantic search and context retrieval
- **AI Assistant**: Your browsing history and chat conversations are used to provide contextual responses through our AI assistant
- **Proactive Recommendations**: Based on your browsing patterns, we generate personalized tips, todo suggestions, activity summaries, and daily feeds

#### 3.2 Data Processing
- All data processing occurs locally on your device or through third-party AI services that you configure
- We do not send your data to our own servers
- All data is stored locally on your computer

### 4. Data Storage

#### 4.1 Local Storage
- **SQLite Database**: Your browsing records, settings, and generated content are stored in a local SQLite database on your computer
- **ChromaDB Vector Database**: Vector embeddings of your content are stored locally in ChromaDB on your computer
- **Browser Storage**: Extension settings and preferences are stored using Chrome's storage API (chrome.storage)

#### 4.2 Data Location
- All data is stored exclusively on your local device
- No data is transmitted to remote servers operated by us
- Data is only sent to third-party AI service providers (LLM and Embedding APIs) that you configure, and only for processing purposes

### 5. Third-Party Services

#### 5.1 AI Service Providers
LifeContext uses third-party AI services that you configure:
- **LLM APIs**: For content analysis, conversation, and content generation
- **Embedding APIs**: For converting text content into vector embeddings

#### 5.2 Third-Party Data Sharing
- Your browsing content may be sent to third-party LLM and Embedding API providers that you configure (e.g., OpenAI, Anthropic, or other compatible API providers)
- We do not control these third-party services' privacy practices
- We recommend reviewing the privacy policies of any third-party AI service providers you choose to use
- You are responsible for configuring and managing your own API keys for these services

#### 5.3 No Data Sharing with Us
- We do not collect, receive, or store your data on our servers
- We do not sell, rent, or share your data with any third parties except as necessary for the AI processing services you configure
- We do not use your data for advertising or marketing purposes

### 6. Permissions Used

LifeContext requests the following Chrome extension permissions:

- **`scripting`**: To inject content scripts for page content extraction
- **`activeTab`**: To access the current active tab's content
- **`storage`**: To store extension settings and preferences locally
- **`notifications`**: To display browser notifications for tips, todos, and other alerts
- **`alarms`**: To schedule periodic tasks (e.g., generating daily reports)

**Host Permissions**: 
- Only `http://localhost:3000/*` and `http://localhost:8000/*` - These are used to communicate with your local backend server, which runs on your computer

### 7. Your Rights and Controls

#### 7.1 Data Control
- **Disable Collection**: You can disable data collection at any time through the extension settings
- **URL Blacklist**: You can add specific domains to a blacklist to exclude them from data collection
- **Delete Data**: You can delete individual browsing records or all data through the extension interface
- **Uninstall**: Uninstalling the extension removes all stored data from Chrome's storage (local SQLite and ChromaDB databases remain on your computer until manually deleted)

#### 7.2 Access and Export
- You can view all your browsing records through the Timeline feature
- You can export your data through the extension interface

### 8. Data Security

- All data is stored locally on your device
- We use Chrome's built-in security features for data storage
- You are responsible for securing your local database files and API keys
- We recommend using strong, unique API keys for third-party AI services

### 9. Children's Privacy

LifeContext is not intended for children under the age of 13. We do not knowingly collect personal information from children under 13.

### 10. Changes to This Privacy Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.

### 11. Contact Us

If you have any questions about this Privacy Policy, please contact us through:
- GitHub Issues: [https://github.com/LifeContext/lifecontext/issues](https://github.com/LifeContext/lifecontext/issues)
- Project Repository: [https://github.com/LifeContext/lifecontext](https://github.com/LifeContext/lifecontext)


**Note / 注意**: This extension requires a local backend server to function. All data processing and storage occur on your local device. You are responsible for configuring third-party AI services and managing your API keys securely.

