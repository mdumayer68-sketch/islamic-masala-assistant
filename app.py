import streamlit as st
from groq import Groq
import fitz  # PyMuPDF
import os
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="ইসলামিক মাসআলা সহায়িকা",
    page_icon="☪️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #1a1a2e;
        color: #ffffff;
    }
    .stTextInput > div > div > input {
        background-color: #16213e;
        color: #ffffff;
        border: 1px solid #0f3460;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-family: 'Noto Nastaliq Urdu', serif;
    }
    .user-message {
        background-color: #0f3460;
        text-align: right;
    }
    .assistant-message {
        background-color: #16213e;
        border-left: 4px solid #e94560;
    }
    .reference-box {
        background-color: #0f3460;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 14px;
        border: 1px solid #e94560;
    }
    .header-text {
        text-align: center;
        color: #e94560;
        font-size: 28px;
        font-weight: bold;
        padding: 20px 0;
    }
    .sub-header {
        text-align: center;
        color: #a8a8b3;
        font-size: 16px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header-text">☪️ ইসলামিক মাসআলা সহায়িকা</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">হানাফী মাযহাব | শুধুমাত্র আপলোড করা কিতাব থেকে উত্তর</div>', 
            unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ সেটিংস")
    
    # API Key input
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_xxxxxxxxxxxx",
        help="আপনার Groq API Key দিন"
    )
    
    st.markdown("---")
    st.markdown("### 📚 কিতাব আপলোড করুন")
    
    uploaded_files = st.file_uploader(
        "পিডিএফ আপলোড করুন",
        type=['pdf'],
        accept_multiple_files=True,
        help="একসাথে একাধিক কিতাব আপলোড করতে পারবেন"
    )
    
    if uploaded_files:
        st.markdown("**আপলোড করা কিতাবসমূহ:**")
        for file in uploaded_files:
            st.markdown(f"✅ {file.name}")
    
    st.markdown("---")
    st.markdown("### ℹ️ তথ্য")
    st.markdown("""
    - শুধু আপলোড করা কিতাব থেকে উত্তর দেবে
    - কিতাবের নাম ও পৃষ্ঠা নম্বর দেখাবে
    - বাইরের কোনো তথ্য দেবে না
    """)

# PDF Processing Function
def extract_text_from_pdfs(uploaded_files):
    all_chunks = []
    
    for uploaded_file in uploaded_files:
        try:
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            book_name = uploaded_file.name.replace('.pdf', '')
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    chunk = {
                        "book_name": book_name,
                        "page_number": page_num + 1,
                        "total_pages": total_pages,
                        "content": text.strip()
                    }
                    all_chunks.append(chunk)
            
            doc.close()
            
        except Exception as e:
            st.error(f"❌ {uploaded_file.name} পড়তে সমস্যা হয়েছে: {str(e)}")
    
    return all_chunks

# Search Function
def search_relevant_chunks(query, chunks, max_chunks=5):
    query_words = query.lower().split()
    
    scored_chunks = []
    for chunk in chunks:
        content_lower = chunk['content'].lower()
        score = sum(1 for word in query_words if word in content_lower)
        if score > 0:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks[:max_chunks]]

# Get Answer Function
def get_answer(query, relevant_chunks, api_key):
    if not relevant_chunks:
        return "আপলোড করা কিতাবগুলোতে এই বিষয়ে কোনো তথ্য পাওয়া যায়নি।", []
    
    context = ""
    references = []
    
    for i, chunk in enumerate(relevant_chunks):
        context += f"\n\n[রেফারেন্স {i+1}]\n"
        context += f"কিতাব: {chunk['book_name']}\n"
        context += f"পৃষ্ঠা: {chunk['page_number']}\n"
        context += f"বিষয়বস্তু:\n{chunk['content']}\n"
        
        references.append({
            "book": chunk['book_name'],
            "page": chunk['page_number']
        })
    
    system_prompt = """আপনি একজন হানাফী মাযহাবের ইসলামিক স্কলার সহায়িকা।

আপনার কঠোর নিয়মসমূহ:
১. শুধুমাত্র নিচে দেওয়া রেফারেন্স থেকে উত্তর দিবেন
২. নিজে থেকে কিছু যোগ করবেন না
৩. যদি রেফারেন্সে উত্তর না থাকে তাহলে বলবেন "আপলোড করা কিতাবে এই বিষয়ে তথ্য পাওয়া যায়নি"
৪. উত্তরে অবশ্যই কিতাবের নাম ও পৃষ্ঠা নম্বর উল্লেখ করবেন
৫. বাংলায় উত্তর দিবেন
৬. আরবি ইবারত থাকলে সেটিও উল্লেখ করবেন"""

    user_prompt = f"""প্রশ্ন: {query}

নিচের রেফারেন্স থেকে উত্তর দিন:
{context}

মনে রাখবেন: শুধু এই রেফারেন্স থেকেই উত্তর দিবেন।"""

    try:
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        return answer, references
        
    except Exception as e:
        return f"❌ সমস্যা হয়েছে: {str(e)}", []

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# Process PDFs when uploaded
if uploaded_files and api_key:
    if st.sidebar.button("📖 কিতাব প্রসেস করুন", type="primary"):
        with st.spinner("কিতাব পড়া হচ্ছে... একটু অপেক্ষা করুন..."):
            st.session_state.chunks = extract_text_from_pdfs(uploaded_files)
            st.sidebar.success(f"✅ {len(st.session_state.chunks)} টি পৃষ্ঠা প্রসেস হয়েছে!")

# Chat Interface
st.markdown("### 💬 প্রশ্ন করুন")

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            🙋 <strong>আপনার প্রশ্ন:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            ☪️ <strong>উত্তর:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)
        
        if "references" in message and message["references"]:
            refs_html = '<div class="reference-box">📚 <strong>রেফারেন্সসমূহ:</strong><br>'
            for ref in message["references"]:
                refs_html += f'• {ref["book"]} — পৃষ্ঠা: {ref["page"]}<br>'
            refs_html += '</div>'
            st.markdown(refs_html, unsafe_allow_html=True)

# Input
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "আপনার মাসআলা লিখুন:",
        placeholder="যেমন: নামাজে সিজদায় যাওয়ার সঠিক পদ্ধতি কী?",
        height=100
    )
    submit = st.form_submit_button("🔍 উত্তর খুঁজুন", type="primary")

if submit and user_input:
    if not api_key:
        st.error("⚠️ প্রথমে Groq API Key দিন!")
    elif not st.session_state.chunks:
        st.error("⚠️ প্রথমে কিতাব আপলোড করে প্রসেস করুন!")
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        with st.spinner("কিতাব থেকে উত্তর খোঁজা হচ্ছে..."):
            relevant_chunks = search_relevant_chunks(
                user_input, 
                st.session_state.chunks
            )
            answer, references = get_answer(
                user_input, 
                relevant_chunks, 
                api_key
            )
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "references": references
        })
        
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #a8a8b3; font-size: 12px;'>
    শুধুমাত্র আপলোড করা কিতাব থেকে উত্তর প্রদান করা হয় | হানাফী মাযহাব
</div>
""", unsafe_allow_html=True)
