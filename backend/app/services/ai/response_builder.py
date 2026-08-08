class ResponseBuilder:

    def build(
        self,
        answer,
        analysis,
        documents
    ):

        return {

            "answer": answer,

            "analysis": analysis,

            "documents_used": documents

        }