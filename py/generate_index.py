import os
import time

# --- 配置区 ---
DATA_DIR = "ip"
OUTPUT_FILE = "index.html"
# 这里换成你 Cloudflare Pages 的实际域名
DOMAIN = "gbox.indevs.in" 

def generate():
    if not os.path.exists(DATA_DIR):
        print(f"错误: 找不到目录 {DATA_DIR}")
        return

    files = sorted([f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))])
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Based IP 资源索引</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body class="bg-gray-50 text-gray-900 min-h-screen">
        <div class="max-w-4xl mx-auto py-12 px-4">
            <header class="mb-10 text-center">
                <h1 class="text-4xl font-extrabold text-indigo-600 mb-2">Based IP 资源索引</h1>
                <p class="text-gray-500">自动实时更新 · 稳定可靠的流媒体资源</p>
                <div class="mt-4 flex justify-center space-x-4 text-sm text-gray-400">
                    <span><i class="fa-regular fa-file-lines"></i> 文件总数: {len(files)}</span>
                    <span><i class="fa-regular fa-clock"></i> 更新于: {update_time}</span>
                </div>
            </header>

            <div class="bg-white shadow-xl rounded-2xl overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-indigo-50 text-indigo-700 uppercase text-xs font-bold">
                        <tr>
                            <th class="px-6 py-4">文件名</th>
                            <th class="px-6 py-4 text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
    """

    for file in files:
        full_url = f"{DOMAIN}/{DATA_DIR}/{file}"
        html_template += f"""
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 font-medium text-gray-700">
                                <i class="fa-solid fa-link text-indigo-300 mr-2"></i>{file}
                            </td>
                            <td class="px-6 py-4 text-right space-x-2">
                                <a href="{DATA_DIR}/{file}" target="_blank" class="inline-flex items-center px-3 py-1 bg-white border border-gray-300 rounded-md text-sm text-gray-600 hover:bg-gray-50 font-medium transition shadow-sm">
                                    查看内容
                                </a>
                                <button onclick="copyToClipboard('{full_url}')" class="inline-flex items-center px-3 py-1 bg-indigo-600 border border-transparent rounded-md text-sm text-white hover:bg-indigo-700 font-medium transition shadow-sm">
                                    复制 URL
                                </button>
                            </td>
                        </tr>
        """

    html_template += """
                    </tbody>
                </table>
            </div>
            
            <footer class="mt-12 text-center text-gray-400 text-sm">
                <p>基于 GitHub Actions & Cloudflare Pages 构建</p>
                <a href="https://github.com/linyu345/based" class="hover:text-indigo-500 transition"><i class="fa-brands fa-github mt-2"></i> View on GitHub</a>
            </footer>
        </div>

        <script>
            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('复制成功！地址可直接用于播放器。');
                }).catch(err => {
                    console.error('复制失败', err);
                });
            }
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)
    print("已生成专业的 index.html")

if __name__ == "__main__":
    generate()
