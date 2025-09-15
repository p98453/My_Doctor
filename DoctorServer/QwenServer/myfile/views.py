import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

UPLOAD_DIR = "../QwenServer/myfile/files"

@csrf_exempt
def upload(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        user_id = request.POST.get("user_id", 0)

        if not file:
            return JsonResponse({"code": 400, "msg": "No file found in request"})

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        filename = os.path.basename(file.name)
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # 读取文件内容（仅适合小文件）
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = ""

        return JsonResponse({
            "code": 200,
            "msg": "File uploaded successfully",
            "file_name": filename,
            "file_path": file_path,
            "user_id": user_id,
            "content": content[:5000]  # 避免太大，可以只返回前5000字符
        })

    return JsonResponse({"code": 405, "msg": "Method Not Allowed"})
