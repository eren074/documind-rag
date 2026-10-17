# 📚 DocuMind AI — Dokümanlarla Konuşan RAG Asistanı

Bu proje, Microsoft **Generative AI for Beginners** müfredatındaki **RAG (Retrieval-Augmented Generation)** mimarisini uygulamak amacıyla geliştirilmiştir. Yüklenen PDF dokümanlarını parçalara (chunks) ayırır, **ChromaDB** vektör veritabanında saklar ve sorulara **yalnızca doküman içeriğinden sayfa numarası referansı vererek** yanıt üretir.

---

## 🚀 Hızlı Kurulum (Kendi Bilgisayarınızda Çalıştırın)

Projeyi kendi bilgisayarınıza kurmak ve çalıştırmak için aşağıdaki komutları sırasıyla terminalinize yapıştırın:

### 1. Projeyi İndirin ve Sanal Ortamı Kurun
```bash
git clone https://github.com/eren074/documind-rag.git
cd documind-rag
python3 -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
```

### 2. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. API Anahtarınızı Tanımlayın (.env)
Örnek şablonu kopyalayarak kendi `.env` dosyanızı oluşturun:
```bash
cp .env.example .env
```
Ardından `.env` dosyasını açıp [Google AI Studio](https://aistudio.google.com/apikey) üzerinden ücretsiz aldığınız API anahtarınızı `LLM_API_KEY=` kısmına yapıştırın.

### 4. Uygulamayı Başlatın
```bash
streamlit run app.py
```
Tarayıcınızda otomatik açılan `http://localhost:8501` adresinden PDF yükleyip soru sormaya başlayabilirsiniz!

---

## 🧪 Modül Testleri (Opsiyonel)
Sistemin alt modüllerini terminalden ayrı ayrı test etmek için:
```bash
python3 test_connection.py
python3 src/document_processor.py
python3 src/vector_store.py
python3 -m src.rag_engine
```
