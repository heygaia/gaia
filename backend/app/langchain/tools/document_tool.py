import os
import tempfile
from typing import Annotated, Any, Dict, Optional, Literal, TypedDict
from uuid import uuid4

import pypandoc
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.config.loggers import chat_logger as logger
from app.docstrings.langchain.tools.document_tool_docs import GENERATE_DOCUMENT
from app.decorators import with_doc, with_rate_limiting
from app.services.upload_service import upload_file_to_cloudinary


# Simplified PDF configuration
class PDFConfig(TypedDict, total=False):
    """Simplified PDF configuration with commonly used options."""

    margins: str  # e.g., "0.5in", "1cm"
    font_family: str  # e.g., "Times New Roman", "Arial"
    line_spacing: float  # e.g., 1.0, 1.5, 2.0
    paper_size: Literal["letter", "a4"]
    document_class: Literal["article", "report"]
    table_of_contents: bool
    number_sections: bool


@tool
@with_rate_limiting("document_generation")
@with_doc(GENERATE_DOCUMENT)
async def generate_document(
    config: RunnableConfig,
    content: Annotated[
        str,
        "Complete file content - write EXACTLY what should appear in the final file",
    ],
    filename: Annotated[
        str, "Filename WITHOUT extension (e.g., 'script' not 'script.py')"
    ],
    format: Annotated[
        str, "File extension ONLY (e.g., 'py', 'js', 'html', 'pdf', 'docx', 'txt')"
    ],
    is_plain_text: Annotated[
        bool,
        "ALWAYS True for: code files (py,js,html,css,json,xml,sql,etc), text files, data files, config files. ONLY False for: pdf,docx,odt,epub - documents requiring special formatting",
    ],
    title: Annotated[
        Optional[str], "Document title - ONLY used when is_plain_text=False"
    ] = None,
    metadata: Annotated[
        Optional[Dict[str, Any]],
        "Additional metadata - ONLY used when is_plain_text=False",
    ] = None,
    font_size: Annotated[
        Optional[int],
        "Font size in points (e.g., 12, 14, 50) - ONLY used for PDF generation",
    ] = None,
    pdf_config: Annotated[
        Optional[PDFConfig],
        """Simple PDF configuration options - ONLY used for PDF generation. Supports:
        - margins: str (e.g., '0.5in', '1cm') - page margins
        - font_family: str (e.g., 'Times New Roman', 'Arial') - main font
        - line_spacing: float (e.g., 1.0, 1.5, 2.0) - line spacing multiplier
        - paper_size: 'letter' or 'a4' - paper size
        - document_class: 'article' or 'report' - document type
        - table_of_contents: bool - include table of contents
        - number_sections: bool - number sections and subsections
        Note: Colored links are always enabled for better PDF readability.
        """,
    ] = None,
) -> str:
    output_filename = f"{filename}.{format}"
    # Use secure temporary directory instead of hardcoded /tmp
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, output_filename)

    try:
        if is_plain_text:
            # Direct write - no processing, no limitations
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            # Process through pypandoc for formatted documents
            extra_args = []

            if title:
                extra_args.extend(["-M", f"title={title}"])

            if metadata:
                for key, value in metadata.items():
                    extra_args.extend(["-M", f"{key}={value}"])

            if format == "pdf":
                # Determine font size - use parameter if provided, otherwise default to 14pt
                pdf_font_size = font_size if font_size else 14

                # Base PDF configuration
                extra_args.extend(
                    [
                        "--pdf-engine=xelatex",
                        "-V",
                        f"fontsize={pdf_font_size}pt",
                        "-V",
                        "colorlinks=true",
                        "-V",
                        "linkcolor=blue",
                        "-V",
                        "urlcolor=blue",
                        "-V",
                        "citecolor=green",
                    ]
                )

                # Apply pdf_config if provided
                if pdf_config:
                    # Handle specific configurations individually to satisfy TypedDict
                    if "margins" in pdf_config:
                        extra_args.extend(
                            ["-V", f"geometry:margin={pdf_config['margins']}"]
                        )
                    if "font_family" in pdf_config:
                        extra_args.extend(
                            ["-V", f"mainfont={pdf_config['font_family']}"]
                        )
                    if "line_spacing" in pdf_config:
                        extra_args.extend(
                            ["-V", f"linestretch={pdf_config['line_spacing']}"]
                        )
                    if "paper_size" in pdf_config:
                        extra_args.extend(
                            ["-V", f"papersize={pdf_config['paper_size']}"]
                        )
                    if "document_class" in pdf_config:
                        extra_args.extend(
                            ["-V", f"documentclass={pdf_config['document_class']}"]
                        )

                    # Handle boolean configurations
                    if pdf_config.get("table_of_contents", False):
                        extra_args.extend(["-V", "toc=true"])
                    if pdf_config.get("number_sections", False):
                        extra_args.extend(["-V", "numbersections=true"])

                    # Set default margins if not specified
                    if "margins" not in pdf_config:
                        extra_args.extend(["-V", "geometry:margin=0.5in"])
                else:
                    # Default configuration if no pdf_config provided
                    extra_args.extend(["-V", "geometry:margin=0.5in"])

            pypandoc.convert_text(
                source=content,
                to=format,
                format="md",
                outputfile=temp_path,
                extra_args=extra_args,
            )

        cloudinary_url = upload_file_to_cloudinary(
            file_path=temp_path, public_id=f"{uuid4()}_{output_filename}"
        )

        # Return the successfully processed events
        writer = get_stream_writer()

        # Send calendar options to frontend via writer
        writer(
            {
                "document_data": {
                    "filename": output_filename,
                    "url": cloudinary_url,
                    "is_plain_text": is_plain_text,
                    "title": title,
                    "metadata": metadata,
                    "font_size": font_size,
                    "pdf_config": pdf_config,
                },
            }
        )

        logger.info("Document generated and uploaded successfully")
        logger.info(f"Document URL: {cloudinary_url}")

        return f"SUCCESS: Document '{output_filename}' has been generated and uploaded. The file is now available to the user through the frontend interface."

    except Exception as e:
        logger.error(f"Error generating document: {str(e)}")
        raise Exception(f"Generation failed: {str(e)}")
    finally:
        # Clean up temporary file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
