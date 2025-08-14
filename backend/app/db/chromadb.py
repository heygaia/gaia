from functools import lru_cache
from typing import Dict, Optional

import chromadb
from app.config.loggers import chroma_logger as logger
from app.config.settings import settings
from chromadb.api import AsyncClientAPI, ClientAPI
from chromadb.config import Settings
from fastapi import Request
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


@lru_cache(maxsize=1)
def get_langchain_embedding_model():
    """
    Lazy-load the Google Gemini embedding model and cache it.

    Returns:
        GoogleGenerativeAIEmbeddings: The embedding model
    """
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
    )


class ChromaClient:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ChromaClient, cls).__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance

    def __init__(
        self,
        chroma_client: AsyncClientAPI,
        langchain_chroma_client: Chroma,
        constructor_client: ClientAPI | None = None,
    ):
        # Only initialize once
        if not hasattr(self, "_initialized") or not self._initialized:
            self._chroma_client = chroma_client
            self._default_langchain_client = langchain_chroma_client
            self._constructor_client = constructor_client
            self._langchain_clients: Dict[str, Chroma] = {}
            self._initialized: bool = True

    @staticmethod
    def get_client(request: Request | None = None):
        """
        Get the ChromaDB client from the application state.

        Args:
            request: The FastAPI request object

        Returns:
            The ChromaDB client from the application state

        Raises:
            RuntimeError: If ChromaDB client is not available in the application state
        """
        if not request:
            if ChromaClient.__instance is None or not hasattr(
                ChromaClient.__instance, "_chroma_client"
            ):
                logger.error("ChromaDB client not initialized")
                raise RuntimeError("ChromaDB client not initialized")
            return ChromaClient.__instance._chroma_client

        if not hasattr(request.app.state, "chroma_client"):
            logger.error("ChromaDB client not found in application state")
            raise RuntimeError("ChromaDB client not initialized in application state")
        return request.app.state.chroma_client

    @staticmethod
    async def get_langchain_client(
        collection_name: Optional[str] = None,
        embedding_function=None,
        create_if_not_exists: bool = True,
    ) -> Chroma:
        """
        Get a langchain Chroma client for a specific collection.

        Args:
            collection_name: The name of the collection to connect to. If None, returns the default client.
            embedding_function: Optional embedding function to use with the client.
                               If None, the default embedding model will be used.
            create_if_not_exists: Whether to create the collection if it doesn't exist.

        Returns:
            The langchain Chroma client for the specified collection

        Raises:
            RuntimeError: If langchain Chroma client is not available
        """
        if embedding_function is None:
            embedding_function = get_langchain_embedding_model()

        if ChromaClient.__instance is None:
            logger.error("ChromaClient instance not initialized")
            raise RuntimeError("ChromaClient instance not initialized")

        # If no collection name provided, return the default client
        if not collection_name:
            if (
                not hasattr(ChromaClient.__instance, "_default_langchain_client")
                or not ChromaClient.__instance._default_langchain_client
            ):
                logger.error("Default Langchain Chroma client not found")
                raise RuntimeError("Default Langchain Chroma client not initialized")
            return ChromaClient.__instance._default_langchain_client

        # Check if we already have a client for this collection
        if collection_name in ChromaClient.__instance._langchain_clients:
            return ChromaClient.__instance._langchain_clients[collection_name]

        # Create a new client for this collection
        try:
            chroma_client = ChromaClient.__instance._chroma_client
            constructor_client = ChromaClient.__instance._constructor_client

            # Check if collection exists, create if it doesn't
            collections = await chroma_client.list_collections()
            collections = list(map(lambda x: x.name, collections))  # type: ignore

            if collection_name not in collections:
                if create_if_not_exists:
                    logger.info(
                        f"Collection '{collection_name}' not found. Creating new collection..."
                    )
                    await chroma_client.create_collection(
                        name=collection_name, metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"Collection '{collection_name}' created successfully.")
                else:
                    logger.error(
                        f"Collection '{collection_name}' not found and create_if_not_exists is False"
                    )
                    raise RuntimeError(f"Collection '{collection_name}' not found")

            # Create Langchain client for this collection
            new_client = Chroma(
                client=constructor_client,
                collection_name=collection_name,
                embedding_function=embedding_function,
            )

            # Cache the client for future use
            ChromaClient.__instance._langchain_clients[collection_name] = new_client
            logger.info(
                f"Created new Langchain client for collection '{collection_name}'"
            )
            return new_client
        except Exception as e:
            logger.error(
                f"Error creating Langchain client for collection '{collection_name}': {e}"
            )
            raise RuntimeError(f"Failed to create Langchain client: {e}") from e


async def init_chroma(app=None):
    """
    Initialize ChromaDB connection and store the client in the app state.

    Args:
        app: FastAPI application instance

    Returns:
        The ChromaDB client
    """
    try:
        logger.info("Initializing ChromaDB connection...")

        # Initialize ChromaDB async http client
        client = await chromadb.AsyncHttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT,
        )

        # Initialize ChromaDB async client for langchain
        # This is a workaround to avoid the `coroutine` error in langchain
        # when using the async client directly
        constructor_client = chromadb.Client(
            settings=Settings(
                chroma_server_host=settings.CHROMADB_HOST,
                chroma_server_http_port=settings.CHROMADB_PORT,
            )
        )

        # Create default langchain client with no specific collection
        langchain_chroma_client = Chroma(
            client=constructor_client,
            embedding_function=get_langchain_embedding_model(),
        )

        response = await client.heartbeat()
        logger.info(f"ChromaDB heartbeat response: {response}")
        logger.info(
            f"Successfully connected to ChromaDB at {settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}"
        )

        existing_collections = await client.list_collections()
        existing_collection_names = [col.name for col in existing_collections]  # type: ignore
        collection_names = ["notes", "documents"]

        # Create collections if they don't exist
        for collection_name in collection_names:
            if collection_name not in existing_collection_names:
                logger.info(
                    f"'{collection_name}' collection not found. Creating new collection..."
                )
                await client.create_collection(
                    name=collection_name, metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"'{collection_name}' collection created successfully.")
            else:
                logger.info(
                    f"Collection '{collection_name}' already exists, skipping creation."
                )

        ChromaClient(
            chroma_client=client,
            langchain_chroma_client=langchain_chroma_client,
            constructor_client=constructor_client,
        )

        if app:
            app.state.chroma_client = client
            logger.info("Client stored in application state")

        return client
    except Exception as e:
        logger.error(f"Error connecting to ChromaDB: {e}")
        logger.warning(
            f"Failed to connect to ChromaDB at {settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}"
        )
        raise RuntimeError(f"ChromaDB connection failed: {e}") from e
