# app.py - CÓDIGO COMPLETO PARA COMEÇAR
from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Criar pastas se não existirem
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h1>Auto Video Editor</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="video" accept="video/*" required>
                <button type="submit">Processar com IA</button>
            </form>
        </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return 'Nenhum vídeo enviado'
    
    video = request.files['video']
    if video.filename == '':
        return 'Nenhum vídeo selecionado'
    
    # Salvar vídeo
    filename = secure_filename(video.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(input_path)
    
    # Processar (por enquanto só copia)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], f'processed_{filename}')
    
    # COMANDO FFMPEG SIMPLES - CORREÇÃO BÁSICA
    import subprocess
    cmd = f'ffmpeg -i {input_path} -vf "eq=contrast=1.1:brightness=0.02" -c:a copy {output_path}'
    subprocess.run(cmd, shell=True)
    
    return f'<a href="/download/{os.path.basename(output_path)}">Download</a>'

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True)
