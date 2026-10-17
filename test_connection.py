import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

def test_llm():
    print("LLM bağlantısı test ediliyor...")
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {"role": "system", "content": "Sen yardımcı bir bilgisayar mühendisliği asistanısın."},
            {"role": "user", "content": "RAG mimarisinin amacını tek cümleyle açıkla."}
        ],
        temperature=0.3
    )
    print("\n✅ Bağlantı Başarılı! Modelin Yanıtı:")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    test_llm()
