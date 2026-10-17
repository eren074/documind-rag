import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Kendi yazdığımız VectorStore modülünü içe aktarıyoruz
from src.vector_store import VectorStore

load_dotenv()


class RAGEngine:
    """
    Vektör veritabanından gelen alakalı doküman parçalarını (Context)
    Büyük Dil Modeli (LLM) ile birleştirerek kaynaklı yanıt üreten ana motor.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL")
        )
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

        # Ders 04 & 13: Grounding (Temellendirme) Sistem Promptu
        self.system_prompt = (
            "Sen yalnızca sağlanan doküman içeriklerine dayanarak yanıt veren güvenilir bir akademik asistansın.\n"
            "KURALLAR:\n"
            "1. Sadece aşağıda sana verilen 'BAĞLAM (CONTEXT)' bölümündeki bilgileri kullan.\n"
            "2. Yanıtında kullandığın bilgilerin sonunda mutlaka kaynak adını ve sayfa numarasını belirt (Örn: [Kaynak: Bilgisayar_Mimarisi.pdf, Sayfa: 12]).\n"
            "3. Eğer kullanıcının sorusunun yanıtı verilen BAĞLAM içinde yer almıyorsa, KESİNLİKLE kendi genel kültürünü kullanma ve "
            "'Üzgünüm, yüklenen dokümanlarda bu sorunun yanıtı bulunmamaktadır.' şeklinde cevap ver."
        )

    def format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Vektör veritabanından dönen parçaları LLM'in rahatça okuyabileceği metin formatına çevirir.
        """
        context_parts = []
        for i, item in enumerate(search_results, 1):
            source = item["metadata"].get("source", "Bilinmeyen Kaynak")
            page = item["metadata"].get("page_number", "?")
            text = item["text"]
            context_parts.append(f"[Parça {i} | Kaynak: {source} | Sayfa: {page}]\n{text}")

        return "\n\n".join(context_parts)

    def ask(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        1. Soruyu vektör veritabanında aratır (Retrieval).
        2. Bulunan parçaları prompta ekler (Augmentation).
        3. LLM'den kaynaklı yanıt üretir (Generation).
        """
        # 1. Retrieval (Bilgi Getirme)
        retrieved_chunks = self.vector_store.search(query=question, top_k=top_k)

        if not retrieved_chunks:
            return {
                "answer": "Henüz veritabanına hiçbir doküman yüklenmemiş. Lütfen önce bir PDF yükleyin.",
                "sources": []
            }

        # 2. Augmentation (Bağlamı Zenginleştirme)
        context_text = self.format_context(retrieved_chunks)
        user_prompt = (
            f"BAĞLAM (CONTEXT):\n{context_text}\n\n"
            f"---\n"
            f"KULLANICI SORUSU: {question}\n\n"
            f"Lütfen yukarıdaki bağlama sadık kalarak ve kaynak/sayfa belirterek yanıtla:"
        )

        # 3. Generation (Yanıt Üretimi)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2  # Halüsinasyonu önlemek için düşük yaratıcılık
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": retrieved_chunks
        }


# --- HIZLI TEST BLOĞU ---
if __name__ == "__main__":
    # Bir önceki adımda kaydettiğimiz 3 ders notunun olduğu veritabanına bağlan
    store = VectorStore()
    rag = RAGEngine(vector_store=store)

    print("🤖 TEST 1: Dokümanda OLAN bir bilgiyi soralım")
    soru_1 = "İşlemci matematiksel hesaplamaları hangi bileşenle yapar ve TCP ne işe yarar?"
    print(f"Soru: {soru_1}\n")
    yanit_1 = rag.ask(soru_1, top_k=3)
    print(f"Yanıt:\n{yanit_1['answer']}\n")
    print("-" * 60)

    print("\n🤖 TEST 2: Dokümanda OLMAYAN bir bilgiyi soralım (Halüsinasyon Testi)")
    soru_2 = "Python programlama dilinde sözlük (dictionary) nasıl tanımlanır?"
    print(f"Soru: {soru_2}\n")
    yanit_2 = rag.ask(soru_2, top_k=3)
    print(f"Yanıt:\n{yanit_2['answer']}\n")