# src/advisory/book_processor.py
# Compatible with langchain>=1.x, langchain-community>=0.4.x

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import tempfile
import os


class FinancialBookProcessor:
    """
    Processes uploaded financial books (PDFs) and enables Q&A.
    Built on LangChain RAG: PDF → Chunks → Embeddings → FAISS → Q&A
    """

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2,
                              api_key=os.getenv("OPENAI_API_KEY"))
        self.vectorstore = None
        self.qa_chain = None
        self.book_name = None

    def load_book(self, pdf_bytes: bytes, book_name: str) -> dict:
        """
        Load a PDF book, chunk it, embed, and build retrieval chain.
        Returns status and number of chunks created.
        """
        try:
            # Write to temp file (PyPDFLoader needs a file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            # Load and split
            loader = PyPDFLoader(tmp_path)
            documents = loader.load()
            os.unlink(tmp_path)

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            chunks = splitter.split_documents(documents)

            # Build FAISS vector store
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            self.book_name = book_name

            # Build QA chain with custom prompt
            prompt_template = f"""You are a financial advisor who has studied {book_name} deeply.
Use the following excerpts from the book to answer the question.
Always relate the answer to practical Indian financial context (SIP, UPI, Indian tax laws).
If the answer is not in the context, say "This specific topic isn't covered in the book, but generally..."

Context from book:
{{context}}

Question: {{question}}

Answer (practical, specific, actionable):"""

            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
                chain_type_kwargs={"prompt": PROMPT}
            )

            return {"success": True, "chunks": len(chunks), "pages": len(documents)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def ask(self, question: str) -> str:
        """Ask a question about the loaded book."""
        if not self.qa_chain:
            return "No book loaded. Please upload a financial PDF first."
        try:
            result = self.qa_chain.invoke({"query": question})
            return result["result"]
        except Exception as e:
            return f"Error answering question: {str(e)}"
