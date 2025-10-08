from flask import Flask, request, send_file, render_template_string
import os
import subprocess
from werkzeug.utils import secure_filename
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Criar pastas se não existirem
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# HTML simples mas funcional
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Auto Video Editor</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .btn:disabled { background: #ccc; }
        .progress { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🎬 Auto Video Editor</h1>
    <p>Faça upload do seu vídeo para processamento automático com IA</p>
    
    <form id="uploadForm" enctype="multipart/form-data">
        <div class="upload-area">
            <input type="file" name="video" accept="video/*" required id="videoInput">
            <p>Arraste ou clique para selecionar um vídeo (até 2 minutos)</p>
        </div>
        <button type="submit" class="btn" id="processBtn">Processar com IA</button>
    </form>
    
    <div id="progress" style="display: none;">
        <h3>Processando seu vídeo...</h3>
        <p>Isso pode levar alguns minutos</p>
    </div>
    
    <div id="result" style="display: none;">
        <h3>✅ Seu vídeo está pronto!</h3>
        <a id="downloadLink" class="btn">Baixar Vídeo Editado</a>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const videoFile = document.getElementById('videoInput').files[0];
            
            if (!videoFile) {
                alert('Por favor, selecione um vídeo');
                return;
            }
            
            formData.append('video', videoFile);
            
            // Mostrar progresso
            document.getElementById('progress').style.display = 'block';
            document.getElementById('processBtn').disabled = true;
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Erro no processamento');
                }
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('downloadLink').href = result.download_url;
                    document.getElementById('result').style.display = 'block';
                } else {
                    throw new Error(result.error || 'Erro desconhecido');
                }
                
            } catch (error) {
                alert('Erro: ' + error.message);
            } finally {
                document.getElementById('progress').style.display = 'none';
                document.getElementById('processBtn').disabled = false;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return {'success': False, 'error': 'Nenhum vídeo enviado'}, 400
        
        video = request.files['video']
        if video.filename == '':
            return {'success': False, 'error': 'Nenhum vídeo selecionado'}, 400
        
        # Verificar extensão
        allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        if not any(video.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {'success': False, 'error': 'Formato de vídeo não suportado'}, 400
        
        # Salvar vídeo original
        filename = secure_filename(video.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video.save(input_path)
        
        # Nome do arquivo processado
        output_filename = f'processed_{os.path.splitext(filename)[0]}.mp4'
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # PROCESSAMENTO COM FFMPEG - CORREÇÕES BÁSICAS
        # 1. Correção de cor básica
        # 2. Estabilização leve
        # 3. Normalização de áudio
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', 'eq=contrast=1.1:brightness=0.02:saturation=1.1,deshake',
            '-af', 'loudnorm',
            '-c:v', 'libx264', '-preset', 'fast',
            output_path
        ]
        
        # Executar comando FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'success': False, 'error': f'Erro no FFmpeg: {result.stderr}'}, 500
        
        # Verificar se arquivo foi criado
        if not os.path.exists(output_path):
            return {'success': False, 'error': 'Arquivo processado não foi criado'}, 500
        
        return {
            'success': True, 
            'download_url': f'/download/{output_filename}',
            'message': 'Vídeo processado com sucesso!'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(app.config['PROCESSED_FOLDER'], filename),
            as_attachment=True,
            download_name=f'video_editado_{filename}'
        )
    except Exception as e:
        return f'Erro ao baixar arquivo: {str(e)}', 404

if __name__ == '__main__':
    print("🎬 Auto Video Editor iniciando...")
    print("📧 Acesse: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
