from pypdf import PdfReader
from typing import List, Dict, Any


class DocumentProcessor:
    """
    PDF dokümanlarını okuyan ve RAG mimarisi için örtüşmeli (overlapping)
    metin parçalarına (chunks) ayıran sınıf.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap değeri chunk_size değerinden küçük olmalıdır!")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_pages_from_pdf(self, pdf_file, source_name: str = "Doküman") -> List[Dict[str, Any]]:
        """
        PDF dosyasını sayfa sayfa okur ve her sayfanın metnini sayfa numarasıyla döndürür.
        """
        reader = PdfReader(pdf_file)
        pages_data = []

        for page_index, page in enumerate(reader.pages):
            raw_text = page.extract_text()
            if raw_text and raw_text.strip():
                # Fazla boşlukları ve satır sonlarını temizle
                cleaned_text = " ".join(raw_text.split())
                pages_data.append({
                    "text": cleaned_text,
                    "page_number": page_index + 1,
                    "source": source_name
                })

        return pages_data

    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        Uzun bir metni kelimeleri ortadan bölmemeye dikkat ederek
        chunk_size ve chunk_overlap kurallarına göre parçalara ayırır.
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Eğer metnin sonunda değilsek, kelimeyi ortadan kesmemek için son boşluğa kadar geri çekil
            if end < text_length:
                last_space = text.rfind(" ", start, end)
                if last_space != -1 and last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            # Bir sonraki parçaya overlap (örtüşme) kadar geriden başla
            start = max(end - self.chunk_overlap, start + 1)

        return chunks

    def process_pdf(self, pdf_file, source_name: str = "Doküman") -> List[Dict[str, Any]]:
        """
        PDF'i okur, parçalara ayırır ve her parçaya kaynak/sayfa bilgisini (metadata) ekler.
        """
        pages = self.extract_pages_from_pdf(pdf_file, source_name)
        all_chunks = []
        chunk_id = 0

        for page in pages:
            page_chunks = self.split_text_into_chunks(page["text"])
            for chunk_text in page_chunks:
                all_chunks.append({
                    "id": f"{source_name}_p{page['page_number']}_c{chunk_id}",
                    "text": chunk_text,
                    "metadata": {
                        "source": page["source"],
                        "page_number": page["page_number"]
                    }
                })
                chunk_id += 1

        return all_chunks


# --- HIZLI TEST BLOĞU ---
if __name__ == "__main__":
    processor = DocumentProcessor(chunk_size=120, chunk_overlap=30)
    ornek_metin = (
        "Retrieval-Augmented Generation (RAG), büyük dil modellerinin "
        "kendi eğitim verilerinde bulunmayan özel dokümanlara erişmesini "
        "ve bu dokümanlardan referans göstererek halüsinasyon görmeden "
        "doğru yanıtlar üretmesini sağlayan modern bir yapay zeka mimarisidir."
    )

    parcalar = processor.split_text_into_chunks(ornek_metin)
    print(f"✅ Örnek metin toplam {len(parcalar)} parçaya (chunk) bölündü:\n")
    for i, parca in enumerate(parcalar, 1):
        print(f"--- Parça {i} ({len(parca)} karakter) ---")
        print(parca)
        print()