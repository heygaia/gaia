"""Memory service layer for handling all memory operations."""

from typing import Any, Dict, List, Optional

from app.config.loggers import llm_logger as logger
from app.agents.memory.client import memory_client_manager
from app.models.memory_models import (
    MemoryEntry,
    MemoryRelation,
    MemorySearchResult,
)


class MemoryService:
    """Service class for managing memory operations."""

    def __init__(self):
        """Initialize the memory service."""
        self.logger = logger

    async def _get_client(self):
        """Get the configured async memory client."""
        return await memory_client_manager.get_client()

    def _validate_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        Validate and return user_id.

        Args:
            user_id: User identifier

        Returns:
            Validated user_id or None
        """
        if not user_id:
            self.logger.warning("No user_id provided for memory operation")
            return None

        # Handle different user_id formats
        if isinstance(user_id, dict):
            # If user_id is accidentally a user object
            user_id = user_id.get("user_id") or user_id.get("id")

        return str(user_id) if user_id else None

    def _parse_memory_result(self, result: Dict[str, Any]) -> Optional[MemoryEntry]:
        """
        Parse a single memory result from Mem0 API response.

        Args:
            result: Memory result dictionary

        Returns:
            MemoryEntry or None if parsing fails
        """
        if not isinstance(result, dict):
            self.logger.warning(f"Expected dict, got {type(result)}: {result}")
            return None

        # Extract memory content - all API responses use "memory" field
        content = result.get("memory", "")

        if not content:
            self.logger.warning(f"No memory content found in result: {result}")
            return None

        try:
            memory_entry = MemoryEntry(
                id=result.get("id"),
                content=content,
                user_id=result.get("user_id", ""),
                metadata=result.get("metadata") or {},  # Handle None values
                categories=result.get("categories") or [],  # Handle None values
                created_at=result.get("created_at"),
                updated_at=result.get("updated_at"),
                expiration_date=result.get("expiration_date"),
                immutable=result.get("immutable", False),
                organization=result.get("organization"),
                owner=result.get("owner"),
            )

            self.logger.debug(f"Successfully parsed memory: {memory_entry.id}")
            return memory_entry

        except Exception as e:
            self.logger.error(
                f"Error creating MemoryEntry from data: {e}, raw data: {result}"
            )
            return None

    def _parse_memory_list(
        self, memories: List[Dict[str, Any]], user_id: str
    ) -> List[MemoryEntry]:
        """
        Parse a list of memory results.

        Args:
            memories: List of memory dictionaries
            user_id: User ID to associate with memories

        Returns:
            List of MemoryEntry objects
        """
        parsed_memories = []
        for memory_data in memories:
            try:
                if memory_entry := self._parse_memory_result(memory_data):
                    memory_entry.user_id = user_id
                    parsed_memories.append(memory_entry)
            except Exception as e:
                self.logger.warning(f"Failed to parse memory: {e}")
                continue

        self.logger.debug(
            f"Successfully parsed {len(parsed_memories)}/{len(memories)} memories"
        )
        return parsed_memories

    def _parse_add_result(self, result: Dict[str, Any]) -> Optional[MemoryEntry]:
        """
        Parse add operation result from Mem0 API.

        Args:
            result: Add result dictionary with format:
                    {"id": "...", "memory": "...", "event": "ADD", "structured_attributes": {...}}

        Returns:
            MemoryEntry or None if parsing fails
        """
        if not isinstance(result, dict):
            self.logger.warning(f"Expected dict, got {type(result)}: {result}")
            return None

        # Extract memory content directly from result
        content = result.get("memory", "")

        if not content:
            self.logger.warning(f"No memory content found in add result: {result}")
            return None

        try:
            memory_entry = MemoryEntry(
                id=result.get("id"),
                content=content,
                metadata=result.get("structured_attributes", {}),
                # Model now has defaults for all optional fields
            )

            self.logger.debug(f"Successfully parsed add result: {memory_entry.id}")
            return memory_entry

        except Exception as e:
            self.logger.error(
                f"Error creating MemoryEntry from add result: {e}, raw data: {result}"
            )
            return None

    def _extract_relationships_from_response(
        self, response: Any
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships list from API response.

        Args:
            response: API response which might contain relationships

        Returns:
            List of relationship dictionaries
        """
        # For Mem0 API v2, relationships are in the 'entities' format
        if isinstance(response, dict):
            # v2 API returns relationships as 'entities'
            entities = response.get("entities", [])
            if entities:
                return entities

            # Fallback to older formats if needed
            return (
                response.get("relations", [])
                or response.get("relationships", [])
                or response.get("graph", {}).get("relationships", [])
            )
        return []

    def _parse_relationships(
        self, relations: List[Dict[str, Any]]
    ) -> List[MemoryRelation]:
        """
        Parse relationships from Mem0 API v2 response.

        Args:
            relations: List of relationship dictionaries in v2 'entities' format:
                      [{"source": "alice123", "relation": "likes", "destination": "hiking"}]

        Returns:
            List of MemoryRelation objects
        """
        parsed_relations = []
        for relation_data in relations:
            try:
                # Handle v2 API format with 'entities'
                if (
                    "source" in relation_data
                    and "relation" in relation_data
                    and "destination" in relation_data
                ):
                    relation = MemoryRelation(
                        source=relation_data.get("source", ""),
                        source_type="entity",  # v2 API doesn't specify types, default to 'entity'
                        relationship=relation_data.get("relation", ""),
                        target=relation_data.get("destination", ""),
                        target_type="entity",  # v2 API doesn't specify types, default to 'entity'
                    )
                    parsed_relations.append(relation)
                # Fallback to old format if available
                elif (
                    "source" in relation_data
                    and "relationship" in relation_data
                    and "target" in relation_data
                ):
                    relation = MemoryRelation(
                        source=relation_data.get("source", ""),
                        source_type=relation_data.get("source_type", "entity"),
                        relationship=relation_data.get("relationship", ""),
                        target=relation_data.get("target", ""),
                        target_type=relation_data.get("target_type", "entity"),
                    )
                    parsed_relations.append(relation)
                else:
                    self.logger.warning(f"Unknown relationship format: {relation_data}")

            except Exception as e:
                self.logger.warning(f"Failed to parse relationship: {e}")
                continue

        self.logger.debug(
            f"Successfully parsed {len(parsed_relations)}/{len(relations)} relationships"
        )
        return parsed_relations

    async def store_memory(
        self,
        content: str,
        user_id: Optional[str],
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntry]:
        """
        Store a single memory.

        Args:
            content: Memory content to store
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            MemoryEntry if successful, None otherwise
        """
        user_id = self._validate_user_id(user_id)
        if not user_id:
            return None

        try:
            # Store as a simple user message for mem0 to infer memory from
            client = await self._get_client()
            result = await client.add(
                messages=[{"role": "user", "content": content}],
                user_id=user_id,
                metadata=metadata or {},
                infer=True,
                version="v2",
                run_id=conversation_id,
                output_format="v1.1",
            )

            self.logger.info(f"Memory stored for user {user_id}")
            # Mem0 add API returns a dict with 'results' key containing list of result objects
            if isinstance(result, dict) and "results" in result:
                results_list = result["results"]
            elif isinstance(result, list):
                results_list = result
            else:
                self.logger.warning(
                    f"Unexpected response format from mem0 add: {result}"
                )
                return None

            if not results_list:
                self.logger.warning("No results returned from mem0 add")
                return None

            # Get the first result (usually only one when adding)
            first_result = results_list[0]

            # Parse the add result
            memory_entry = self._parse_add_result(first_result)

            # Set the user_id and metadata
            if memory_entry:
                memory_entry.user_id = user_id
                if metadata:
                    memory_entry.metadata = metadata

            return memory_entry

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str],
        limit: int = 5,
    ) -> MemorySearchResult:
        """
        Search for relevant memories.

        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            MemorySearchResult with matching memories
        """
        user_id = self._validate_user_id(user_id)
        if not user_id:
            return MemorySearchResult()

        try:
            client = await self._get_client()
            results = await client.search(
                query=query,
                filters={"AND": [{"user_id": user_id}, {"run_id": "*"}]},
                limit=limit,
                keyword_search=True,
                rerank=True,
                version="v2",
            )

            # Response is a list of memory objects
            if not isinstance(results, list):
                self.logger.warning(
                    f"Unexpected response format from mem0 search: {type(results)}"
                )
                return MemorySearchResult()

            memories = self._parse_memory_list(results, user_id)

            return MemorySearchResult(
                memories=memories,
                total_count=len(memories),
                page=1,
                page_size=limit,
            )

        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return MemorySearchResult()

    async def get_all_memories(
        self,
        user_id: Optional[str],
        page: int = 1,
        page_size: int = 10,
    ) -> MemorySearchResult:
        """
        Get all memories for a user with pagination.

        Args:
            user_id: User identifier
            page: Page number
            page_size: Results per page

        Returns:
            MemorySearchResult with user's memories
        """
        user_id = self._validate_user_id(user_id)
        if not user_id:
            return MemorySearchResult()

        try:
            client = await self._get_client()
            # Request with graph enabled to get relationships
            response = await client.get_all(
                filters={"AND": [{"user_id": user_id}, {"run_id": "*"}]},
                version="v2",
                output_format="v1.1",  # Use format that includes graph data
            )

            # Check if response has graph data
            memories_list = []
            relationships_list = []

            if isinstance(response, dict):
                # v1.1 format with potential graph data
                memories_list = response.get("memories", response.get("results", []))
                relationships_list = self._extract_relationships_from_response(response)
            elif isinstance(response, list):
                # Simple list format
                memories_list = response
            else:
                self.logger.warning(
                    f"Unexpected response format from mem0 get_all: {type(response)}"
                )
                return MemorySearchResult()

            # Parse memories and relationships
            memory_entries = self._parse_memory_list(memories_list, user_id)
            relationships = self._parse_relationships(relationships_list)

            # Calculate pagination
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_memories = memory_entries[start_index:end_index]

            self.logger.info(
                f"Successfully processed {len(memory_entries)} memories and {len(relationships)} relationships for user {user_id}, "
                f"returning page {page} ({len(paginated_memories)} items)"
            )

            return MemorySearchResult(
                memories=paginated_memories,
                relations=relationships,
                total_count=len(memory_entries),
                page=page,
                page_size=page_size,
                has_next=end_index < len(memory_entries),
            )

        except Exception as e:
            self.logger.error(f"Error retrieving all memories: {e}")
            return MemorySearchResult()

    async def delete_memory(self, memory_id: str, user_id: Optional[str]) -> bool:
        """
        Delete a specific memory.

        Args:
            memory_id: Memory identifier
            user_id: User identifier (for validation only)

        Returns:
            True if successful, False otherwise
        """
        user_id = self._validate_user_id(user_id)
        if not user_id:
            return False

        try:
            # Mem0 cloud API doesn't require user_id for delete
            client = await self._get_client()
            await client.delete(memory_id=memory_id)
            self.logger.info(f"Memory {memory_id} deleted for user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            return False


# Create singleton instance
memory_service = MemoryService()
