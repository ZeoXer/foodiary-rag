import glob
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_PATH = glob.glob("data/*.txt")


def load_txt_documents():
    document_loader = UnstructuredLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def calculate_chunk_ids(chunks):
    count_dict = {}

    for chunk in chunks:
        filename = chunk.metadata.get("filename")

        if filename not in count_dict:
            count_dict[filename] = 0
        else:
            count_dict[filename] += 1

        element_id = chunk.metadata.get("element_id")
        chunk_id = f"{filename}_{element_id}_{count_dict[filename]}"

        chunk.metadata["id"] = chunk_id

    return chunks


if __name__ == "__main__":
    docs = load_txt_documents()
    chunks = split_documents(docs)
    chunks = calculate_chunk_ids(chunks)
    # pc = PineconeIndex()
    # pc.search_documents("How to make high protein meals?")
    # rc = RedisClient()
    # messages = rc.get_recent_messages("user_0")
    # print(len(messages))
    # print(messages)
