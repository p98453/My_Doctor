<template>
	<view class="container">
		<!-- 顶部栏 -->
		<view class="header">
			<!-- 左上角按钮（点击可展开历史对话弹窗） -->
			<image class="nav-icon" src="/static/newchat.png" mode="aspectFill" @tap="toggle('left')" />
			<view class="title-box">
				<text class="title">中医在线问诊系统</text>
				<text class="subtitle">你的超级个人医生</text>
			</view>
		</view>

		<!-- 聊天框 -->
		<view class="chat-box">
			<!-- 滚动区域（显示消息） -->
			<scroll-view class="chat-content" scroll-y :scroll-into-view="scrollToView"
				:style="{ height: dynamicChatContentHeight + 'px' }">
				<!-- 遍历消息列表 -->
				<view v-for="(message, index) in messages" 
					  :key="index" 
					  :id="'message-' + index" 
					  class="chat-message" 
					  :class="{ self: message.self }">
					<!-- 头像 -->
					<image class="avatar" :class="{ self: message.self }" 
						:src="message.self ? userAvatar : assistantAvatar" />
					<!-- 消息文本（支持 Markdown 渲染） -->
					<view class="message-text" :class="{ self: message.self }">
						<zero-markdown-view :markdown="message.text" :aiMode="true" />
					</view>
				</view>
			</scroll-view>


			<!-- 输入区 -->
			<view class="input-box">
				<view class="input-row">
					<!-- 文件上传按钮（静态展示，不写交互） -->
					<view class="upload-btn">
						<image src="/static/upload.png" mode="aspectFit" @tap="upFile" class="upload-icon" />
					</view>
					<!-- 输入框 -->
					<input class="chat-input" v-model="inputText" @confirm="sendMessage" placeholder="输入消息..." />
				</view>
			</view>
		</view>

		<!-- 弹窗（显示历史对话列表） -->
		<uni-popup class="history" ref="popup" background-color="#fff" @change="change">
			<view class="popup-content" :class="{ 'popup-height': type === 'left' || type === 'right' }">
				<!-- 遍历历史对话列表 -->
				<view class="chat-container" 
					  v-for="(h, index) in historylist" 
					  :key="h.id"
					  @tap="getTopic(h.id)" 
					  @longpress="deleteTopic(h.id, index)">
					<view class="chat-item">
						<view class="chat-bubble" :class="current_topic == h.id ? 'selected':''">
							{{h.title}}
						</view>
					</view>
				</view>
			</view>
		</uni-popup>

	</view>
</template>

<script>
	// 导入全局变量路径
	import config from '@/common/config.js';
