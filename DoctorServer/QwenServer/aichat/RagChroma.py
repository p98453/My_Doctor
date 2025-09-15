

# 导入配置信息
from django.conf import settings
import requests

# 启用词向量数据库

import chromadb

# 导入embedding_functions
from chromadb.utils import embedding_functions

class MyChromaDB:
    def __init__(self, ragconfig={}):
        self.chroma_client = chromadb.HttpClient(
            host=ragconfig['chroma_host']["host"], port=ragconfig['chroma_host']["port"]
        )
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=ragconfig['chroma_config']["embedding_model_path"]
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=ragconfig['chroma_config']["collection_name"],
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.emb_fn,
        )

    # 定义查询方法
    def query(self, query_text, n_results=20, ifRerank=True, topk=5):
        # 粗排：词向量数据库检索
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        # TODO：需要处理元消息和得分
        if not ifRerank:
            return {
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
            }

        # 二次精排
        data = {
            "model": "/root/autodl-tmp/RAG检索增强生成/bge-reranker-base",
            "query": query_text,
            "documents": results["documents"][0],
        }
        response = requests.post(settings.RAG_CONFIG["rerank_host"], json=data)
        rerank_results = response.json()["results"][:topk]
        # 构建metadata信息
        metadata = []
        documents = []
        relevance_score = []
        for d in rerank_results:
            # 这里的元消息不要去重了，和下面冲突了
            # if results["metadatas"][0][d["index"]] not in metadata
            # else None
            metadata.append(results["metadatas"][0][d["index"]])
            documents.append(d["document"]["text"])
            relevance_score.append(d["relevance_score"])

        return {
            "documents": documents,
            "metadatas": metadata,
            "relevance_score": relevance_score,
        }

    # 根据阈值对找到的知识块进行筛选
    def filter_knowledge(self, rerank_results, threshold):
        contexts = []
        metedatas = []
        for i, score in enumerate(rerank_results["relevance_score"]):
            if score >= threshold:
                contexts.append(rerank_results["documents"][i])
                # 构建不重复的元消息
                (
                    metedatas.append(rerank_results["metadatas"][i])
                    if rerank_results["metadatas"][i] not in metedatas
                    else None
                )

        return contexts, metedatas
