from langchain_core.callbacks import StreamingStdOutCallbackHandler, streaming_stdout
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser

from pathlib import Path
from typing import List, Dict, TypedDict

import os, logging

logger = logging.getLogger("assistant")


class DocumentManager:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=256,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " "]
        )

    def load_documents(self, path: Path):
        if path.is_file() and path.suffix.lower() == ".pdf":
            # Load a single PDF
            loader = PyPDFLoader(str(path))
            return loader.load()

        documents = []
        if path.is_dir():
            # Load all PDFs in the directory
            for file in path.glob("*.pdf"):
                loader = PyPDFLoader(str(file))
                documents.extend(loader.load())
        else:
            raise ValueError("Invalid path: Must be a PDF file or a directory containing PDFs.")

        return documents

    def process_doc(self, path: Path):
        docs = self.load_documents(path)
        return [
            Document(
                page_content=doc.page_content,
                metadata=self._clean_metadata(doc.metadata)
            ) for doc in self.text_splitter.split_documents(docs)
        ]

    def _clean_metadata(self, metadata: Dict) -> Dict:
        return {
            k: str(v) for k, v in metadata.items()
            if isinstance(v, (str, int, float, bool))
        }


class VectorStoreManager:
    def __init__(self, embeddings: OllamaEmbeddings, docs_dir: Path = Path("../documents/"), persist_dir: Path = Path("../faiss/")) -> None:
        self.embeddings = embeddings
        self.vector_store = None
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir
        self.doc_manager = DocumentManager()


        if not self.vector_store:
            try:
                logger.info("Loading FAISS vectorstore")
                if not self.persist_dir.exists():
                    logger.warning("Vector store persistance directory does not exists")
                    raise Exception("Vector store directory missing")
                elif not os.path.exists(f"{str(self.persist_dir)}/index.faiss"):
                    logger.warning("Vector store persistance does not exists")
                    raise Exception("Vector store missing")

                self.vector_store = FAISS.load_local(
                    str(self.persist_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Successfully Loaded FAISS vectorstore")
            except:
                logger.warning("Failed to load FAISS vectorstore")
                logger.info("Recreating FAISS vectorstore")

                docs = self.doc_manager.load_documents(self.docs_dir)
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
                self.persist()
                logger.info("Successfully created FAISS vectorstore")

    def get_retriever(self, search_kwargs: Dict = {"k": 3}):
        if not self.vector_store:
            logger.critical("FAISS vector store not initialized")
            raise ValueError("Vector store not initialized")
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def persist(self):
        if self.vector_store:
            self.vector_store.save_local(str(self.persist_dir))


class ConversationState(TypedDict):
    question: str 
    retrieved_docs: List[Document]
    conversation_history: List[Dict]
    generation: str



class Assistant:
    def __init__(self, model_name: str = "llama3.1", embeddings: str = "llama3.1"):
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.7,
            num_ctx=4048,
            # disable_streaming=False,
            # callbacks=[StreamingStdOutCallbackHandler()]
        )
        self.embeddings = OllamaEmbeddings(
            model=embeddings,
        )
        self.retriever = VectorStoreManager(self.embeddings, Path("./documents"), Path("./faiss")).get_retriever()
        self.prompt = PromptTemplate.from_template("""
        You are an mental health assistant who is chatting with a human to resolve there mental issues, anixety etc. 
        Use the following pieces of retrieved context to answer the question if it is relevant for answering the question. If you don't know the answer, just say that you don't know. 
        Use chat history, long term memory about user and context for replying to the user.
        ChatHistory: {chat_history}
        LongTermMemory: {long_term_memory}
        User: {question} 
        Context: {context} 
        Answer:
        """)

        workflow = StateGraph(ConversationState)
        # Define nodes
        # workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("generate", self.generate)

        # Build graph
        # workflow.add_edge(START, "retrieve")
        workflow.add_edge(START, "generate")
        # workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Compile
        self.workflow = workflow.compile()

    def retrieve(self, state: ConversationState) -> ConversationState:
        print("--RETRIEVE--")
        question = state['question']
        state['retrieved_docs'] = self.retriever.invoke(question)

        return state

    async def generate(self, state: ConversationState) -> ConversationState:
        print("--GENERATE--")
        question = state['question']
        docs = state['retrieved_docs']
        conversation_history = state['conversation_history']

        # Prompt
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        def format_history(history):
            return "\n".join(f"{msg['role']}: {msg["content"]}" for msg in history)

        rag_chain = self.prompt | self.llm | StrOutputParser()

        response = await rag_chain.ainvoke({
            "chat_history": format_history(conversation_history), 
            "long_term_memory": "",
            "context": format_docs(docs), 
            "question": question
        })
        state["generation"] = response

        return state