export default {
	data() {
		return {
			streamcontent: '',         // 流式返回的内容
			type: "center",            // 弹窗类型（left/right/center）
			messages: [],              // 聊天消息列表
			inputText: '',             // 输入框绑定内容
			isLoading: false,          // 是否正在等待 AI 回复
			userAvatar: '/static/myself.png',     // 用户头像
			assistantAvatar: '/static/model.png', // 助手头像
			chatlists:[],
			scrollToView: null,        // 滚动定位到的消息 id
			topic_id: 0,               // 当前会话的主题 ID
			historylist: [],           // 历史对话记录列表
			current_topic: 0,          // 当前选中的历史对话 id
			context:'', //存放上传的文件内容
		};
	},
	computed: {
		// 动态计算聊天内容区高度
		dynamicChatContentHeight() {
			const screenHeight = uni.getSystemInfoSync().windowHeight;
			return screenHeight - 120; // 预留顶部和底部高度
		}
	},

	methods: {
		// 上传文件
		upFile() {
			uni.chooseFile({
				count: 1, // 只选择一个文件
				success: (res) => {
					let user_id = 0
					try{
						let user_id = uni.getStorageSync('user_id')
					}catch(e){
						user_id = 0
					}
					console.log(user_id)
					
					// 选择的文件临时路径
					const filePath = res.tempFiles[0].path;
					console.log("选择的文件:", filePath);

					// 上传文件到后端
					uni.uploadFile({
						url: config.baseUrl + '/myfile/upload/', // 你的后端上传接口
						filePath: filePath,
						name: 'file', // 后端接收文件的字段名
						fromData:{
							'user_id': user_id
						},
						success: (uploadFileRes) => {
							let data = JSON.parse(uploadFileRes.data)
							console.log("上传成功:", data);
							uni.showToast({ title: "上传成功", duration: 1000 });
							this.context = data.content
							console.log(this.context)
						},
						fail: (err) => {
							console.error("上传失败:", err);
							uni.showToast({ title: "上传失败", icon: "none" });
						}
					});
				},
				fail: (err) => {
					console.error("选择文件失败:", err);
				}
			});
		},



		// 删除历史对话
		deleteTopic(topic_id, index) {
			uni.showModal({
				title: "确认删除",
				content: "确定要删除这个对话吗？",
				success: (res) => {
					if (res.confirm) {
						// 调用后端删除接口
						uni.request({
							url: config.baseUrl + '/ai/delete_topic/',
							method: 'POST',
							data: { topic_id },
							success: (res) => {
								// 删除成功后，从前端移除
								this.historylist.splice(index, 1);
								uni.showToast({ title: "删除成功", duration: 1000 });
							},
							fail: () => {
								uni.showToast({ title: "删除失败", icon: "none" });
							}
						});
					}
				}
			});
		},
		// 选择历史对话
		getTopic(topic_id) {
			this.current_topic = topic_id;
			uni.request({
				url: config.baseUrl + '/ai/chathistory/',
				data: { topic_id },
				success: (res) => {
					this.chatlists = res.data.data;
					this.topic_id = topic_id;
	
					// 转换历史消息格式
					this.messages = this.chatlists.map(item => ({
						text: item.content,
						self: item.role === "user"
					}));
	
					this.$refs.popup.close();
					this.scrollToBottom();
				},
			});
		},


		// 发送消息
		sendMessage() {
			const inputText = this.inputText.trim();
			if (!inputText && !this.context) {
				return uni.showToast({ title: "请输入内容或上传文件", duration: 1000 });
			}
			if (this.isLoading) {
				return uni.showToast({ title: "正在思考中，请稍候...", duration: 1000 });
			}

			this.isLoading = true;

			// 1. 聊天框显示的消息，只显示用户输入
			this.messages.push({ text: inputText, self: true });
			this.scrollToBottom();

			// 2. 构造实际发送给后端的内容（带上传文件内容）
			let sendContent = inputText;
			if (this.context) {
				sendContent += "\n\n[上传文件内容开始]\n" + this.context + "\n[上传文件内容结束]";
			}

			// 清空输入框（可选：上传文件内容保留，防止多次发送同一个文件）
			this.inputText = '';

			// 发送给后端 SSE 流式请求
			const evtSource = new EventSource(
				config.baseUrl + "/ai/ai_chat_123/stream/?question=" + encodeURIComponent(sendContent) + '&topic_id=' + this.topic_id
			);

			let assistantMsgIndex = null;

			evtSource.onmessage = (event) => {
				let content = event.data.replace(/^data:\s*/, "");

				if (event.data.includes("<topic_id>")) {
					this.topic_id = content.match(/<topic_id>(.*?)<\/topic_id>/)[1];
					console.log('提取到的 topic_id:', this.topic_id);
					return false;
				}

				if (content.includes("[DONE]")) {
					this.isLoading = false;
					evtSource.close();
					content = content.replace("[DONE]", "");
					if (!content.trim()) return;
				}

				if (assistantMsgIndex === null) {
					this.messages.push({ text: content, self: false });
					assistantMsgIndex = this.messages.length - 1;
				} else {
					this.messages[assistantMsgIndex].text += content;
				}

				this.scrollToBottom();
			};

			evtSource.onerror = (error) => {
				console.error("流式请求出错：", error);
				evtSource.close();
				this.isLoading = false;
				uni.showToast({
					title: "请求出错，请稍候再试",
					duration: 1000,
					icon: 'none'
				});
			};
		},



		// 滚动到底部
		scrollToBottom() {
			setTimeout(() => {
				this.scrollToView = 'message-' + (this.messages.length - 1);
			}, 50);
		},
		// 弹窗状态变化（打开时获取历史对话）
		change(e) {
			if (this.historylist.length > 0){
				return false;
			}
			uni.request({
				url: config.baseUrl + '/ai/chatlist/', // 获取历史对话列表
				success: (res) => {
					console.log(res.data);
					this.historylist = res.data.data;
				},
			});
			console.log('当前模式：' + e.type + ',状态：' + e.show);
		},
		// 打开弹窗
		toggle(type) {
			this.type = type;
			this.$refs.popup.open(type);
		},
	}
};
</script>

