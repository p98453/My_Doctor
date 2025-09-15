from django.db import models

# Create your models here.

'''
    Topic：类名，当我们进行模型迁移之后，会根据类名自动创建一个表topic
    models.Model：是Django写好的基类，在创建模型的时候，一定要继承该类
'''
class Topic(models.Model):
    # 主键 id：自动增加，key 是唯一的
    id = models.AutoField(primary_key=True) # 就这样就添加了一个字段
    # 话题：title， varchar(500)
    title = models.CharField(max_length=5000)

    # # 添加一个新的字段：问题的摘要内容，长度为40，允许为空
    # summary = models.CharField(max_length=40, null=True)
    
    # status：状态， int， 默认值为1, 0表示删除
    status = models.IntegerField(default=1)
    
    # 用户id：user_id， int
    user_id = models.IntegerField()
    # 话题开启时间：create_time， datetime，当前时间作为默认值
    create_time = models.DateTimeField(auto_now_add=True)
    
class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    topic_id = models.IntegerField()
    user_id = models.IntegerField()
    # 角色：user  assiant
    role = models.CharField(max_length=10)
    # status：状态， int， 默认值为1, 0表示删除
    status = models.IntegerField(default=1)
    
    content = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)