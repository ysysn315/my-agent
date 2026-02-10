from pymilvus import connections, utility
connections.connect(host="localhost", port=19530)
utility.drop_collection("knowledge_base")
print("Collection 已删除")