<style>
/* ===== 整体容器样式 ===== */
.container {
	display: flex;
	flex-direction: column;
	height: 100%;
	background: #f8f9fa;
}

/* ===== 历史对话列表样式 ===== */
.chat-container {
    width: 100%;
    padding: 4% 5%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column; 
    align-items: flex-start; /* 左对齐 */
}
.chat-item {
    margin-bottom: 6%;
    width: 100%; 
}
.chat-time {
    font-size: 12px;
    color: #999;
    margin-bottom: 2%;
    display: block;
    text-align: left; 
}
/* 普通气泡 */
.chat-bubble {
	padding: 3% 2%;
	background-color: #fff;
	border-radius: 8rpx;
	font-size: 32rpx;
	color: #333;
	white-space: nowrap;      /* 不换行 */
	overflow: hidden;         /* 超出隐藏 */
	text-overflow: ellipsis;  /* 超出显示省略号 */
}
/* 选中气泡 */
.chat-bubble.selected {
	background-color: #e6f0ff;
	color: #2a62ff;
}

/* ===== 顶部栏样式 ===== */
.header {
	display: flex;
	align-items: center;
	padding: 10px;
	background: #fff;
	box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.nav-icon {
	width: 28px;
	height: 28px;
	margin-right: 8px;
}
.title-box {
	display: flex;
	flex-direction: column;
}
.title {
	font-size: 18px;
	font-weight: bold;
}
.subtitle {
	font-size: 12px;
	color: #888;
}

/* ===== 聊天区域样式 ===== */
.chat-box {
	flex: 1;
	display: flex;
	flex-direction: column;
}
.chat-content {
	padding: 10px;
}
.chat-message {
	display: flex;
	align-items: flex-start;
	margin-bottom: 12px;
}
/* 自己的消息靠右 */
.chat-message.self {
	justify-content: flex-end;
}
.avatar {
	width: 32px;
	height: 32px;
	border-radius: 50%;
	margin-right: 8px;
}
.avatar.self {
	order: 2;          /* 自己的头像在最右边 */
	margin-left: 8px;  
	margin-right: 0;
}
.message-text {
	max-width: 70%;
	padding: 8px 12px;
	border-radius: 12px;
	background: #fff;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.message-text.self {
	order: 1;          
	background: #d4f1ff;
}

/* ===== 输入框样式 ===== */
.input-box {
	padding: 8px;
	background: #fff;
	box-shadow: 0 -1px 4px rgba(0, 0, 0, 0.05);
}
.input-row {
	display: flex;
	align-items: center;
}
.upload-btn {
	width: 32px;
	height: 32px;
	margin-right: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #f1f1f1;
	border-radius: 8px;
}
.upload-icon {
	width: 20px;
	height: 20px;
}
.chat-input {
	flex: 1;
	padding: 10px;
	border-radius: 20px;
	background: #f1f1f1;
}

/* ===== 弹窗样式 ===== */
.history .popup-content {
	width: 80vw;       /* 弹窗宽度占屏幕 80% */
	max-width: 600px;  /* 最大宽度限制 */
}
</style>
