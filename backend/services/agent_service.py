"""
ScholARA — Agent Service
Implements a multi-agent workflow using LangGraph.
Nodes: Retriever, Reranker, Research (Synthesis), Fact Checker, Confidence.
"""

import math
from typing import TypedDict, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from loguru import logger

from backend.services.embedding_service import get_embedding_service
from backend.services.rerank_service import get_rerank_service
from backend.services.llm_service import get_llm_service


class AgentState(TypedDict):
    query: str
    document_ids: Optional[List[int]]
    chat_history: List[Dict]
    retrieved_chunks: List[Dict]
    reranked_chunks: List[Dict]
    synthesis: str
    fact_check_result: str
    confidence: float
    final_answer: str


def retrieve_node(state: AgentState):
    """Retrieve top 20 chunks."""
    logger.info("Agent: Running Retriever")
    embedding_svc = get_embedding_service()
    chunks = embedding_svc.search(
        query=state["query"],
        top_k=20,
        document_ids=state["document_ids"],
    )
    return {"retrieved_chunks": chunks}


def rerank_node(state: AgentState):
    """Rerank chunks and keep top 5."""
    logger.info("Agent: Running Reranker")
    rerank_svc = get_rerank_service()
    chunks = state["retrieved_chunks"]
    top_5 = rerank_svc.rerank(state["query"], chunks, top_k=5)
    return {"reranked_chunks": top_5}


async def research_node(state: AgentState):
    """Synthesize answer using structured format."""
    logger.info("Agent: Running Research Synthesizer")
    llm_svc = get_llm_service()
    
    system_prompt = """You are ScholARA, an expert AI research assistant.
You must analyze the retrieved context and provide a highly structured response.
Format your answer EXACTLY using these headings:

Summary:
[Brief overview of the answer]

Key Findings:
- [Finding 1]
- [Finding 2]

Evidence:
[Cite specific details from the context]

Methodology:
[How the research was conducted, if applicable]

Limitations:
[Any limitations mentioned in the text]

Source Citations:
[List sources used]

Do not include a Confidence section. 
Be precise and cite sources using the format provided in the context blocks.
If the context is empty or irrelevant, state that you cannot find the information.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in state.get("chat_history", []):
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    chunks = state.get("reranked_chunks", [])
    if chunks:
        context_text = "\n\n---\n\n".join([
            f"[Source: {c['filename']}, chunk {c['chunk_index'] + 1}, Section: {c.get('section', 'Unknown')}]\n{c['content']}"
            for c in chunks
        ])
        prompt = f"## Context\n{context_text}\n\n## Question\n{state['query']}"
    else:
        prompt = f"## Question\n{state['query']}\n\n(No context available)"
        
    messages.append({"role": "user", "content": prompt})
    
    response = await llm_svc.generate_response(messages)
    return {"synthesis": response}


async def fact_check_node(state: AgentState):
    """Verify claims in synthesis against chunks."""
    logger.info("Agent: Running Fact Checker")
    llm_svc = get_llm_service()
    
    # We use a lightweight check to ensure no gross hallucinations
    verify_prompt = f"""You are a Fact Checker. Review the context and the synthesis.
If the synthesis makes claims entirely unsupported by the context, write a brief correction.
Otherwise, just output 'VERIFIED'.

Context:
{state.get('reranked_chunks', [])}

Synthesis:
{state['synthesis']}
"""
    messages = [{"role": "user", "content": verify_prompt}]
    fact_check = await llm_svc.generate_response(messages)
    return {"fact_check_result": fact_check}


def confidence_node(state: AgentState):
    """Calculate confidence score based on retrieval, reranking, and citation."""
    logger.info("Agent: Running Confidence Calculator")
    chunks = state.get("reranked_chunks", [])
    
    if not chunks:
        confidence = 0.0
    else:
        # 1. Retrieval Similarity (normalize 0-1)
        sims = [c.get("similarity_score", 0) for c in chunks]
        # BGE embeddings cosine similarity is often high, but we'll cap it
        retrieval_sim = min(1.0, max(0.0, sum(sims)/len(sims)))
        
        # 2. Reranker Score (CrossEncoder logits to prob)
        def sigmoid(x):
            return 1 / (1 + math.exp(-x)) if x > -10 else 0.0
            
        r_scores = [sigmoid(c.get("reranker_score", 0)) for c in chunks]
        rerank_score = sum(r_scores)/len(r_scores)
        
        # 3. Citation Coverage
        synthesis = state.get("synthesis", "")
        cited = 0
        for c in chunks:
            if f"chunk {c['chunk_index'] + 1}" in synthesis or c["filename"] in synthesis:
                cited += 1
        citation_coverage = cited / len(chunks) if chunks else 0
        
        confidence_val = ((retrieval_sim + rerank_score + citation_coverage) / 3) * 100
        confidence = round(confidence_val, 1)
    
    # Format confidence string
    conf_str = f"Low ({confidence}%)"
    if confidence > 75:
        conf_str = f"High ({confidence}%)"
    elif confidence >= 50:
        conf_str = f"Medium ({confidence}%)"
        
    final_answer = f"{state['synthesis']}\n\nConfidence:\n{conf_str}"
    
    return {"confidence": confidence, "final_answer": final_answer}


def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("research", research_node)
    workflow.add_node("fact_check", fact_check_node)
    workflow.add_node("confidence", confidence_node)
    
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "research")
    workflow.add_edge("research", "fact_check")
    workflow.add_edge("fact_check", "confidence")
    workflow.add_edge("confidence", END)
    
    return workflow.compile()


_agent_graph = None

def get_agent_graph():
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_graph()
    return _agent_graph
