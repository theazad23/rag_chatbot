from fastapi import APIRouter, HTTPException
from app.models.chat import QuestionRequest
from app.services import chat_model, memory_manager, vector_store

router = APIRouter(tags=["chat"])

@router.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question with conversation history."""
    try:
        conversation_context = []
        if request.conversation_id:
            history = memory_manager.get_conversation_context(request.conversation_id)
            
            conversation_context = [
                f"Previous interaction {i+1}:\n"
                f"Question: {interaction['question']}\n"
                f"Answer: {interaction['response']['response']}"
                for i, interaction in enumerate(history)
            ]
            
        document_context = vector_store.query(
            request.question,
            n_results=request.max_context
        )
        
        combined_context = [
            "\nConversation History:\n" + "\n\n".join(conversation_context),
            "\nRelevant Documents:\n" + "\n\n".join(document_context)
        ] if conversation_context else document_context
        
        result = await chat_model.generate_response(
            question=request.question,
            context=combined_context,
            strategy=request.strategy,
            response_format=request.response_format,
            context_mode=request.context_mode,
            metadata={"conversation_id": request.conversation_id} if request.conversation_id else None
        )
        
        if request.conversation_id:
            memory_manager.add_interaction(
                request.conversation_id,
                request.question,
                result,
                document_context
            )
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/conversation/{conversation_id}/continue")
async def continue_conversation(
    conversation_id: str,
    request: QuestionRequest
):
    """Continue an existing conversation."""
    try:
        if not memory_manager.get_conversation_summary(conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        request.conversation_id = conversation_id
        return await ask_question(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))