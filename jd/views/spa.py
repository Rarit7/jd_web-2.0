import os
from flask import send_from_directory, send_file
from jd import app

# SPA 单页应用支持

@app.route('/')
def serve_spa():
    """服务Vue应用的入口文件"""
    dist_path = os.path.join(app.static_folder, 'dist')
    index_path = os.path.join(dist_path, 'index.html')
    
    # 如果存在构建后的文件，返回Vue应用
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        # 开发模式下的提示页面
        return """
        <html>
        <head><title>JD Web</title></head>
        <body>
            <h2>JD Web 应用正在启动...</h2>
            <p>请确保前端应用已构建或开发服务器正在运行。</p>
            <ul>
                <li>开发模式: <code>cd frontend && npm run dev</code></li>
                <li>生产构建: <code>cd frontend && npm run build</code></li>
            </ul>
        </body>
        </html>
        """

@app.route('/<path:filename>')
def serve_spa_assets(filename):
    """服务SPA应用的静态资源"""
    dist_path = os.path.join(app.static_folder, 'dist')
    
    # 检查是否为API请求
    if filename.startswith('api/'):
        return app.send_static_file(filename)
    
    # 检查构建后的静态文件是否存在
    if os.path.exists(os.path.join(dist_path, filename)):
        return send_from_directory(dist_path, filename)
    
    # 对于Vue Router的路由，返回index.html
    index_path = os.path.join(dist_path, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    
    # 开发模式下返回404
    return "File not found", 404