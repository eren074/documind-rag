import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any


class VectorStore:
    """
    Metin parçalarını (chunks) vektörlere (embeddings) dönüştürüp
    ChromaDB üzerinde saklayan ve anlamsal arama (semantic search) yapan sınıf.
    """

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents"):
        # Veritabanını diske kaydedecek şekilde başlat
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = collection_name

        # Türkçe ve İngilizce destekli çok dilli Embedding modeli
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        # Koleksiyonu (tabloyu) oluştur veya mevcutsa getir
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        DocumentProcessor'dan gelen metin parçalarını vektör veritabanına ekler.
        """
        if not chunks:
            return 0

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Aynı ID varsa günceller, yoksa yeni ekler (upsert)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Kullanıcının sorusunu vektöre çevirir ve en alakalı top_k metin parçasını döndürür.
        """
        if self.collection.count() == 0:
            return []

        # Koleksiyondaki toplam parça sayısından fazla sonuç istememek için kontrol
        n_results = min(top_k, self.collection.count())

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
                })

        return formatted_results

    def clear_database(self):
        """
        Veritabanındaki tüm kayıtları temizler.
        """
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )


# --- HIZLI TEST BLOĞU ---
if __name__ == "__main__":
    print("Vektör veritabanı ve Embedding modeli hazırlanıyor (İlk çalışmada model indirilir)...")
    store = VectorStore()
    store.clear_database()

    # Birbirinden farklı 3 konudan örnek ders notu parçaları
    ornek_parcalar = [
        {
            "id": "not_1",
            "text": "CPU içindeki ALU (Aritmetik Mantık Birimi), toplama, çıkarma ve mantıksal karşılaştırma işlemlerini donanım seviyesinde gerçekleştirir.",
            "metadata": {"source": "Bilgisayar_Mimarisi.pdf", "page_number": 12}
        },
        {
            "id": "not_2",
            "text": "İlişkisel veritabanlarında Primary Key (Birincil Anahtar), bir tablodaki her satırı benzersiz şekilde tanımlamak için kullanılır ve NULL olamaz.",
            "metadata": {"source": "Veritabani_Sistemleri.pdf", "page_number": 5}
        },
        {
            "id": "not_3",
            "text": "TCP protokolü, verilerin karşı tarafa eksiksiz ve sıralı gitmesini garanti eden bağlantı yönelimli bir iletişim protokolüdür.",
            "metadata": {"source": "Bilgisayar_Aglari.pdf", "page_number": 24}
        }
    ]

    eklenen = store.add_chunks(ornek_parcalar)
    print(f"✅ Veritabanına {eklenen} adet ders notu parçası eklendi.\n")

    # DİKKAT: Sorumuzda 'ALU' veya 'CPU' kelimesi hiç geçmiyor, sadece 'işlemci matematiksel hesaplamaları' diyoruz!
    soru = "İşlemci matematiksel hesaplamaları hangi bileşenle yapar?"
    print(f"🔍 Soru: '{soru}'\n")

    sonuclar = store.search(soru, top_k=2)
    for sira, sonuc in enumerate(sonuclar, 1):
        print(f"--- En Alakalı {sira}. Sonuç (Kaynak: {sonuc['metadata']['source']}, Sayfa: {sonuc['metadata']['page_number']}) ---")
        print(f"Metin: {sonuc['text']}")
        print(f"Vektör Uzaklığı (Küçük olması daha yüksek benzerlik demektir): {sonuc['distance']:.4f}\n")