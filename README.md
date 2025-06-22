# UniGRC

![image](https://github.com/user-attachments/assets/985ef739-5e2c-4430-bd42-071933dbf10f)

A tool built to assist users in compliance guidance. Currently UniGRC supports three frameworks **(ISO 27001, NIST CSF, CIS Controls)**.
After the questionnaire of any framework detailed summary and risk analysis is generated.
The best part is according to the compliance data generated a AI report is given to the users which consists of executive summary, risk analysis, compliance guidance etc.

# How to run??

**The model uses openrouter api key:**
So create a .env file to store the API_KEY and mongodb URI
```
OPENROUTER_API_KEY=your_api_key
MONGODB_URI=your_mongodb_uri
```
**Install node modules using npm install**
Go to backend/ and install required modules using
```
python -r requirement.txt
```
Design the mongodb database like this:
## 📊 UniGRC Database Structure

| Database Name | Collections         | Description                                    |
|---------------|---------------------|------------------------------------------------|
| `unigrc`      | `cis`               | Stores CIS control framework data             |
|               | `iso`               | Stores ISO 27001 control framework data       |
|               | `nist`              | Stores NIST Cybersecurity Framework (CSF) data |

# Run
**Frontend:**
```
npm run dev
```
**Backend:**
```
uvicorn trial:app --relaod
```
