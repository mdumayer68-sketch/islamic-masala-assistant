import os
import streamlit as st
from qdrant_client import QdrantClient
from openai import OpenAI

# এনভায়রনমেন্ট ভেরিয়েবল থেকে কিগুলো নেওয়া
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_KEY")
nvidia_key = os.getenv("NVIDIA_API_KEY")

# ক্লায়েন্ট কানেকশন
qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nvidia_key)

st.title("Islamic Masala Assistant")
user_input = st.text_input("আপনার প্রশ্ন লিখুন:")

if user_input:
    st.write("চিন্তা করছি...")
    # এখানে আমরা পরে সার্চ এবং এনভায়রনমেন্ট ইন্টিগ্রেশন যুক্ত করব
    st.write("আপনার প্রশ্নের উত্তর এখানে আসবে।")
