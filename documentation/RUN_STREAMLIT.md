# 🚀 Running the Streamlit UI

## Quick Start

1. **Install Streamlit** (if not already installed):
   ```bash
   pip install streamlit
   ```

2. **Run the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Access the app**:
   - Browser will automatically open to `http://localhost:8501`
   - If not, navigate to that URL manually

## Features

### 📍 Cascading Filters (Sidebar)
- **Semester**: Select a semester (filters subjects and books)
- **Subject**: Select a subject (filters books)
- **Books**: Multi-select specific books (optional)
- **Clear All**: Reset all filters

Filters automatically cascade:
- Select semester → subjects update to show only those in that semester
- Select subject → books update to show only those in that subject/semester

### 💬 Chat Interface
- Ask questions in natural language
- Answers include page numbers and source citations
- Chat history maintained throughout session
- Clear chat history button

### 📊 Library Statistics
- View total semesters, subjects, and books in sidebar

## Usage Tips

1. **Start broad, then narrow down**:
   - Begin with "All" for everything
   - Select semester to focus on one term
   - Select subject to dive into specific topic
   - Select books if you want specific textbooks only

2. **Leave books empty** to search all books in the selected scope

3. **Clear filters** to search across all materials

## Example Workflow

```
1. Select: Semester = "Y3S2"
2. Select: Subject = "Time Series"
3. Ask: "What is autocorrelation?"
   → System searches only Y3S2 Time Series materials

4. Clear All Filters
5. Ask: "Compare autocorrelation across different subjects"
   → System searches all materials
```

## Troubleshooting

**"Vector store not found" error**:
- Run ingestion first: `python StudyRAGSystem.py` → Select option 1

**Filters not updating**:
- Try clicking "Clear All Filters" and reselecting

**Page not loading**:
- Check terminal for errors
- Ensure port 8501 is not in use
- Try: `streamlit run streamlit_app.py --server.port 8502`

## Keyboard Shortcuts

- `Ctrl + R` / `Cmd + R`: Rerun the app
- `Ctrl + Shift + R` / `Cmd + Shift + R`: Clear cache and rerun

Enjoy studying! 📚✨
