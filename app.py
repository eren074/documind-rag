import warnings
warnings.filterwarnings("ignore")  # macOS LibreSSL uyarısını gizle

import streamlit as st
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.rag_engine import RAGEngine

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="DocuMind AI | RAG Asistanı",
    page_icon="📚",
    layout="wide"
)

# 2. Session State (Oturum Hafızası) Başlatma
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine(vector_store=st.session_state.vector_store)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Yan Menü (Sidebar) - PDF Yükleme ve Ayarlar
with st.sidebar:
    st.title("⚙️ Doküman Yönetimi")
    st.markdown("PDF ders notlarınızı veya teknik belgelerinizi yükleyerek onlarla sohbet edin.")

    uploaded_files = st.file_uploader(
        "PDF Dosyalarını Seçin",
        type=["pdf"],
        accept_multiple_files=True
    )

    st.subheader("🔧 RAG Parametreleri")
    chunk_size = st.slider("Parça Boyutu (Chunk Size)", min_value=300, max_value=1500, value=800, step=100)
    chunk_overlap = st.slider("Örtüşme (Chunk Overlap)", min_value=50, max_value=300, value=150, step=25)
    top_k = st.slider("Getirilecek Kaynak Sayısı (Top-K)", min_value=1, max_value=6, value=3)

    if st.button("📥 Dokümanları İşle ve Kaydet", use_container_width=True, type="primary"):
        if not uploaded_files:
            st.warning("Lütfen önce en az bir PDF dosyası yükleyin.")
        else:
            with st.spinner("PDF'ler okunuyor, parçalara ayrılıyor ve vektörleştiriliyor..."):
                processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                total_chunks = 0

                for pdf_file in uploaded_files:
                    chunks = processor.process_pdf(pdf_file, source_name=pdf_file.name)
                    added = st.session_state.vector_store.add_chunks(chunks)
                    total_chunks += added

                st.success(f"✅ {len(uploaded_files)} dosya işlendi! Toplam {total_chunks} metin parçası eklendi.")

    st.divider()

    # Veritabanı Durumu ve Temizleme
    db_count = st.session_state.vector_store.collection.count()
    st.caption(f"📊 Veritabanındaki Aktif Parça Sayısı: **{db_count}**")

    if st.button("🗑️ Veritabanını ve Sohbeti Sıfırla", use_container_width=True):
        st.session_state.vector_store.clear_database()
        st.session_state.messages = []
        st.rerun()

# 4. Ana Ekran - Sohbet Arayüzü
st.title("📚 DocuMind AI: Dokümanlarla Konuşan RAG Asistanı")
st.caption("Microsoft Generative AI for Beginners (RAG & Grounding Mimarisi)")

# Geçmiş mesajları ekrana çizdir
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("🔍 Referans Alınan Doküman Parçaları (Kanıtlar)"):
                for idx, src in enumerate(message["sources"], 1):
                    source_name = src["metadata"].get("source", "Bilinmeyen")
                    page_num = src["metadata"].get("page_number", "?")
                    distance = src.get("distance")
                    dist_str = f" | Vektör Uzaklığı: `{distance:.4f}`" if distance is not None else ""
                    st.markdown(f"**{idx}. Kaynak:** `{source_name}` — **Sayfa:** `{page_num}`{dist_str}")
                    st.info(src["text"])

# 5. Kullanıcıdan Yeni Soru Alma
if user_question := st.chat_input("Yüklediğiniz PDF'ler hakkında bir soru sorun..."):
    # Kullanıcının mesajını ekrana ve hafızaya ekle
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Asistanın yanıtını üret ve ekrana yazdır
    with st.chat_message("assistant"):
        with st.spinner("Dokümanlar taranıyor ve yanıt üretiliyor..."):
            result = st.session_state.rag_engine.ask(question=user_question, top_k=top_k)
            answer = result["answer"]
            sources = result["sources"]

            st.markdown(answer)

            if sources:
                with st.expander("🔍 Referans Alınan Doküman Parçaları (Kanıtlar)"):
                    for idx, src in enumerate(sources, 1):
                        source_name = src["metadata"].get("source", "Bilinmeyen")
                        page_num = src["metadata"].get("page_number", "?")
                        distance = src.get("distance")
                        dist_str = f" | Vektör Uzaklığı: `{distance:.4f}`" if distance is not None else ""
                        st.markdown(f"**{idx}. Kaynak:** `{source_name}` — **Sayfa:** `{page_num}`{dist_str}")
                        st.info(src["text"])

    # Asistan mesajını hafızaya kaydet
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })