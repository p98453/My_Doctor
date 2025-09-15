from concurrent.futures import thread
import json
import requests
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings

from .Qwen import Qwen
from .models import Topic, Chat
from .RagChroma import MyChromaDB

# 初始化配置
vllm_host = settings.VLLM_CONFIG["host"]
vllm_model = settings.VLLM_CONFIG["model"]
tokenizer_url = vllm_host + "/tokenize"

qwen_client = Qwen(host=vllm_host, model=vllm_model)
MAX_TOKENS = 9000  # 总 token 限制

# 初始化 RAG 数据库
vdb = MyChromaDB(settings.RAG_CONFIG)

def ai_chat_123(request):

    def count_tokens(messages):
        """
        调用 tokenizer 服务，计算 messages 的总 token 数
        """
        resp = requests.post(tokenizer_url, json={"messages": messages}, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        return result.get("count", 0)

    question = request.GET.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "问题不能为空"}, status=400)

    user_id = 1
    topic_id = int(request.GET.get("topic_id", "0"))
    topic = None

    if topic_id == 0:
        topic = Topic(title=question, user_id=user_id, status=1)
        topic.save()
        topic_id = topic.id
    else:
        try:
            topic = Topic.objects.get(id=topic_id, status=1)
        except Topic.DoesNotExist:
            topic = Topic(title=question, user_id=user_id, status=1)
            topic.save()
            topic_id = topic.id

    # system 消息永远保留
    messages = [{"role": "system", "content": "你是一个有帮助的助手,擅长紧密结合上下文来回答问题。"}]

    # 获取历史聊天
    chats = list(Chat.objects.filter(topic_id=topic_id).order_by("id"))

    # 精准截断历史对话
    total_tokens = None
    for chat in chats:
        candidate_messages = messages + [{"role": chat.role, "content": chat.content}]
        total_tokens = count_tokens(candidate_messages)
        if total_tokens > MAX_TOKENS:
            # 超过限制，丢弃历史，仅保留 system
            messages = [messages[0]]
            break
        messages = candidate_messages

    # 加入本次用户输入
    messages.append({"role": "user", "content": question})

    # -------------------- RAG 知识检索 --------------------
    rerank_results = vdb.query(question, 30, topk=settings.RAG_CONFIG.get("rerank_top_k", 5))
    threshold = settings.RAG_CONFIG.get("rerank_threshold", 0.5)
    contexts, metadatas = vdb.filter_knowledge(rerank_results, threshold)

    if contexts:
        # 拼接上下文到 prompt
        prompt = f"""
        结合上下文内容，请回答用户问题：
        Context: {"\n\n".join(contexts)}
        Question: {question}
        Response:
        """
        messages.append({"role": "user", "content": prompt})

    # --------------------------------------------------------

    try:
        data = qwen_client.inference(messages, stream=True)

        def stream_response():
            yield f"data: <topic_id>{topic_id}</topic_id>\n\n"
            response_content = ""

            for chunk in data:
                processed_chunk = chunk.replace("data:", "")
                response_content += processed_chunk
                yield f"{chunk}\n\n"

            yield f"data: <metedata>{metadatas}</metedata>\n\n"
            yield "data: [DONE]\n\n"

            # 保存助手消息
            Chat.objects.create(topic_id=topic_id, user_id=user_id,
                                role="assistant", content=response_content)

            # 控制台输出
            print(f"topic_id: {topic_id}, question: {question}, response: {response_content}")

        # 保存用户输入
        Chat.objects.create(topic_id=topic_id, user_id=user_id,
                            role="user", content=question)

        response_stream = StreamingHttpResponse(stream_response(),
                                                content_type='text/event-stream')

        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream

    except Exception as e:
        return JsonResponse({"error": f"调用大模型失败：{e}"}, status=500)


# 创建第二个视图函数
def chatlist(request):

    # 假设一个用户
    user_id = 1

    history = Topic.objects.filter(user_id=user_id).order_by("-id")
    chatlist = []
    # 把数据放到列表中
    for item in history:
        chatlist.append(
            {
                "id": item.id,
                "title": item.title,
            }
        )

    data = {
        "code": 200,
        "msg": "OK",
        "data": chatlist,
    }

    return JsonResponse(data, safe=False)

# 创建第三个视图函数
def chathistory(request):
    # 接收前端提交的topic_id
    topic_id = int(request.GET.get("topic_id", "0"))
    # 获取对应的聊天记录
    chat_history = Chat.objects.filter(topic_id=topic_id).order_by("-id")
    chatlist = []
    # 把数据放到列表中
    for item in chat_history:
        chatlist.append(
            {
                "role": item.role,
                "content": item.content,
            }
        )
        data = {
            "code": 200,
            "msg": "OK",
            "data": chatlist,
            }
    return JsonResponse(data, safe=False)

# 创建第四个视图函数
def delete_topic(request):
    # 接收前端提交的 topic_id
    topic_id = int(request.GET.get("topic_id", "0"))
    print(f"接收到的 topic_id 是：{topic_id}")  # 调试信息

    try:
        topic = Topic.objects.get(id=topic_id)
        topic.status = 0   # 逻辑删除（标记为无效）
        topic.save()
        data = {
            "code": 200,
            "msg": "删除成功",
        }
    except Topic.DoesNotExist:
        data = {
            "code": 404,
            "msg": "该对话不存在",
        }

    return JsonResponse(data, safe=False)




