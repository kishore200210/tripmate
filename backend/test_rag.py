import asyncio
from app.db.session import AsyncSessionLocal
from app.modules.users.models import *
from app.modules.destinations.models import *
from app.modules.trips.models import *
from app.modules.ai_concierge.models import *
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.service import RAGService
from app.modules.rag.schemas import RAGQueryRequest

async def main():
    async with AsyncSessionLocal() as session:
        doc_repo = DocumentRepository(session)
        dest_repo = DestinationRepository(session)
        service = RAGService(repository=doc_repo, destination_repository=dest_repo)
        
        print("Reindexing...")
        res = await service.reindex_all_documents()
        print(res)
        
        print("Querying...")
        query = RAGQueryRequest(query="What is Paris known for?")
        res2 = await service.query_knowledge_base(query)
        print("Answer:", res2.answer)
        print("Sources:", res2.sources)

if __name__ == "__main__":
    asyncio.run(main())
