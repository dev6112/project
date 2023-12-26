from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import numpy as np
import PIL.Image
from sklearn.decomposition import PCA
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'  # Change this to a more secure key
app.config['UPLOAD_FOLDER'] = 'uploads'

class PCAImageCompressor:
    def __init__(self):
        self.image_path = ''
        self.result_filename = ''

    def compress_image(self, image_path, num_components):
        img = PIL.Image.open(image_path)
        img = img.convert("L")
        img_array = np.array(img)

        pca = PCA(n_components=num_components)
        compressed_img_array = pca.fit_transform(img_array)
        reconstructed_img_array = pca.inverse_transform(compressed_img_array)

        compressed_img = PIL.Image.fromarray(reconstructed_img_array.astype(np.uint8))

        filename, extension = os.path.splitext(os.path.basename(image_path))
        result_filename = f"{filename}_compressed_pca_{num_components}.jpg"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        compressed_img.save(result_path)

        return result_path, os.path.getsize(result_path)

    def reset(self):
        self.image_path = ''
        self.result_filename = ''

obj = PCAImageCompressor()

@app.route('/')
def index():
    return render_template('index.html', result='')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        flash('No image file provided.')
        return redirect(url_for('index'))

    image = request.files['image']
    if image.filename == '':
        flash('No selected image file.')
        return redirect(url_for('index'))

    num_components = int(request.form['components'])
    obj.reset()

    try:
        filename = secure_filename(image.filename)
        obj.image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(obj.image_path)

        result_path, compressed_img_size = obj.compress_image(obj.image_path, num_components)

        return render_template('index.html', result=result_path, compressed_img_size=compressed_img_size / 1024)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
app.run(debug=True)
