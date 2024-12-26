from llama_index.core import Document, VectorStoreIndex

import qcflow

index = VectorStoreIndex.from_documents(documents=[Document.example()])

qcflow.models.set_model(index)
