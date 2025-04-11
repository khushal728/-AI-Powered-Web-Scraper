import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from io import BytesIO
import spacy
import streamlit.components.v1 as components
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# --- Streamlit UI ---
st.set_page_config(page_title="AI Web Scraper", layout="wide")

# Theme toggle with multiple options
st.sidebar.title("🎨 Theme")
theme = st.sidebar.radio("Choose your theme", ["🌞 Light", "🌙 Dark", "🌀 Gradient"])

if theme == "🌙 Dark":
    st.markdown("""
        <style>
            body { background-color: #0e1117; color: white; }
            .stTextInput > div > div > input,
            .stTextArea > div > textarea {
                background-color: #262730; color: white;
            }
        </style>
    """, unsafe_allow_html=True)

elif theme == "🌀 Gradient":
    st.markdown("""
        <style>
            body {
                background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
                color: white;
            }
            .stTextInput > div > div > input,
            .stTextArea > div > textarea {
                background-color: #2c3e50; color: white;
                border: 1px solid #16a085;
            }
            .stButton button {
                background-color: #16a085; color: white;
                border-radius: 12px;
            }
        </style>
    """, unsafe_allow_html=True)


st.title("🕷️ AI-Powered Web Scraper")
st.markdown("Built with ❤️ using Streamlit + NLP + AI")

url = st.text_input("🌐 Enter the URL to scrape")
tag = st.text_input("🏷️ Enter HTML tag to target (e.g., p, h1, table)", "")
scrape_button = st.button("🚀 Scrape")

# Placeholder for data
data = []
df = pd.DataFrame()

# Function for heuristic tag detection
def detect_relevant_tags(soup):
    priority_tags = ['main', 'article', 'section', 'table', 'div', 'p', 'h1', 'h2', 'h3']
    tag_scores = {}
    for tag in priority_tags:
        elements = soup.find_all(tag)
        text_lengths = [len(el.get_text(strip=True)) for el in elements if el.get_text(strip=True)]
        tag_scores[tag] = sum(text_lengths)
    sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, score in sorted_tags if score > 0][:3]  # Top 3 suggestions

# Function to extract named entities
def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return pd.DataFrame(entities, columns=["Entity", "Type"])

# Function to summarize text
def summarize_text(text, num_sentences=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

if scrape_button and url:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Smart tag detection if no tag is provided
        if not tag:
            suggested_tags = detect_relevant_tags(soup)
            st.info(f"🤖 Suggested tags based on content: {', '.join(suggested_tags)}")
            tag = suggested_tags[0]

        elements = soup.find_all(tag)
        data = [element.get_text(strip=True) for element in elements if element.get_text(strip=True)]
        df = pd.DataFrame(data, columns=[f"{tag} Content"])

        if not df.empty:
            st.success("✅ Scraping Successful!")
            st.dataframe(df)

            # NLP Entity Extraction
            all_text = " ".join(data)
            entity_df = extract_entities(all_text)
            if not entity_df.empty:
                st.subheader("🧠 Named Entity Recognition")
                st.dataframe(entity_df)

            # Summarization
            st.subheader("📝 Text Summarization")
            summary = summarize_text(all_text)
            st.write(summary)

            # Export Buttons
            st.subheader("📤 Export Options")
            col1, col2, col3 = st.columns(3)

            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📄 Download CSV", csv, "scraped_data.csv", "text/csv")

            with col2:
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
                st.download_button("📊 Download Excel", excel_buffer.getvalue(), "scraped_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with col3:
                json_data = df.to_json(orient="records", indent=2)
                st.download_button("🧾 Download JSON", json_data, "scraped_data.json", "application/json")

            # Visual Highlighting
            st.subheader("🔍 Webpage Preview with Tag Highlighting")
            highlight_script = f"""
            <iframe srcdoc='{response.text.replace("'", "&apos;")}' width="100%" height="500"></iframe>
            <script>
            setTimeout(() => {{
                const elements = window.frames[0].document.getElementsByTagName('{tag}');
                for (let el of elements) {{
                    el.style.border = "2px solid red";
                    el.title = "Highlighted: {tag}";
                }}
            }}, 1000);
            </script>
            """
            components.html(highlight_script, height=550, scrolling=True)

        else:
            st.warning("⚠️ No data found for the specified tag.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
