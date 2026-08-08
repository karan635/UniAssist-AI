from langchain_core.documents import Document


class ContextBuilder:

    def build_context(
        self,
        documents: list[Document]
    ) -> str:

        if not documents:
            return ""

        context = ""

        for index, doc in enumerate(documents, start=1):

            context += (
                f"\n\n========== Document {index} ==========\n"
            )

            context += (
                f"Course : {doc.metadata.get('course')}\n"
            )

            context += (
                f"Topic : {doc.metadata.get('topic')}\n"
            )

            context += (
                f"File : {doc.metadata.get('filename')}\n"
            )

            context += (
                f"Page : {doc.metadata.get('page') + 1}\n\n"
            )

            context += doc.page_content

            context += "\n"

        return context.strip()