from pydantic import BaseModel, Field

class SourceOptions(BaseModel):
    """
    Options for the source of the data.
    """
    path: str = Field(..., description="The source of the data, e.g., 'file', 'api', etc.")
    type: str = Field(..., description="The type of the source, e.g., 'pdf', 'markdown', etc.")