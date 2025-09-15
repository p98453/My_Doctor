# 首先，确保安装了OpenAI的SDK
# pip3 install openai

from openai import OpenAI
from django.http import StreamingHttpResponse

class Qwen:
    def __init__(self, host, model):
        self.client = OpenAI(
            api_key="EMPTY",  # APIKey
            base_url=host + "/v1",  # 请求地址  /chat/completions
        )
        self.model = model  # 模型名称
        self.gen_kwargs = {
            "max_tokens": 1000,  # 生成的最大长度
            "temperature": 0.7,  # 生成丰富性，越大越有创造力 越小越确定
            "top_p": 0.8,  # 采样时的前P个候选词，越大越随机
            "extra_body": {
                "do_sample": True,  # 是否使用概率采样
                "top_k": 50,  # 采样时的前K个候选词，越大越随机
                "repetition_penalty": 1.2,  # 重复惩罚系数，越大越不容易重复
            }
        }

    def inference(self, messages, stream=False):
        """
        发送请求到OpenAI API进行文本生成。

        :param messages: 要发送给模型的消息列表。
        :param stream: 是否以流式方式接收响应。
        :return: 生成的文本内容或StreamingHttpResponse对象。
        """

        # 面向对象的模块化编程
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream, # 是否流式输出
            **self.gen_kwargs,
        )


        # 如果不需要流式处理，直接返回生成的文本内容
        if not stream:
            return response.choices[0].message.content
        # 如果需要流式处理
        else:
            for chunk in response:
                yield f"data:{chunk.choices[0].delta.content}"
            yield "data: [DONE]"


