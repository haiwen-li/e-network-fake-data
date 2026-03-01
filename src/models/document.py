from pydantic import BaseModel


STATUSES = {"pending", "text_extracted", "processed"}


class Document(BaseModel):
    id: str
    title: str
    url: str = ""           # empty if local file
    local_path: str = ""    # path to .txt file in data/text/
    source: str = ""        # e.g. courtlistener, archive.org, local
    date: str = ""
    notes: str = ""
    status: str = "pending" # pending | text_extracted | processed
