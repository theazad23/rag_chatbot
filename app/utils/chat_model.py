# app/utils/chat_model.py
from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from app.config import settings
import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class PromptStrategy(str, Enum):
    STANDARD = "standard"
    ACADEMIC = "academic"
    CONCISE = "concise"
    CREATIVE = "creative"
    STEP_BY_STEP = "step_by_step"

class ResponseFormat(str, Enum):
    DEFAULT = "default"
    JSON = "json"
    MARKDOWN = "markdown"
    BULLET_POINTS = "bullet_points"

class ChatModelCallback(BaseCallbackHandler):
    """Callback handler for logging and monitoring chat model interactions."""
    
    def __init__(self):
        self.start_time = None
        self.total_tokens = 0
        
    def on_llm_start(self, *args, **kwargs):
        self.start_time = datetime.now()
        logger.info(f"Starting LLM call at {self.start_time}")
    
    def on_llm_end(self, *args, **kwargs):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        logger.info(f"LLM call completed in {duration:.2f} seconds")
    
    def on_llm_error(self, error: Exception, *args, **kwargs):
        logger.error(f"LLM error occurred: {str(error)}")

class ChatModel:
    """Enhanced chat model with configurable prompts and response formats."""
    
    def __init__(self):
        self.callbacks = [ChatModelCallback()]
        self.model = ChatOpenAI(
            model_name=settings.MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            model_kwargs={"top_p": settings.TOP_P},
            callbacks=self.callbacks
        )
        
        # Initialize prompt templates for different strategies
        self._initialize_prompt_templates()
        
    def _initialize_prompt_templates(self):
        """Initialize different prompt strategies."""
        self.prompt_templates = {
            PromptStrategy.STANDARD: ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant with broad knowledge and understanding. 
                Answer questions based on the provided context. If the answer cannot be found in the context, 
                say 'I don't have enough information in the provided context to answer that question.'"""),
                ("human", "Context: {context}\n\nQuestion: {question}")
            ]),
            
            PromptStrategy.ACADEMIC: ChatPromptTemplate.from_messages([
                ("system", """You are an academic expert providing detailed, well-structured analyses. 
                Cite specific examples from the context and organize your response with clear sections. 
                Use academic language and maintain a scholarly tone."""),
                ("human", """Context: {context}

Question: {question}

Please provide a structured analysis with:
1. Main points
2. Supporting evidence from the context
3. Detailed explanation
4. Conclusion""")
            ]),
            
            PromptStrategy.CONCISE: ChatPromptTemplate.from_messages([
                ("system", """Provide brief, direct answers focusing on key information. 
                Be concise but complete. Use simple language and get straight to the point."""),
                ("human", "Context: {context}\n\nQuestion: {question}\n\nProvide a concise answer:")
            ]),
            
            PromptStrategy.CREATIVE: ChatPromptTemplate.from_messages([
                ("system", """You are a creative communicator who makes information engaging and interesting. 
                Use analogies, examples, and engaging language while maintaining accuracy. 
                Make complex information accessible and memorable."""),
                ("human", "Context: {context}\n\nQuestion: {question}")
            ]),
            
            PromptStrategy.STEP_BY_STEP: ChatPromptTemplate.from_messages([
                ("system", """Break down complex information into clear, sequential steps. 
                Number each point and provide a logical flow of information. 
                Ensure each step builds upon the previous one."""),
                ("human", """Context: {context}

Question: {question}

Please break this down step by step:""")
            ])
        }
    
    def _format_response(self, response: str, format_type: ResponseFormat) -> str:
        """Format the response according to the specified format."""
        try:
            if format_type == ResponseFormat.DEFAULT:
                return response
            
            if format_type == ResponseFormat.JSON:
                # Parse the response into structured data
                sections = response.split('\n\n')
                return json.dumps({
                    "main_response": sections[0],
                    "additional_details": sections[1:] if len(sections) > 1 else [],
                    "generated_at": datetime.now().isoformat()
                }, indent=2)
                
            if format_type == ResponseFormat.MARKDOWN:
                # Add markdown formatting
                lines = response.split('\n')
                formatted = []
                for line in lines:
                    if line.strip():
                        if line.startswith(('1.', '2.', '3.')):
                            formatted.append(f"\n{line}")
                        elif ':' in line:
                            title, content = line.split(':', 1)
                            formatted.append(f"### {title.strip()}\n{content.strip()}")
                        else:
                            formatted.append(line)
                return '\n\n'.join(formatted)
                
            if format_type == ResponseFormat.BULLET_POINTS:
                lines = response.split('\n')
                formatted = []
                for line in lines:
                    if line.strip():
                        if not line.startswith('•'):
                            formatted.append(f"• {line.strip()}")
                        else:
                            formatted.append(line)
                return '\n'.join(formatted)
                
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return response

    async def generate_response(
        self,
        question: str,
        context: List[str],
        strategy: PromptStrategy = PromptStrategy.STANDARD,
        response_format: ResponseFormat = ResponseFormat.DEFAULT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response with enhanced options and metadata.
        
        Args:
            question: The question to answer
            context: List of context strings
            strategy: The prompt strategy to use
            response_format: The desired response format
            metadata: Optional metadata to include in response
        
        Returns:
            Dict containing response and metadata
        """
        try:
            # Get the appropriate prompt template
            prompt_template = self.prompt_templates.get(strategy, self.prompt_templates[PromptStrategy.STANDARD])
            
            # Combine context chunks into a single string
            context_text = "\n\n".join(context)
            
            # Generate prompt
            prompt = prompt_template.format(
                context=context_text,
                question=question
            )
            
            # Get response from model
            response = self.model.invoke(prompt)
            
            # Format the response
            formatted_response = self._format_response(response.content, response_format)
            
            # Prepare the result dictionary
            result = {
                "response": formatted_response,
                "metadata": {
                    "strategy": strategy,
                    "response_format": response_format,
                    "timestamp": datetime.now().isoformat(),
                    "model": settings.MODEL_NAME,
                    "context_chunks_used": len(context)
                }
            }
            
            # Add any additional metadata
            if metadata:
                result["metadata"].update(metadata)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def update_prompt_strategy(self, strategy: PromptStrategy, system_message: str, human_template: str):
        """
        Add or update a prompt strategy.
        
        Args:
            strategy: The strategy name to update
            system_message: The new system message
            human_template: The new human message template
        """
        try:
            self.prompt_templates[strategy] = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_template)
            ])
            logger.info(f"Successfully updated prompt strategy: {strategy}")
        except Exception as e:
            logger.error(f"Error updating prompt strategy: {e}")
            raise