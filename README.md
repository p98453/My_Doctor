# MyDoctor
中医在线问诊系统，能够实现全栈搭建的项目

## 搭建血泪史

渲染数据

![image-20250907122001283](README/image-20250907122001283.png)

调用api回应请求

![image-20250907131600355](README/image-20250907131600355.png)

构建服务器

![image-20250907163209894](README/image-20250907163209894.png)

功能模块创建

![image-20250907163325029](README/image-20250907163325029.png)

![image-20250907164533148](README/image-20250907164533148.png)

启动服务器

![image-20250907164808358](README/image-20250907164808358.png)

将前段端口从大模型改到服务器，解决**跨域问题**，实现前后端交互

![image-20250910183856872](README/image-20250910183856872.png)

![image-20250910184311568](README/image-20250910184311568.png)

服务器接收前段输入

![image-20250910192547084](README/image-20250910192547084.png)

流式输出

![image-20250911151136996](README/image-20250911151136996.png)

数据库创建表

![image-20250911153656091](README/image-20250911153656091.png)

生成迁移文件

![image-20250911155302990](README/image-20250911155302990.png)

迁移到数据库中

![image-20250911155436455](README/image-20250911155436455.png)

服务器存储前端输入内容存入服务器

![](README/image-20250911183655087.png)

将每一轮对话设计成一个相同的topic_id,方便后面进行上下文检索

![image-20250911192201533](README/image-20250911192201533.png)

存储模型响应结果

![image-20250911195044752](README/image-20250911195044752.png)

显示对话列表，并转到相应对话，后续可以进行上下文互通，多轮对话

![image-20250912101754819](README/image-20250912101754819.png)

多轮对话，(system prompt + 历史对话 + 本次用户输入 + 模型生成输出) ≤ 10000 tokens（--max-model-len 10000）

![image-20250912104626047](README/image-20250912104626047.png)

管理上下文总tokens

![image-20250912112937300](README/image-20250912112937300.png)

调用大模型计算总的tokens，并删除超出的内容

![image-20250912193517262](README/image-20250912193517262.png)

导入全局变量

![image-20250912195156306](README/image-20250912195156306.png)

保存前端提交的文件

![image-20250913104539088](README/image-20250913104539088.png)

将文件内容交给大模型，实现文件交互

![image-20250913104304022](README/image-20250913104304022.png)

### RAG

使用langchain读取不同格式的文档信息

### 首先安装依赖包

pip install langchain-community
pip install langchain-unstructured

### 读取目录中的非结构化数据

pip install unstructured
pip install "unstructured[pptx]"
pip install "unstructured[image]"
pip install "unstructured[md]"
pip install "unstructured[pdf]"

pip install "unstructured[xlsx]"

### 识别图片

conda install -c conda-forge libmagic

下载软件包和语言包（指定文件存放），配置相关环境变量

![image-20250913132717434](README/image-20250913132717434.png)

![image-20250913132928836](README/image-20250913132928836.png)

### 将目录下面的文件全部读取，并存储为Json文件

![image-20250913143545894](README/image-20250913143545894.png)

### 语义分割

基于某一个**语义分割大模型**完成语义分割，实现知识点分块，减小上下文腐蚀

![image-20250913152542630](README/image-20250913152542630.png)

把分割后的知识库保存到新的json文件，每个知识块作为一个独立的条目

![image-20250913155521098](README/image-20250913155521098.png)

基于**rerank模型**，计算每个知识块与问题的文本相关性分数，以此决定哪些文本需要进入上下文

但是我们**通常不直接这么添加上下文**，详细内容接着往下看

![image-20250913163401024](README/image-20250913163401024.png)

### 词向量数据库

pip install chromadb

chroma run --path RAG检索增强生成/chromadb --host 127.0.0.1 --port 10221

激活服务器，将chroma 词向量存储在./chromadb下![image-20250913232719684](README/image-20250913232719684.png)

将知识块用语义分割模型分割成知识块后，使用嵌入向量生成模型为每个知识块生成向量，存到向量数据库中

当我们用collection.query来查询用户输入问题与向量数据库存储的知识块的相关性，嵌入向量生成模型将问题转化为词向量，在数据库中寻找相似度最近的返回

![image-20250914142608639](README/image-20250914142608639.png)

使用rerank模型进行二次精排

